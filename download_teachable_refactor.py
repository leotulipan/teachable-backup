import csv
import os
import pathlib
import re
import sys
import time
import traceback
import unicodedata
from typing import Any, Dict, List, Optional

import asyncio
import aiohttp

from dotenv import load_dotenv
from loguru import logger

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

def normalize_utf_filename(filename: str) -> str:
    """Normalizes a filename by removing unsafe characters and enforcing length limits."""
    normalized_filename = unicodedata.normalize("NFKD", filename)
    return safe_filename(normalized_filename)

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
                    async with session.get(url, headers=self.headers) as response:
                        if response.status != 429:
                            logger.debug(f"Received {response} response.")
                            return response

                        logger.debug(f"Received 429 response. Rate limit headers: {response.headers}")
                        reset_time_str = response.headers.get("RateLimit-Reset", "")
                        if reset_time_str.isdigit():
                            delay = int(reset_time_str)
                            logger.warning(f"Rate limit reached. Retrying after {delay} seconds (RateLimit-Reset).")
                        else:
                            delay = self.initial_delay * (self.delay_factor ** retries)
                            logger.warning(f"Rate limit reached; no valid 'RateLimit-Reset'. Retrying in {delay}s.")
                        await asyncio.sleep(delay)
                        retries += 1
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
            response = await self._handle_rate_limit(self.session, url)
        except Exception as e:
            logger.error(f"Exception occurred while fetching URL {url} in _handle_rate_limit: {e}")
            raise

        if response.status >= 400:
            # Use .read() to download all content even if chunked
            error_bytes = await response.read()
            logger.error(
                f"Error response for URL {url}: {response.status} - "
                f"{error_bytes[:500].decode(errors='replace')}..."  # log a partial preview
            )
            response.raise_for_status()

        # If we get here, we have a 2xx or 3xx response
        # Force a full read of the body before parsing,
        # so we can catch chunked / partial data errors
        try:
            raw_bytes = await response.read()
            logger.debug(f"Successfully read {len(raw_bytes)} bytes from URL {url}.")
        except Exception as e:
            logger.error(f"Could not read body for URL {url}: {e}")
            raise

        # Convert bytes to string and parse JSON
        try:
            raw_text = raw_bytes.decode(errors="replace")
            logger.debug(f"Raw text (first 500 chars) for {url}: {raw_text[:500]}...")
            json_data = aiohttp.helpers.json_loads(raw_text)
            logger.debug(f"parsed JSON for {url}: {json_data}")
            return json_data
        except Exception as e:
            logger.error(f"Failed to parse JSON from body. URL={url}, Error={e}\nRaw text:\n{raw_text}")
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
    (Converted to async but action remains file-based, so no real concurrency changes needed.)
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

async def download_file(
    url: str, file_path: pathlib.Path, semaphore: asyncio.Semaphore
) -> bool:
    """
    Asynchronously downloads a file using aiohttp with a bounded semaphore for concurrency.
    """
    if not url:
        logger.warning("Skipping download: Missing URL.")
        return False

    async with semaphore:  # Limit concurrency here
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status >= 400:
                        logger.error(f"Download failed [{response.status}]: {url}")
                        return False

                    file_size = int(response.headers.get("Content-Length") or 0)
                    if file_path.exists() and file_path.stat().st_size == file_size:
                        logger.info(f"File already exists and is complete: {file_path.name}")
                        return True
                    elif file_path.exists():
                        logger.warning(f"File size mismatch, re-downloading: {file_path.name}")
                        file_path.unlink()

                    with open(file_path, "wb") as out_file:
                        while True:
                            chunk = await response.content.read(1024 * 1024)
                            if not chunk:
                                break
                            out_file.write(chunk)

            logger.info(f"Downloaded: {file_path.name}")
            return True
        except aiohttp.ClientError as e:
            logger.error(f"Error downloading {url}: {e}")
            if file_path.exists():
                file_path.unlink()
            return False

