import csv
import os
import pathlib
import queue
import re
import sys
import threading
import time
import traceback
import unicodedata
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm
import signal
import argparse

# Constants
MAX_RETRIES = 5
DELAY_FACTOR = 3
INITIAL_DELAY = 20
MAX_CONCURRENT_DOWNLOADS = 3  # You can adjust this based on your needs

# --- Global Variables ---
stop_event = threading.Event()

# Load environment variables from .env file
load_dotenv()

# Configure loguru
logger.add(
    sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO"
)
logger.add("download_teachable_{time:YYYY-MM-DD}.log", rotation="500 MB")

# --- Helper Functions ---
def signal_handler(sig, frame):
    logger.warning('You pressed Ctrl+C!')
    stop_event.set()
    raise KeyboardInterrupt  # This will now interrupt system calls like time.sleep()

def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitizes a filename by removing unsafe characters and enforcing length limits.
    """
    filename = re.sub(r"[\\/*?:\"><|]", "", filename)
    filename = filename.replace(" ", "_")
    filename = filename.replace(",", "")
    filename = filename.replace("_-_", "-")
    return filename[:max_length]

def get_unique_filename(file_path: pathlib.Path) -> pathlib.Path:
    """
    Generates a unique filename if a file already exists by appending a number.
    """
    if not file_path.exists():
        return file_path

    counter = 1
    while True:
        new_file_path = file_path.with_stem(f"{file_path.stem}_{counter}")
        if not new_file_path.exists():
            return new_file_path
        counter += 1

def find_file_by_partial_name(
    directory: pathlib.Path, partial_name: str
) -> Optional[pathlib.Path]:
    """
    Finds a file in a directory whose name contains a specific partial string.
    """
    for entry in directory.iterdir():
        if entry.is_file() and partial_name in entry.name:
            return entry
    return None

def rename_course_directory(
    base_dir: pathlib.Path,
    course_id: int,
    old_course_name: str,
    new_course_name: str,
) -> None:
    """
    Renames a course directory if the course name has changed.
    """
    old_dirname = f"{course_id} - {safe_filename(old_course_name)}"
    new_dirname = f"{course_id} - {safe_filename(new_course_name)}"

    old_path = base_dir / old_dirname
    new_path = base_dir / new_dirname

    if old_path.exists() and old_path != new_path:
        if not new_path.exists():
            try:
                old_path.rename(new_path)
                logger.info(f"Directory renamed:")
                logger.info(f"  From: {old_path}")
                logger.info(f"  To:   {new_path}")
                logger.info("")
            except OSError as e:
                logger.error(f"Error renaming directory: {e}")
        else:
            logger.warning(f"Rename skipped, target directory already exists:")
            logger.warning(f"  From: {old_path}")
            logger.warning(f"  To:   {new_path}")
            logger.warning("")

def backup_existing_file(file_path: pathlib.Path) -> None:
    """
    Creates a backup of an existing file with a timestamp.
    """
    if file_path.exists():
        created_time = time.strftime(
            "%Y-%m-%d_%H-%M-%S", time.gmtime(os.path.getctime(file_path))
        )
        backup_file_path = file_path.with_name(
            f"{file_path.stem}_{created_time}{file_path.suffix}"
        )

        if not backup_file_path.exists():
            try:
                file_path.rename(backup_file_path)
                logger.info(f"Renamed '{file_path.name}' to '{backup_file_path.name}'.")
            except OSError as e:
                logger.error(f"Error renaming file: {e}")

def save_data_to_csv(
    data: List[Dict[str, Any]],
    file_path: pathlib.Path,
    delimiter: str = ";",
    quotechar: str = '"',
) -> None:
    """Saves a list of dictionaries to a CSV file."""
    if not data:
        return

    # Clean text fields before writing
    cleaned_data = []
    for row in data:
        cleaned_row = {k: clean_text(v) if isinstance(v, str) else v for k, v in row.items()}
        cleaned_data.append(cleaned_row)

    fieldnames = data[0].keys()
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            delimiter=delimiter,
            quotechar=quotechar,
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        writer.writerows(cleaned_data)  # Write the cleaned data

def save_text_attachment(content: str, file_path: pathlib.Path) -> None:
    """Saves a text attachment to a file."""
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

def save_json_attachment(content: Dict[str, Any], file_path: pathlib.Path) -> None:
    """Saves a JSON attachment to a file."""
    import json

    with open(file_path, "w") as file:
        json.dump(content, file)

def clean_text(text: str) -> str:
    """
    Clean text by handling encoding issues (specifically windows-1252).
    """
    try:
        return text.encode("windows-1252", errors="replace").decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        return text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")

def process_lecture_data(
    lecture: Dict[str, Any], course_id: int, course_name: str, section_position: int, section_name: str
) -> List[Dict[str, Any]]:
    """Processes raw lecture data into a list of dictionaries for CSV export"""
    processed_data = []

    for attachment in lecture["attachments"]:
        # Normalize attachment name
        normalized_name = normalize_utf_filename(attachment["name"])

        processed_data.append(
            {
                "course_id": course_id,
                "course_name": course_name,
                "module_position": section_position,  # Now correctly using section_position
                "module_id": lecture["section_id"],
                "module_name": section_name,  # Use section name
                "lecture_position": lecture["position"],
                "lecture_id": lecture["id"],
                "lecture_name": lecture["name"],
                "lecture_is_published": lecture["is_published"],
                "attachment_position": attachment["position"],
                "attachment_id": attachment["id"],
                "attachment_name": normalized_name,  # Use normalized name
                "attachment_kind": attachment["kind"],
                "attachment_url": attachment["url"],
                "url_thumbnail": attachment.get("url_thumbnail", ""),
                "media_duration": attachment.get("media_duration", 0),
                "text": attachment.get("text"),
                "quiz": attachment.get("quiz"),
            }
        )

    return processed_data

# --- API Client ---
class TeachableAPIClient:
    def __init__(
        self, api_key: str, base_url: str = "https://developers.teachable.com/v1"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"accept": "application/json", "apiKey": self.api_key}
        self.max_retries = MAX_RETRIES
        self.delay_factor = DELAY_FACTOR
        self.initial_delay = INITIAL_DELAY
        self._stop_event = threading.Event()
        self.session = requests.Session()  # Create a requests session
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]) # Configure retries
        self.session.mount('https://', HTTPAdapter(max_retries=retries)) # Use with the session


    def stop(self):
        self._stop_event.set()

    def _handle_rate_limit(self, url: str) -> requests.Response:
        """Handles API rate limiting with retries."""
        retries = 0
        while retries < self.max_retries:
            if self._stop_event.wait(timeout=0): # Check stop event immediately.
                raise KeyboardInterrupt("API client stopped.")

            try:
                response = self.session.get(url, headers=self.headers, timeout=30) #<- Use session here with headers and timeout
                logger.debug(f"_handle_rate_limit - Requesting URL: {url}, Status code: {response.status_code}")
                if response.status_code != 429:
                    return response
            except requests.exceptions.RequestException as e:
                logger.error(f"_handle_rate_limit - Request failed: {e}") # Log error details

            retries += 1
            try:
                reset_time = int(response.headers.get("RateLimit-Reset", 0))
                delay = max(
                    reset_time, self.initial_delay * (self.delay_factor ** (retries - 1))
                )
                logger.warning(f"Rate limit reached. Retrying in {delay} seconds...")
                if not sleep_with_interrupt(delay):
                  raise KeyboardInterrupt
            except ValueError:
                delay = self.initial_delay * (self.delay_factor ** (retries - 1))
                logger.warning(
                    f"Rate limit reached, but reset time is not provided. Retrying in {delay} seconds..."
                )
                # Check for Ctrl+C during sleep
                if not sleep_with_interrupt(delay):
                  raise KeyboardInterrupt

        # If we've reached here, it means we've exceeded max retries
        logger.error(
            f"Max retries exceeded. Last response: {response.status_code} {response.reason}"
        )
        raise requests.exceptions.RetryError(
            f"Max retries exceeded. Last response: {response.status_code} {response.reason}"
        )
        

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Makes a GET request to the API."""
        url = f"{self.base_url}{endpoint}"

        # Add parameters to the URL if provided
        if params:
            url += "?" + "&".join(f"{key}={value}" for key, value in params.items())

        response = self._handle_rate_limit(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()

    def get_all_courses(self) -> List[Dict[str, Any]]:
        logger.info("Fetching all courses...")
        all_courses = []
        page = 1
        per_page = 20  # matches the API's "per_page" default or limit
        try:
            while not stop_event.is_set():
                logger.info(f"Fetching courses page {page}...")
                params = {"page": page, "per": per_page}
                try:
                    data = self.get("/courses", params=params)

                    courses = data["courses"]
                    all_courses.extend(courses)

                    meta = data.get("meta", {})
                    total_pages = meta.get("number_of_pages")
                    current_page = meta.get("page", page)
                    # for debugging
                    # total = meta.get("total", 0)
                    # from_result = meta.get("from", 0)
                    # to_result = meta.get("to", 0)
                    # logger.info(f"Total pages: {total_pages}, Current page: {current_page}, Total courses: {total}, Results: {from_result}-{to_result}")

                    # Stop when we've reached the total number of pages
                    if current_page >= total_pages:
                        break

                    page += 1
                except (requests.exceptions.RequestException, ValueError) as e:
                    logger.error(f"Error fetching courses: {e}")
                    break  # Exit the loop on error
                except KeyboardInterrupt:
                    logger.warning("User interrupted fetching courses. Stopping.")
                    break
        except KeyboardInterrupt:
            logger.warning("User interrupted fetching courses. Stopping.")
        return all_courses

    def get_course(self, course_id: int) -> Dict[str, Any]:
        """Fetches a specific course by ID."""
        data = self.get(f"/courses/{course_id}")
        return data["course"]

    def get_course_by_name(self, course_name: str) -> Optional[Dict[str, Any]]:
        """Fetches a course by name."""
        all_courses = self.get_all_courses()
        for course in all_courses:
            if course["name"] == course_name:
                return course
        return None

    def get_course_content(self, course_id: int) -> Dict[str, Any]:
        """
        Fetch detailed information about a specific course, including all lectures and attachments.
        """
        course_data = self.get_course(course_id)

        # Rename 'lecture_sections' to 'sections' for clarity and consistency
        course_data["sections"] = course_data.pop("lecture_sections")

        # Fetch details for each lecture within each section
        for section in course_data["sections"]:
            section["lectures_detailed"] = []  # Prepare a list for detailed lecture info
            for lecture in section["lectures"]:
                try:
                    lecture_details = self.get_lecture(course_id, lecture["id"])
                    # Add section information to the lecture details
                    lecture_details["section_id"] = section["id"]
                    lecture_details["section_name"] = section["name"]
                    lecture_details["section_position"] = section["position"]
                    section["lectures_detailed"].append(lecture_details)
                except requests.exceptions.HTTPError as e:
                    logger.error(
                        f"Error fetching details for lecture ID {lecture['id']} in course ID {course_id}: {e}"
                    )

        return course_data

    def get_lecture(self, course_id: int, lecture_id: int) -> Dict[str, Any]:
        """Fetches a specific lecture."""
        lecture_data = self.get(f"/courses/{course_id}/lectures/{lecture_id}")
        
        # Fetch video details for video attachments
        if 'lecture' in lecture_data and 'attachments' in lecture_data['lecture']:
            for attachment in lecture_data['lecture']['attachments']:
                if attachment['kind'] == 'video':
                    try:
                        video_data = self.get_attachment_details(course_id, lecture_id, attachment['id'], 'video')
                        # Add video details to the attachment
                        attachment['url_thumbnail'] = video_data['video'].get('url_thumbnail', '')
                        attachment['media_duration'] = video_data['video'].get('media_duration', 0)
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            logger.warning(f"Video details not found for attachment ID {attachment['id']} in lecture ID {lecture_id}.")
                        else:
                            logger.error(f"Error fetching video details for attachment ID {attachment['id']} in lecture ID {lecture_id}: {e}")
        
        return lecture_data["lecture"]

    def get_attachment_details(
        self, course_id: int, lecture_id: int, attachment_id: int, attachment_kind: str
    ) -> Dict[str, Any]:
        """Fetches details for a specific attachment."""
        if attachment_kind == "video":
            return self.get(
                f"/courses/{course_id}/lectures/{lecture_id}/videos/{attachment_id}"
            )
        else:
            return self.get(
                f"/courses/{course_id}/lectures/{lecture_id}/attachments/{attachment_id}"
            )

# --- Task Management ---
class TaskManager:
    def __init__(self, maxsize=0):
        self.lock = threading.Lock()
        self.course_queue_size = 0
        self.download_queue_size = 0
        self.course_queue = queue.Queue(maxsize=maxsize)  # Use maxsize here
        self.download_queue = queue.Queue(maxsize=maxsize) # And here
        self.stop_event = threading.Event()

    def all_tasks_done(self) -> bool:
        """Checks if all tasks are completed."""
        if self.stop_event.is_set():
            logger.debug("all_tasks_done() status - stop_event is set")
            return True

        with self.lock:
            course_queue_empty = self.course_queue.empty()
            download_queue_empty = self.download_queue.empty()
            combined_empty = course_queue_empty and download_queue_empty  # Combine *after* checks

            logger.debug(f"all_tasks_done() status - course_queue: {course_queue_empty}, download_queue: {download_queue_empty}, combined: {combined_empty}")  # Log details
            return combined_empty

    def add_course_task(self, course_id: int, module_id: Optional[int], lecture_id: Optional[int], output_dir: pathlib.Path) -> None:
        with self.lock:
            logger.debug(f"Add task: Course: {course_id}. Course queue size: {self.course_queue_size}, Download queue size: {self.download_queue_size}")
            self.course_queue.put((course_id, module_id, lecture_id, output_dir))
            self.course_queue_size += 1

    def get_course_task(self) -> tuple[int, Optional[int], Optional[int], pathlib.Path]:
        with self.lock:
            task = self.course_queue.get()
            self.course_queue_size -=1 #<- Decrement before returning the task from the queue
            return task


    def course_task_done(self) -> None:
        with self.lock:  # Correct placement
            logger.debug(f"Course task done. Course queue size: {self.course_queue_size}, Download queue size: {self.download_queue_size}")
            self.course_queue.task_done()

    def add_download_task(self, task: Optional[Dict[str, Any]]) -> None:  # Allow None for sentinel
        with self.lock:
            if task: # Log only actual download tasks, not None sentinels
               logger.debug(f"Add task: Download for attachment: {task.get('attachment_id', 'None')}. Course queue size: {self.course_queue_size}, Download queue size: {self.download_queue_size}")
            self.download_queue.put(task)
            self.download_queue_size += 1
    
    def get_download_task(self) -> Optional[Dict[str, Any]]:  # Allow returning None
        with self.lock:
            task = self.download_queue.get()
            self.download_queue_size -= 1
            return task

    def download_task_done(self) -> None:
        with self.lock: # Correct Placement
            logger.debug(f"Download task done. Course queue size: {self.course_queue_size}, Download queue size: {self.download_queue_size}")
            self.download_queue.task_done()

    def is_course_queue_empty(self) -> bool:
        with self.lock:
            return self.course_queue.empty()

    def is_download_queue_empty(self) -> bool:
        with self.lock:
            return self.download_queue.empty()


# --- Worker Threads ---
def course_worker(
    task_manager: TaskManager, api_client: TeachableAPIClient, base_output_dir: pathlib.Path
) -> None:
    """
    Worker thread to process course tasks.
    """
    while True:
        time.sleep(1)
        logger.debug(f"/cw/")

        if stop_event.is_set() or api_client._stop_event.is_set():
            break

        try:
            course_id, module_id, lecture_id, output_dir = task_manager.get_course_task()
            # Use the base output directory for course processing
            course_output_dir = base_output_dir
            logger.info(f"Processing course: {course_id}")
            try:
                process_course(api_client, course_id, module_id, lecture_id, course_output_dir, task_manager)
            except Exception as e:
                logger.exception(f"Error processing course {course_id}: {e}")
            finally:
                task_manager.course_task_done()

            # if task_manager.all_tasks_done():  # Check both queues
            #     break  # Exit if all processing and downloads are done   

        except queue.Empty:
            logger.debug("Course queue is empty.")
            # if task_manager.is_course_queue_empty() and task_manager.processing_done.is_set():
            #     # Signal that all courses have been added
            #     task_manager.signal_processing_done()

            #     # Queue sentinel values for download workers
            #     for _ in range(MAX_CONCURRENT_DOWNLOADS):
            #         task_manager.add_download_task(None)
            #     break
            # #time.sleep(0.5)
            if task_manager.is_course_queue_empty():
                break  # Exit if course queue is truly empty
            time.sleep(1) # Check periodically
            continue
        except Exception as e:
            logger.exception(f"Unexpected error in course_processor: {e}")
            traceback.print_exc()

    # After processing all courses, add sentinels for download workers
    for _ in range(MAX_CONCURRENT_DOWNLOADS):  # Add sentinels here
        task_manager.add_download_task(None)

# --- minimal version for debugging ---
def download_worker(task_manager, valid_types, course_dir, thread_index):
    while True:
        time.sleep(0.1)  # Adjust sleep as needed for testing; remove later
        logger.debug(f"/dw/{thread_index}")

        if stop_event.is_set():
            logger.warning(f"Download worker {thread_index}: stop_event is set. Exiting.")
            raise KeyboardInterrupt

        if task_manager.all_tasks_done(): # check *before* getting tasks
            break

        try:
            task = task_manager.get_download_task()
            logger.debug(f"   \\ Task {task.get('attachment_id', 'empty')}")
        except queue.Empty:
            time.sleep(0.1)  # (Or remove entirely)
            continue
        except Exception as e:
            logger.exception(f"download_worker - Unexpected error: {e}")
            traceback.print_exc()
            continue # Retry


        if task is None:
            task_manager.download_task_done()
            logger.debug(f"   \\ None")
            break

        # ... (rest of your download logic)

        task_manager.download_task_done()  # Add this line to mark tasks as done AFTER download logic

    logger.info(f"Download worker {thread_index} finished.")


        
def full_download_worker(task_manager: TaskManager, valid_types: List[str], course_dir: pathlib.Path, thread_index: int) -> None:
    """
    Worker thread to download attachments.
    """
    while True:
        time.sleep(1)
        logger.debug(f"/dw/{thread_index}")

        if stop_event.is_set():  # Check for interrupt
            logger.warning(f"Download worker {thread_index}: stop_event is set. Exiting.")
            raise KeyboardInterrupt  # <--- Force interrupt after setting stop_event

        try:
            task = task_manager.get_download_task()
            logger.debug(f"   \\ Task {task.get('attachment_id', 'empty')}")
        except queue.Empty: # This needs to be outside to catch an empty queue before processing starts
            if task_manager.all_tasks_done():
                break
            time.sleep(1)
            continue # Go back to the beginning of the loop
        except Exception as e:
            logger.exception(f"Unexpected error in download_worker {thread_index}: {e}")
            traceback.print_exc()
            continue
        except KeyboardInterrupt: # Make sure to catch in here also
            logger.warning("Keyboard interrupt received. Exiting download_worker.")
            break

        if task is None: # Check None only after fetching
            task_manager.download_task_done()  # Crucial: Mark the sentinel task as done
            logger.debug(f"   \\ None")
            break   # Exit worker thread when it gets sentinel value (None)
        
        module_pos = task.get('module_position', '')
        lecture_pos = task.get('lecture_position', '')
        attachment_pos = task.get('attachment_position', '')
        attachment_id = task.get('attachment_id', '')
        attachment_name = task.get('attachment_name', '')
        attachment_url = task.get('attachment_url')

        # Skip if attachment type is not valid
        if task["attachment_kind"] not in valid_types:
            task_manager.download_task_done()
            continue

        filename = f"{module_pos:02d}_{lecture_pos:02d}_{attachment_pos:02d}_{attachment_id}_{safe_filename(attachment_name)}"
        file_path = course_dir / filename
        
        rename_if_needed(course_dir, filename, attachment_id)

        # check if file exists based on attachment_id
        existing_file = find_file_by_partial_name(course_dir, f"_{attachment_id}_")
        if existing_file:
            logger.info(
                f"Skipping download: File with attachment ID {attachment_id} already exists: {existing_file.name}"
            )
            task_manager.download_task_done()
            continue

        attachment_url = task.get('attachment_url')
        if not attachment_url: # <-- Check for missing URL
            logger.warning(f"Skipping task: Missing attachment URL for attachment ID {attachment_id}")
            task_manager.download_task_done() # Important: Mark task as done even if skipped
            continue

        with tqdm(
            total=100,
            desc=f"Downloading {filename}",
            unit="%",
            leave=False,
        ) as progress_bar:
            try:
                success = download_file(attachment_url, file_path, progress_bar)
                if success:
                    logger.info(f"Downloaded: {filename}")
                else:
                    logger.error(f"Failed to download: {filename}")
            except Exception as e:
                logger.exception(f"Error downloading {filename}: {e}")

        # Mark the task as done only AFTER successful processing or error handling.
        task_manager.download_task_done()


    logger.info(f"Download worker {thread_index} finished.")

# --- Main Functions ---
def rename_if_needed(directory: pathlib.Path, new_filename: str, attachment_id: str) -> None:
  """
  Checks if a file with the attachment ID exists, and if so, renames it to the new filename.
  """
  existing_file = find_file_by_partial_name(directory, f"_{attachment_id}_")
  if existing_file:
      new_path = directory / new_filename
      if existing_file != new_path:
          try:
              existing_file.rename(new_path)
              logger.info(f"Renamed existing file:")
              logger.info(f"  From: {existing_file}")
              logger.info(f"  To:   {new_path}")
          except OSError as e:
              logger.error(f"Error renaming file: {e}")

def download_file(
    url: str, file_path: pathlib.Path, progress_bar: tqdm
) -> bool:
    """Downloads a file using requests with a tqdm progress bar (thread-safe)."""
    try:
        response = requests.get(url, stream=True, timeout=120)
        logger.debug(f"download_file - Requesting URL: {url}, Status code: {response.status_code}, Headers: {response.headers}")

        response.raise_for_status()

        file_size = int(response.headers.get("Content-Length", 0))

        if file_path.exists() and file_path.stat().st_size == file_size:
            logger.info(f"File already exists and is complete: {file_path.name}")
            progress_bar.update(100)
            return True
        elif file_path.exists():
            logger.warning(
                f"File exists but has incorrect size, re-downloading: {file_path.name}"
            )
            file_path.unlink()

        with open(file_path, "wb") as out_file:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                out_file.write(chunk)
                downloaded += len(chunk)
                progress = (
                    (downloaded / file_size) * 100 if file_size > 0 else 0
                )
                progress_bar.update(progress - progress_bar.n)  # Update progress

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {url}: {e}")
        if file_path.exists():
            os.remove(file_path)
            logger.info(f"Deleted incomplete file: {file_path.name}")
        return False

def process_course(
    api_client: TeachableAPIClient,
    course_id: int,
    module_id: Optional[int],
    lecture_id: Optional[int],
    output_dir: pathlib.Path,
    task_manager: TaskManager,
) -> None:
    """Processes a single course, fetching its details and queuing downloads."""
    try:
        course_data = api_client.get_course(course_id)
        course_name = course_data["name"]
        logger.info(f"Processing course: {course_name} (ID: {course_id})")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"Course with ID '{course_id}' not found.")
        else:
            logger.exception(f"Error fetching course details: {e}")
        return

    # Create course directory
    course_dirname = f"{course_id} - {safe_filename(course_name)}"
    course_dir = output_dir / course_dirname
    course_dir.mkdir(parents=True, exist_ok=True)

    # Check if course name has changed and rename directory if needed
    all_courses = api_client.get_all_courses()
    for c in all_courses:
        if c["id"] == course_id:
            if c["name"] != course_name:
                rename_course_directory(output_dir, course_id, course_name, c["name"])
                course_name = c["name"]
                course_dirname = f"{course_id} - {safe_filename(course_name)}"
                course_dir = output_dir / course_dirname
            break

    # Backup existing course_data.csv
    course_data_path = course_dir / "course_data.csv"
    backup_existing_file(course_data_path)

    # Fetch and process course data
    logger.info(f"Fetching details for course: {course_name} (ID: {course_id})")
    try:
        course_content = api_client.get_course_content(course_id)
    except requests.exceptions.HTTPError as e:
        logger.exception(
            f"Error fetching course sections for course ID {course_id}: {e}"
        )
        return

    processed_data = []

    for section in course_content["sections"]:
        if module_id and section["id"] != module_id:
            continue

        logger.info(f"  Processing section: {section['name']}")
        section_position = section["position"]  # Get the section position

        for index, lecture in enumerate(section["lectures_detailed"]):
            # lecture_position = index + 1  # No longer needed, we have it in lecture

            if lecture_id and lecture_id != lecture["id"]:
                logger.warning(f"Skipping lecture due to lecture ID filter: {lecture['name']}")
                continue

            logger.info(f"    Processing lecture: {lecture['name']}")

            # Queue downloads right after getting lecture details
            for attachment in lecture["attachments"]:

                # Handle missing 'kind' key
                attachment_kind = attachment.get("kind") 
                if attachment_kind is None:
                    logger.warning(f"Attachment {attachment.get('name', 'Unnamed')} missing 'kind' key, skipping.")
                    continue  # Skip this attachment

                # Normalize attachment name, handle None case
                attachment_name = normalize_utf_filename(attachment.get("name"))

                task_manager.add_download_task(
                    {
                        "module_position": section_position,  # Use section_position
                        "lecture_position": lecture["position"],  # Use lecture's position
                        "attachment_position": attachment["position"],
                        "attachment_id": attachment["id"],
                        "attachment_name": attachment_name,
                        "attachment_kind": attachment["kind"],
                        "attachment_url": attachment["url"],
                    }
                )

            processed_lecture_data = process_lecture_data(
                lecture, course_id, course_name, section_position, section["name"]
            )
            processed_data.extend(processed_lecture_data)

        for attachment in processed_lecture_data:
            attachment_kind = attachment.get("kind") # Get kind safely

            if attachment_kind in ("text", "code_embed", "code_display"):
                filename = safe_filename(
                    f"{section['position']:02}_{lecture["position"]:02}_{attachment['position']:02}_{attachment['id']}_{attachment['name']}"
                )
                file_path = course_dir / f"{filename}.html"
                save_text_attachment(attachment["text"], file_path)
            elif attachment_kind == "quiz":
                filename = safe_filename(
                    f"{section['position']:02}_{lecture["position"]:02}_{attachment['position']:02}_{attachment['id']}_{attachment['name']}_quiz"
                )
                file_path = course_dir / f"{filename}.json"
                save_json_attachment(attachment["quiz"], file_path)
      
    # Save processed data to CSV
    save_data_to_csv(processed_data, course_data_path)
    logger.info(f"Course data saved to {course_data_path}")

