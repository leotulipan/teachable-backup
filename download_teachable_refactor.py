import csv
import os
import pathlib
import re
import sys
import time
import traceback
import unicodedata
from typing import Any, Dict, List, Optional, Set

import asyncio
import aiohttp
import signal

from dotenv import load_dotenv
from loguru import logger
from dataclasses import dataclass
from asyncio import Queue

# Constants
API_MAX_CONCURRENT_CALLS = 2  # <--- Limit total Teachable API calls at once
MAX_RETRIES = 5
DELAY_FACTOR = 3
INITIAL_DELAY = 20
MAX_CONCURRENT_DOWNLOADS = 3  # Set concurrency for attachment downloads

# Load environment variables from .env file
load_dotenv()

# Configure loguru
logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
logger.add("download_teachable_{time:YYYY-MM-DD}.log", rotation="10 MB")

# --- Helper Functions ---
def sleep_with_interrupt(duration: float) -> bool:
  """Sleeps for the given duration (in seconds), returning early if stop_event is set.

  Args:
      duration: The sleep duration in seconds.

  Returns:
      True if the function slept for the full duration, False if it was interrupted.
  """
  if asyncio.get_event_loop().is_closed():
      return True  # If loop is closed, we're in an async context
  return asyncio.get_event_loop().run_until_complete(asyncio.sleep(duration))

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


def normalize_utf_filename(attachment_name: str | None) -> str | None:
    if isinstance(attachment_name, str) and attachment_name not in (None, ""):
        try:
            attachment_name = unicodedata.normalize("NFC", attachment_name)
        except Exception as e:
            logger.error(f"Error normalizing name: '{attachment_name}' {e}")
    return attachment_name

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

def format_filename_for_log(filename: str, max_length: int = 25, spacer: str = '[..]') -> str:
    """
    Formats a filename for logging by truncating the middle if too long.
    Keeps the extension and start of filename intact.
    """
    if len(filename) <= max_length:
        return filename
        
    name, ext = os.path.splitext(filename)
    if not ext:
        return f"{filename[:max_length]}{spacer}"
    
    # Account for extension length in the max_length
    available_length = max_length - len(ext)
    if available_length <= 0:
        return f"{filename[:max_length]}{spacer}"
        
    return f"{name[:available_length]}{spacer}{ext}"

def format_admin_urls(course_info: Optional[Dict[str, Any]], attachment_id: Optional[int] = None) -> str:
    """
    Formats admin URLs for troubleshooting download issues.
    
    Creates two URLs:
    1. Frontend admin URL to view the lecture (requires course_id and lecture_id)
    2. API endpoint URL for manual download attempt (requires attachment_id)
    
    Note: These URLs only work for logged-in admin users in the Teachable backend.
    """
    if not course_info:
        return ""

    frontend_domain = os.environ.get("TEACHABLE_FRONTEND_DOMAIN", "your-teachable-domain.com")
    if not frontend_domain or not course_info.get('course_id') or not course_info.get('lecture_id'):
        return ""

    admin_urls = "\nAdmin URLs (requires backend login):"
    
    # Frontend URL to view the lecture
    admin_urls += f"\n  View lecture: https://{frontend_domain}/admin-app/courses/{course_info['course_id']}/curriculum/lessons/{course_info['lecture_id']}"
    
    # API endpoint for manual download (if attachment_id is provided)
    if attachment_id:
        admin_urls += f"\n  Manual download: https://{frontend_domain}/api/v1/attachments/{attachment_id}/hotmart_video_download_link"
    
    return admin_urls