async def process_course(
    api_client: TeachableAPIClient,
    course_id: int,
    module_id: Optional[int],
    lecture_id: Optional[int],
    output_dir: pathlib.Path,
    valid_types: List[str],
    semaphore: asyncio.Semaphore
) -> None:
    """
    Processes a single course (in series), then spawns async downloads for attachments
    with concurrency limited by the semaphore.
    """
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
    download_tasks = []

    for section in course_content["sections"]:
        if module_id and section["id"] != module_id:
            continue

        logger.info(f"  Processing section: {section['name']}")
        section_position = section["position"]

        for lecture in section["lectures_detailed"]:
            if lecture_id and lecture_id != lecture["id"]:
                logger.warning(f"Skipping lecture due to lecture ID filter: {lecture['name']}")
                continue

            logger.info(f"    Processing lecture: {lecture['name']}")
            for attachment in lecture["attachments"]:
                attachment_kind = attachment.get("kind")
                if attachment_kind is None:
                    logger.warning(f"Attachment {attachment.get('name', 'Unnamed')} has no 'kind'. Skipping.")
                    continue
                if attachment_kind not in valid_types:
                    continue

                attachment_name = normalize_utf_filename(attachment.get("name") or "")
                filename = f"{section_position:02d}_{lecture['position']:02d}_{attachment['position']:02d}_{attachment['id']}_{safe_filename(attachment_name)}"
                file_path = course_dir / filename

                await rename_if_needed(course_dir, filename, str(attachment["id"]))
                existing_file = find_file_by_partial_name(course_dir, f"_{attachment['id']}_")
                if existing_file:
                    logger.info(f"Skipping download: File for attachment {course_dir}/{attachment['id']} already exists.")
                    continue

                # Queue async download
                url = attachment.get("url")
                download_tasks.append(download_file(url, file_path, semaphore))

            # Prepare CSV data
            processed_lecture_data = process_lecture_data(
                lecture, 
                course_id, 
                course_name, 
                section_position, 
                section["name"]
            )
            processed_data.extend(processed_lecture_data)

            # Save embedded text or quiz attachments if present
            for att in lecture["attachments"]:
                kind = att.get("kind")
                if kind in ("text", "code_embed", "code_display"):
                    fname = safe_filename(f"{section_position:02d}_{lecture['position']:02d}_{att['position']:02d}_{att['id']}_{att['name']}")
                    file_path = course_dir / f"{fname}.html"
                    if att.get("text"):
                        save_text_attachment(att["text"], file_path)
                elif kind == "quiz":
                    fname = safe_filename(f"{section_position:02d}_{lecture['position']:02d}_{att['position']:02d}_{att['id']}_{att['name']}_quiz")
                    file_path = course_dir / f"{fname}.json"
                    if att.get("quiz"):
                        save_json_attachment(att["quiz"], file_path)

    # Save processed data to CSV
    save_data_to_csv(processed_data, course_data_path)
    logger.info(f"Course data saved to {course_data_path}. Now downloading attachments...")

    # Run all download tasks concurrently
    await asyncio.gather(*download_tasks)
    logger.info(f"All downloads for course {course_id} finished.")

async def main() -> None:
    """
    Main async entry point. Handles argument parsing, sets up concurrency, and processes courses.
    """
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
    # Replicates the exact sync snippet you provided, but in async form.
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

    async with TeachableAPIClient(api_key=os.environ.get("TEACHABLE_API_KEY", "")) as api_client:
        # ------------------------------------------------------------------
        # Handle the new "test-snippet" subcommand
        # ------------------------------------------------------------------
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
        # ------------------------------------------------------------------

        if args.operation == "fetch-all":
            courses = await api_client.get_all_courses()
            file_path = args.output / "all_courses_data.csv"
            save_data_to_csv(courses, file_path)
            logger.info(f"All courses saved to {file_path}")
            return

        if args.operation == "process":
            # Setup a semaphore for concurrency-limited downloads
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

            for course_id in args.course_ids:
                # Process one course at a time, but attachments for that course download concurrently
                await process_course(
                    api_client,
                    course_id,
                    args.module_id,
                    args.lecture_id,
                    args.output,
                    args.types,
                    semaphore
                )
    logger.info("All tasks finished.")

# Updated entry point for async
if __name__ == "__main__":
    asyncio.run(main())