def normalize_utf_filename(attachment_name):
    if isinstance(attachment_name, str) and attachment_name not in (None, ""):
        try:
            attachment_name = unicodedata.normalize("NFC", attachment_name)
        except Exception as e:
            logger.error(f"Error normalizing name: '{attachment_name}' {e}")
    return attachment_name

def main() -> None:
    """
    Main function to handle command-line arguments and execute course operations.
    """

    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        description="Manage and download course data from Teachable."
    )

    # Main operations
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")

    # Fetch all courses
    parser_fetch_all = subparsers.add_parser(
        "fetch-all", help="Fetch and save a list of all courses"
    )
    parser_fetch_all.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        default=".",
        help="Directory to save the all courses CSV",
    )

    # Process a course (you can adapt this to process multiple courses)
    parser_process = subparsers.add_parser(
        "process", help="Process and download data for specific courses"
    )
    parser_process.add_argument(
        "course_ids",
        metavar="course_id",
        type=int,
        nargs="+",
        help="One or more Course IDs to process and download",
    )
    parser_process.add_argument(
        "--module_id",
        type=int,
        default=None,
        help="Optional module ID to filter processing",
    )
    parser_process.add_argument(
        "--lecture_id",
        type=int,
        default=None,
        help="Optional lecture ID to filter processing",
    )
    parser_process.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        default=".",
        help="Directory to save course data",
    )

    parser.add_argument(
        "--types",
        "-t",
        choices=["pdf", "file", "image", "video", "audio", "pdf_embed"],
        nargs="*",
        default=["pdf", "file", "image", "video", "audio", "pdf_embed"],
        help="Types of attachments to download",
    )

    args = parser.parse_args()

    # Map --types pdf to 'pdf_embed' internally
    if "pdf" in args.types:
        args.types.append("pdf_embed")
        args.types.remove("pdf")


    api_client = TeachableAPIClient(api_key=os.environ.get("TEACHABLE_API_KEY"))
    download_threads = []

    try:
        task_manager = TaskManager()

        if args.operation == "fetch-all":
            courses = api_client.get_all_courses()
            file_path = args.output / "all_courses_data.csv"
            save_data_to_csv(courses, file_path)
            logger.info(f"All courses saved to {file_path}")

        elif args.operation == "process":
            # Start course processing and download threads
            course_thread = threading.Thread(
                name="CourseProcessor", 
                target=course_worker, args=(task_manager, api_client, args.output)
            )
            course_thread.start()

            download_threads = []
            for i in range(MAX_CONCURRENT_DOWNLOADS):
                thread = threading.Thread(
                    name=f"DownloadWorker-{i}",  # Name the threads
                    target=download_worker,
                    args=(task_manager, args.types, args.output, i), # Pass index
                )
                download_threads.append(thread)
                thread.start()

            # Add selected courses to the task queue
            for course_id in args.course_ids:
                task_manager.add_course_task(course_id, args.module_id, args.lecture_id, args.output)

            logger.debug("Wait for the course processor thread to finish.")
            # Wait for the course processor thread to finish
            course_thread.join()
            logger.debug(f"Course thread finished. Active threads: {[t.name for t in threading.enumerate() if t.is_alive()]}")


            # NOW join the download threads *after* course processing
            for thread in download_threads:
                thread.join()

            logger.info("All threads finished.")  # This should also print

            try:
                while any(thread.is_alive() for thread in download_threads):
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.warning("Keyboard interrupt received. Waiting for threads to exit gracefully...")
                stop_event.set() # set event for any waiting download threads

            logger.info("All downloads completed.")            

    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received; attempting graceful shutdown...")
        stop_event.set()
        api_client.stop() # Tell api client to stop.
        time.sleep(5)
    except Exception as e:  # Catch other potential exceptions
        logger.exception(f"An unexpected error occurred: {e}")
    finally:
        pass

if __name__ == "__main__":
    main()