# --- API Client ---
class TeachableAPIClient:
    """
    Asynchronous Teachable API client using aiohttp.
    """
    def __init__(self, api_key: str, base_url: str = "https://developers.teachable.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"accept": "application/json", "apiKey": self.api_key}
        self.max_retries = MAX_RETRIES
        self.delay_factor = DELAY_FACTOR
        self.initial_delay = INITIAL_DELAY
        self._stop = False
        self.session = None
        self.api_calls_semaphore = asyncio.Semaphore(API_MAX_CONCURRENT_CALLS)

    def stop(self) -> None:
        """
        Stops the API client from further requests.
        """
        self._stop = True

    async def _handle_rate_limit(self, session: aiohttp.ClientSession, url: str) -> aiohttp.ClientResponse:
        """
        Performs an HTTP GET inside a concurrency-limited section, with
        built-in rate-limit checking for 429 responses from Teachable.
        """
        retries = 0
        while retries < self.max_retries:
            if self._stop:
                raise asyncio.CancelledError("API client stopped.")
            
            async with self.api_calls_semaphore:  # <--- concurrency-limited
                logger.debug(f"Requesting URL: {url} (Retry {retries})")
                try:
                    response = await session.get(url, headers=self.headers)
                    
                    # Check status code first
                    if response.status == 429:
                        # Read headers but don't consume body for 429
                        logger.debug(f"Received 429 response. Rate limit headers: {response.headers}")
                        reset_time_str = response.headers.get("RateLimit-Reset", "")
                        
                        # Close this response since we'll retry
                        await response.release()
                        
                        if reset_time_str.isdigit():
                            delay = int(reset_time_str)
                            logger.warning(f"Rate limit reached. Retrying after {delay} seconds (RateLimit-Reset).")
                        else:
                            delay = self.initial_delay * (self.delay_factor ** retries)
                            logger.warning(f"Rate limit reached; no valid 'RateLimit-Reset'. Retrying in {delay}s.")
                        await asyncio.sleep(delay)
                        retries += 1
                        continue
                    
                    # For any other status, return the response to be handled by caller
                    return response
                    
                except aiohttp.ClientError as e:
                    logger.error(f"HTTP error when fetching {url}: {e}")
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error when fetching {url}: {e}")
                    raise

        logger.error(f"Max retries exceeded. Could not fetch {url}")
        raise aiohttp.ClientError(f"Max retries exceeded for {url}.")

    async def __aenter__(self) -> "TeachableAPIClient":
        # Provide explicit timeouts for connect, read, total, etc.
        timeout = aiohttp.ClientTimeout(total=60, connect=10, sock_connect=10, sock_read=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.session.close()

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Makes an async GET request to the API.
        """
        if self._stop:
            raise asyncio.CancelledError("API client stopped.")

        url = f"{self.base_url}{endpoint}"
        if params:
            query_str = "&".join(f"{key}={value}" for key, value in params.items())
            url = f"{url}?{query_str}"

        try:
            # Get response but keep it in the context manager
            async with await self._handle_rate_limit(self.session, url) as response:
                if not response.status == 200:
                    logger.debug(f"Response status: {response.status}")
                    # logger.debug(f"Response headers: {response.headers}")
                
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"Error response for URL {url}: {response.status} - {error_text}")
                    response.raise_for_status()

                try:
                    # Use response.json() directly which handles gzip and chunked encoding
                    data = await response.json()
                    # logger.debug(f"Successfully parsed JSON response for {url}")
                    return data
                except Exception as e:
                    # If JSON parsing fails, try to get the raw text for debugging
                    text = await response.text()
                    logger.error(f"Failed to parse JSON from response. URL={url}, Error={e}")
                    logger.error(f"Raw response text: {text[:1000]}...")  # First 1000 chars
                    raise

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error for {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            raise

    async def get_all_courses(self) -> List[Dict[str, Any]]:
        """
        Asynchronously fetches all courses, paging through until all results are gathered.
        """
        logger.info("Fetching all courses...")
        all_courses = []
        page = 1
        per_page = 20

        while not self._stop:
            logger.info(f"Fetching courses page {page}...")
            params = {"page": page, "per": per_page}
            try:
                data = await self.get("/courses", params=params)
            except aiohttp.ClientResponseError as e:
                logger.error(f"ClientResponseError while fetching courses: status={e.status}, message={e.message}, url={e.request_info}")
                break
            except aiohttp.ClientConnectionError as e:
                logger.error(f"ClientConnectionError while fetching courses: {e}")
                break
            except aiohttp.ClientPayloadError as e:
                logger.error(f"ClientPayloadError while reading the response: {e}")
                break
            except aiohttp.ClientError as e:
                logger.error(f"Other aiohttp ClientError fetching courses: {e}")
                break
            except asyncio.CancelledError:
                logger.warning("User interrupted fetching courses. Stopping.")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching courses page {page}: {e}")
                break

            courses = data["courses"]
            all_courses.extend(courses)

            meta = data.get("meta", {})
            total_pages = meta.get("number_of_pages", 1)
            current_page = meta.get("page", page)
            if current_page >= total_pages:
                break
            page += 1

        return all_courses

    async def get_course(self, course_id: int) -> Dict[str, Any]:
        """
        Fetches a specific course by ID.
        """
        data = await self.get(f"/courses/{course_id}")
        return data["course"]

    async def get_course_content(self, course_id: int) -> Dict[str, Any]:
        """
        Fetch detailed information about a specific course, including all lectures and attachments.
        """
        course_data = await self.get_course(course_id)
        course_data["sections"] = course_data.pop("lecture_sections")

        for section in course_data["sections"]:
            section["lectures_detailed"] = []
            for lecture in section["lectures"]:
                try:
                    lecture_details = await self.get_lecture(course_id, lecture["id"])
                    lecture_details["section_id"] = section["id"]
                    lecture_details["section_name"] = section["name"]
                    lecture_details["section_position"] = section["position"]
                    section["lectures_detailed"].append(lecture_details)
                except aiohttp.ClientError as e:
                    logger.error(
                        f"Error fetching details for lecture ID {lecture['id']} in course ID {course_id}: {e}"
                    )
        return course_data

    async def get_lecture(self, course_id: int, lecture_id: int) -> Dict[str, Any]:
        """
        Fetches a specific lecture, including video details if present.
        """
        lecture_data = await self.get(f"/courses/{course_id}/lectures/{lecture_id}")
        attachments = lecture_data["lecture"].get("attachments", [])
        for attachment in attachments:
            if attachment["kind"] == "video":
                try:
                    video_data = await self.get_attachment_details(
                        course_id, lecture_id, attachment["id"], "video"
                    )
                    attachment["url_thumbnail"] = video_data["video"].get("url_thumbnail", "")
                    attachment["media_duration"] = video_data["video"].get("media_duration", 0)
                except aiohttp.ClientError as e:
                    logger.error(f"Error fetching video details for attachment ID {attachment['id']} in lecture ID {lecture_id}: {e}")

        return lecture_data["lecture"]

    async def get_attachment_details(
        self, course_id: int, lecture_id: int, attachment_id: int, attachment_kind: str
    ) -> Dict[str, Any]:
        """
        Fetches details for a specific attachment in an async manner.
        """
        if attachment_kind == "video":
            return await self.get(f"/courses/{course_id}/lectures/{lecture_id}/videos/{attachment_id}")
        return await self.get(f"/courses/{course_id}/lectures/{lecture_id}/attachments/{attachment_id}")

# Removed TaskManager and worker threads. We now use async concurrency.

async def rename_if_needed(directory: pathlib.Path, new_filename: str, attachment_id: str) -> None:
    """
    Checks if a file with the attachment ID exists, and if so, renames it to the new filename.
    Ignores .partial files as they are temporary download files.
    """
    # Find files containing the attachment ID, excluding .partial files
    existing_file = None
    for file in directory.iterdir():
        if (file.is_file() and 
            f"_{attachment_id}_" in file.name and 
            not file.name.endswith('.partial')):
            existing_file = file
            break

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

async def download_file(
    url: str, file_path: pathlib.Path, semaphore: asyncio.Semaphore,
    course_info: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Asynchronously downloads a file using aiohttp with a bounded semaphore for concurrency.
    Downloads to a .partial file first, then renames on successful completion.
    Supports resuming downloads if the server allows it.
    
    Args:
        url: The URL to download from
        file_path: Where to save the file
        semaphore: Concurrency limiter
        course_info: Optional dict containing course/lecture context for better error messages
    """
    if not url:
        logger.warning("Skipping download: Missing URL.")
        return False

    # Create partial download path
    partial_path = file_path.with_suffix(file_path.suffix + '.partial')
    RESUME_SAFETY_MARGIN = 1024 * 1024  # 1MB safety margin for resuming
    SMALL_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB threshold for size mismatch tolerance

    def format_error_context() -> str:
        """Helper to format error context from course_info if available"""
        if not course_info:
            return ""
        return (
            f"\nContext:"
            f"\n  Course: {course_info.get('course_name', 'Unknown')} (ID: {course_info.get('course_id', 'Unknown')})"
            f"\n  Module: {course_info.get('module_name', 'Unknown')} (ID: {course_info.get('module_id', 'Unknown')})"
            f"\n  Lecture: {course_info.get('lecture_name', 'Unknown')} (ID: {course_info.get('lecture_id', 'Unknown')})"
            f"\n  Attachment ID: {course_info.get('attachment_id', 'Unknown')}"
        )

    async with semaphore:
        try:
            timeout = aiohttp.ClientTimeout(total=3600, connect=60, sock_read=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # First request to check file size and server capabilities
                async with session.head(url, headers={"Accept-Ranges": "bytes"}) as head_response:
                    supports_resume = "Accept-Ranges" in head_response.headers
                    file_size = int(head_response.headers.get("Content-Length", 0))
                    
                    # If file exists and is larger than expected for small files, consider it complete
                    if file_path.exists():
                        actual_size = file_path.stat().st_size
                        if actual_size >= file_size and file_size <= SMALL_FILE_THRESHOLD:
                            logger.warning(
                                f"File size larger than expected for {format_filename_for_log(file_path.name)}. "
                                f"Expected: {file_size}, Got: {actual_size}. "
                                f"File is under {SMALL_FILE_THRESHOLD/(1024*1024)}MB - keeping existing file."
                            )
                            if partial_path.exists():
                                partial_path.unlink()
                            return True
                        elif actual_size == file_size:
                            logger.info(f"File already exists and is complete: {format_filename_for_log(file_path.name)}")
                            if partial_path.exists():
                                partial_path.unlink()
                            return True

                # Determine start position for resume
                start_pos = 0
                if partial_path.exists() and supports_resume:
                    partial_size = partial_path.stat().st_size
                    if partial_size > RESUME_SAFETY_MARGIN:
                        # Calculate the actual start position, accounting for the safety margin
                        start_pos = max(0, partial_size - RESUME_SAFETY_MARGIN)
                        logger.info(f"Resuming {format_filename_for_log(file_path.name)} from {start_pos / (1024*1024):.2f}MB")
                        
                        # Truncate the partial file to remove potentially corrupted data
                        with open(partial_path, "ab") as f:
                            f.truncate(start_pos)
                    else:
                        logger.info(f"Partial file too small to resume, starting fresh download of {format_filename_for_log(file_path.name)}")
                        partial_path.unlink()
                elif partial_path.exists():
                    logger.info(f"Server doesn't support resume, starting fresh download of {format_filename_for_log(file_path.name)}")
                    partial_path.unlink()
                elif file_path.exists():
                    logger.info(f"Incomplete file found, restarting download of {format_filename_for_log(file_path.name)}")

                # Prepare headers for resume if needed
                headers = {}
                if start_pos > 0:
                    headers["Range"] = f"bytes={start_pos}-"

                async with session.get(url, headers=headers) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        attachment_id = course_info.get('attachment_id') if course_info else None
                        admin_urls = format_admin_urls(course_info, attachment_id)
                        
                        logger.error(
                            f"Download failed [{response.status}]: {url}"
                            # f"\nError response: {error_text}"
                            # f"{format_error_context()}"
                            f"{admin_urls}"
                        )
                        # Write error message to file for visibility
                        if response.status == 403:
                            error_msg = f"Cannot fetch file: {response.status} {response.reason}"
                            file_path.write_text(error_msg)
                        return False

                    try:
                        # Check available disk space
                        import shutil
                        needed_space = file_size if start_pos == 0 else (file_size - start_pos)
                        free_space = shutil.disk_usage(partial_path.parent).free
                        if needed_space > free_space:
                            logger.error(
                                f"Insufficient disk space for {format_filename_for_log(file_path.name)}. "
                                f"Required: {needed_space / (1024*1024):.2f}MB, "
                                f"Available: {free_space / (1024*1024):.2f}MB"
                            )
                            logger.error(f"Download URL for manual attempt: {url}")
                            return False

                        # Open file in append mode if resuming, write mode if starting fresh
                        mode = "ab" if start_pos > 0 else "wb"
                        with open(partial_path, mode) as out_file:
                            chunk_size = 16 * 1024 * 1024  # 16MB chunks
                            downloaded = start_pos
                            
                            if start_pos == 0:
                                logger.info(f"Downloading {format_filename_for_log(file_path.name)} ({file_size / (1024*1024):.2f} MB)")
                            
                            async for chunk in response.content.iter_chunked(chunk_size):
                                try:
                                    if not chunk:
                                        break
                                    out_file.write(chunk)
                                    downloaded += len(chunk)
                                    if file_size:
                                        progress = (downloaded / file_size) * 100
                                        if downloaded % (50 * 1024 * 1024) == 0:  # Log every 50MB
                                            logger.debug(f"{progress:.1f}%")
                                except asyncio.CancelledError:
                                    logger.info(f"Download interrupted for {format_filename_for_log(file_path.name)}")
                                    return False

                        # Modified size verification
                        actual_size = partial_path.stat().st_size
                        if actual_size != file_size:
                            if actual_size > file_size and file_size <= SMALL_FILE_THRESHOLD:
                                logger.warning(
                                    f"File size larger than expected for {format_filename_for_log(file_path.name)}. "
                                    f"Expected: {file_size}, Got: {actual_size}. "
                                    f"File is under {SMALL_FILE_THRESHOLD/(1024*1024)}MB - keeping downloaded file."
                                )
                                partial_path.rename(file_path)
                                return True
                            else:
                                attachment_id = course_info.get('attachment_id') if course_info else None
                                admin_urls = format_admin_urls(course_info, attachment_id)
                                
                                logger.error(
                                    f"File size mismatch for {format_filename_for_log(file_path.name)}. "
                                    f"Expected: {file_size}, Got: {actual_size}"
                                    # f"{format_error_context()}"
                                    f"{admin_urls}"
                                )
                                logger.error(f"Download URL for manual attempt: {url}")
                                return False

                        # Rename partial file to final filename on success
                        partial_path.rename(file_path)
                        logger.info(
                            f"Completed: {format_filename_for_log(file_path.name)} - "
                            f"{course_info.get('course_name', 'Unknown')} - "
                            f"Module: {course_info.get('module_name', 'Unknown')}"
                        )
                        return True

                    except OSError as e:
                        logger.error(
                            f"OS Error while writing file {format_filename_for_log(file_path.name)}: {e}"
                            f"{format_error_context()}\n"
                            f"Error type: {type(e).__name__}\n"
                            f"Error details: {str(e)}\n"
                            f"Download URL for manual attempt: {url}"
                        )
                        return False

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            attachment_id = course_info.get('attachment_id') if course_info else None
            admin_urls = format_admin_urls(course_info, attachment_id)
            
            error_msg = (
                f"{'Timeout' if isinstance(e, asyncio.TimeoutError) else 'Network error'} "
                f"downloading {format_filename_for_log(file_path.name)}: {e}"
                f"{format_error_context()}"
                f"{admin_urls}\n"
                f"Error type: {type(e).__name__}\n"
                f"Error details: {str(e)}\n"
                f"Download URL for manual attempt: {url}"
            )
            logger.error(error_msg)
            return False
        except Exception as e:
            attachment_id = course_info.get('attachment_id') if course_info else None
            admin_urls = format_admin_urls(course_info, attachment_id)
            
            logger.error(
                f"Unexpected error downloading {format_filename_for_log(file_path.name)}: {e}"
                f"{format_error_context()}"
                f"{admin_urls}\n"
                f"Error type: {type(e).__name__}\n"
                f"Error details: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}\n"
                f"Download URL for manual attempt: {url}"
            )
            return False

@dataclass
class DownloadTask:
    """Represents a single download task with all necessary metadata"""
    url: str
    file_path: pathlib.Path
    course_id: int
    lecture_id: int
    attachment_id: int
    attachment_name: str
    file_size: Optional[int] = None
    course_name: Optional[str] = None
    module_id: Optional[int] = None
    module_name: Optional[str] = None
    lecture_name: Optional[str] = None

    def to_context_dict(self) -> Dict[str, Any]:
        """Convert task metadata to a context dictionary for error messages"""
        return {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'module_id': self.module_id,
            'module_name': self.module_name,
            'lecture_id': self.lecture_id,
            'lecture_name': self.lecture_name,
            'attachment_id': self.attachment_id
        }

class DownloadManager:
    """Centralized download manager for handling concurrent downloads"""
    def __init__(self, max_concurrent: int = MAX_CONCURRENT_DOWNLOADS):
        self.queue: Queue[DownloadTask] = Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self._stop = False
        self._consumers: List[asyncio.Task] = []
        self._started = False
        self.failed_downloads: Set[int] = set()  # Track failed download IDs
        self._active_count = 0  # Add explicit counter for active downloads

    def get_status(self) -> str:
        """Returns current download manager status"""
        # Clean up completed tasks from active_downloads
        self.active_downloads = {
            id_: task for id_, task in self.active_downloads.items() 
            if not task.done()
        }
        return (
            f"Active downloads: {len(self.active_downloads)}, "
            f"Queue size: {self.queue.qsize()}, "
            f"Failed downloads: {len(self.failed_downloads)}"
        )

    def stop(self) -> None:
        """Signal the download manager to stop processing new downloads"""
        self._stop = True
        # Cancel all active downloads
        for task in self.active_downloads.values():
            if not task.done():
                task.cancel()
        # Cancel all consumers
        for consumer in self._consumers:
            if not consumer.done():
                consumer.cancel()

    async def ensure_consumers_running(self, num_consumers: int = 3) -> None:
        """Ensures consumers are running, starts them if not"""
        if not self._started:
            await self.start_consumers(num_consumers)
            self._started = True

    async def add_task(self, task: DownloadTask) -> None:
        """Add a new download task to the queue and ensure consumers are running"""
        if self._stop:
            return
        # Ensure consumers are running before adding task
        await self.ensure_consumers_running()
        await self.queue.put(task)

    async def start_consumers(self, num_consumers: int = 3) -> None:
        """Start consumer tasks to process downloads"""
        self._consumers = [
            asyncio.create_task(self._consumer_worker(f"consumer-{i}"))
            for i in range(num_consumers)
        ]

    async def _consumer_worker(self, worker_id: str) -> None:
        """Worker that processes download tasks from the queue"""
        while not self._stop:
            task = None
            try:
                task = await self.queue.get()
                if task is None:  # Sentinel value for shutdown
                    self.queue.task_done()
                    break

                # Skip if this task previously failed
                if task.attachment_id in self.failed_downloads:
                    logger.debug(f"Skipping previously failed download: {task.attachment_name}")
                    self.queue.task_done()
                    continue

                # Check if file already exists and is complete
                if await self._is_file_complete(task):
                    self.queue.task_done()
                    continue

                # Process the download
                download_task = asyncio.create_task(
                    self._process_download(task)
                )
                self.active_downloads[task.attachment_id] = download_task
                
                try:
                    success = await download_task
                    if not success:
                        # Mark this download as failed to prevent retries
                        self.failed_downloads.add(task.attachment_id)
                        logger.debug(f"Download failed and marked as failed: {task.attachment_name} - {self.get_status()}")
                except asyncio.CancelledError:
                    logger.info(f"Download cancelled for {task.attachment_name} - {self.get_status()}")
                    self.failed_downloads.add(task.attachment_id)  # Mark cancelled downloads as failed
                except Exception as e:
                    logger.error(f"Error downloading {task.attachment_name}: {e} - {self.get_status()}")
                    self.failed_downloads.add(task.attachment_id)
                finally:
                    # Clean up the active download
                    if task.attachment_id in self.active_downloads:
                        self.active_downloads.pop(task.attachment_id)
                    self.queue.task_done()
                    status = self.get_status()  # Get fresh status after cleanup
                    logger.debug(f"Task completed - {status}")

                    # If queue is empty and no active downloads, log final status
                    if self.queue.empty() and not self.active_downloads:
                        logger.info(f"All downloads completed - {status}")

            except asyncio.CancelledError:
                if task:
                    self.queue.task_done()
                break
            except Exception as e:
                if task:
                    self.queue.task_done()
                logger.error(f"Error in consumer {worker_id}: {e} - {self.get_status()}")

    async def _is_file_complete(self, task: DownloadTask) -> bool:
        """Check if the file already exists and is complete"""
        if not task.file_path.exists():
            return False
            
        if task.file_size is None:
            # Fetch file size from server if not provided
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(task.url) as response:
                        task.file_size = int(response.headers.get("Content-Length", 0))
            except Exception as e:
                logger.error(f"Error fetching file size for {task.attachment_name}: {e}")
                return False

        return task.file_path.stat().st_size == task.file_size

    async def _process_download(self, task: DownloadTask) -> None:
        """Process a single download task"""
        async with self.semaphore:
            await download_file(
                task.url, 
                task.file_path, 
                self.semaphore,
                course_info=task.to_context_dict()
            )

    async def wait_for_downloads(self) -> None:
        """Wait for all queued downloads to complete"""
        if self.queue.empty() and not self.active_downloads:
            logger.info("No downloads to wait for")
            return
            
        try:
            await asyncio.wait_for(self.queue.join(), timeout=30)  # Add timeout
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for downloads to complete - {self.get_status()}")
            self._stop = True  # Signal consumers to stop
            
        # Clean up any remaining active downloads
        active_tasks = [task for task in self.active_downloads.values() if not task.done()]
        if active_tasks:
            logger.warning(f"Cancelling {len(active_tasks)} remaining downloads")
            for task in active_tasks:
                task.cancel()
            
            try:
                await asyncio.wait_for(
                    asyncio.gather(*active_tasks, return_exceptions=True),
                    timeout=10
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for active downloads to cancel")

        # Final cleanup
        self.active_downloads.clear()
        logger.info(f"Download manager shutdown complete - {self.get_status()}")

async def process_course(
    api_client: TeachableAPIClient,
    course_id: int,
    module_id: Optional[int],
    lecture_id: Optional[int],
    output_dir: pathlib.Path,
    valid_types: List[str],
    download_manager: DownloadManager
) -> None:
    """Modified to start downloads immediately when attachments are discovered"""
    try:
        course_data = await api_client.get_course(course_id)
        course_name = course_data["name"]
        logger.info(f"Processing course: {course_name} (ID: {course_id})")
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching course {course_id}: {e}")
        return

    course_dirname = f"{course_id} - {safe_filename(course_name)}"
    course_dir = output_dir / course_dirname
    course_dir.mkdir(parents=True, exist_ok=True)

    # Potential rename check
    all_courses = await api_client.get_all_courses()
    for c in all_courses:
        if c["id"] == course_id and c["name"] != course_name:
            rename_course_directory(output_dir, course_id, course_name, c["name"])
            course_name = c["name"]
            course_dirname = f"{course_id} - {safe_filename(course_name)}"
            course_dir = output_dir / course_dirname
            break

    # Backup existing CSV
    course_data_path = course_dir / "course_data.csv"
    backup_existing_file(course_data_path)

    # Fetch course content
    logger.info(f"Fetching details for course: {course_name} (ID: {course_id})")
    try:
        course_content = await api_client.get_course_content(course_id)
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching course sections for course ID {course_id}: {e}")
        return

    processed_data = []
    download_tasks = set()  # Track download tasks for this course

    async def queue_download(attachment: Dict[str, Any], 
                           file_path: pathlib.Path,
                           lecture: Dict[str, Any]) -> None:
        """Helper to queue a download and track its task"""
        if url := attachment.get("url"):
            download_task = DownloadTask(
                url=url,
                file_path=file_path,
                course_id=course_id,
                lecture_id=lecture["id"],
                attachment_id=attachment["id"],
                attachment_name=attachment.get("name", "")
            )
            task = asyncio.create_task(download_manager.add_task(download_task))
            download_tasks.add(task)

    try:
        for section in course_content["sections"]:
            if module_id and section["id"] != module_id:
                continue

            logger.info(f"  Processing section: {section['name']}")
            section_position = section["position"]

            for lecture in section["lectures_detailed"]:
                if lecture_id and lecture_id != lecture["id"]:
                    continue

                lecture_name = lecture['name']
                if len(lecture_name) > 76:
                    lecture_name = lecture_name[:76] + "..."
                logger.info(f"    Processing lecture: {lecture_name}")

                # Process attachments and queue downloads immediately
                for attachment in lecture["attachments"]:
                    attachment_kind = attachment.get("kind")
                    if not attachment_kind or attachment_kind not in valid_types:
                        continue

                    attachment_name = normalize_utf_filename(attachment.get("name") or "")
                    filename = f"{section_position:02d}_{lecture['position']:02d}_{attachment['position']:02d}_{attachment['id']}_{safe_filename(attachment_name)}"
                    file_path = course_dir / filename

                    # Queue download immediately
                    await queue_download(attachment, file_path, lecture)

                # Add lecture data to processed_data for CSV
                processed_lecture_data = process_lecture_data(
                    lecture, 
                    course_id, 
                    course_name, 
                    section_position, 
                    section["name"]
                )
                processed_data.extend(processed_lecture_data)

        # Save processed data to CSV
        course_data_path = course_dir / "course_data.csv"
        save_data_to_csv(processed_data, course_data_path)
        logger.info(f"Course data saved to {course_data_path}")

        # Wait for all downloads from this course to be queued
        if download_tasks:
            await asyncio.gather(*download_tasks)

    except Exception as e:
        logger.error(f"Error processing course {course_id}: {e}")
        raise

async def main() -> None:
    """Updated main function to use the download manager"""
    import argparse
    parser = argparse.ArgumentParser(description="Manage and download course data from Teachable.")
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")

    parser_fetch_all = subparsers.add_parser("fetch-all", help="Fetch and save all courses")
    parser_fetch_all.add_argument("--output", "-o", type=pathlib.Path, default=".", help="Directory to save the all courses CSV")

    parser_process = subparsers.add_parser("process", help="Process and download data for specific courses")
    parser_process.add_argument("course_ids", metavar="course_id", type=int, nargs="+", help="One or more Course IDs to process")
    parser_process.add_argument("--module_id", type=int, default=None, help="Optional module ID to filter processing")
    parser_process.add_argument("--lecture_id", type=int, default=None, help="Optional lecture ID to filter processing")
    parser_process.add_argument("--output", "-o", type=pathlib.Path, default=".", help="Directory to save course data")

    # ----------------------------------------------------------------------
    # NEW SUBCOMMAND: test-snippet
    # Replicates the sync taken from the API Docs testing
    # ----------------------------------------------------------------------
    parser_test_snippet = subparsers.add_parser(
        "test-snippet",
        help="Fetch exactly 2 courses (page=1&per=2) and print the raw JSON, mimicking your working requests example."
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

    # Convert 'pdf' to 'pdf_embed'
    if "pdf" in args.types:
        args.types.append("pdf_embed")
        args.types.remove("pdf")

    download_manager = DownloadManager(MAX_CONCURRENT_DOWNLOADS)
    
    try:
        # Start the download manager consumers
        await download_manager.start_consumers()

        async with TeachableAPIClient(api_key=os.environ.get("TEACHABLE_API_KEY", "")) as api_client:
            if args.operation == "test-snippet":
                # This precisely replicates the "requests" snippet:
                url = "/courses"
                params = {"page": 1, "per": 2}
                # The next call uses our existing TeachableAPIClient.get()
                # method, which includes concurrency-limits, rate-limit logic, etc.
                try:
                    data = await api_client.get(url, params=params)
                    # Print the raw JSON dict
                    import json
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except Exception as exc:
                    logger.error(f"Error while fetching test snippet data: {exc}")

                # End after printing the snippet
                return
            elif args.operation == "fetch-all":
                try:
                    courses = await api_client.get_all_courses()
                    file_path = args.output / "all_courses_data.csv"
                    save_data_to_csv(courses, file_path)
                    logger.info(f"All courses saved to {file_path}")
                except asyncio.CancelledError:
                    logger.info("Operation interrupted. Progress saved.")
                    return
            elif args.operation == "process":
                try:
                    for course_id in args.course_ids:
                        await process_course(
                            api_client,
                            course_id,
                            args.module_id,
                            args.lecture_id,
                            args.output,
                            args.types,
                            download_manager
                        )
                    # Wait for all downloads to complete
                    await download_manager.wait_for_downloads()
                except asyncio.CancelledError:
                    logger.info("Processing interrupted. Waiting for active downloads to complete...")
                    download_manager.stop()
                    return

        logger.info("All tasks completed successfully.")
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down gracefully...")
        download_manager.stop()
    finally:
        await download_manager.wait_for_downloads()
        logger.info("Cleanup complete.")

# Updated entry point with proper signal handling for Windows
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down gracefully...")