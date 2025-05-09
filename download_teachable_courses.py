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
from collections import defaultdict
from datetime import datetime, timedelta, timezone, UTC
import json

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

def format_admin_urls(course_info: Optional[Dict[str, Any]], 
                     attachment_id: Optional[int] = None, 
                     attachment_kind: Optional[str] = None,
                     url: Optional[str] = None) -> str:
    """
    Formats admin URLs for troubleshooting download issues.
    
    Args:
        course_info: Dictionary containing course context
        attachment_id: ID of the attachment
        attachment_kind: Type of attachment ('video', 'pdf', etc.)
        url: Direct download URL
    
    Note: These URLs only work for logged-in admin users in the Teachable backend.
    """
    if not course_info:
        return ""

    frontend_domain = os.environ.get("TEACHABLE_FRONTEND_DOMAIN", "your-teachable-domain.com")
    if not frontend_domain or not course_info.get('course_id') or not course_info.get('lecture_id'):
        return ""

    # Instead of including newlines in the message, format each line as a separate log entry
    admin_urls = []
    
    # Frontend URL to view the lecture
    admin_urls.append(
        f"View lecture: https://{frontend_domain}/admin-app/courses/{course_info['course_id']}/curriculum/lessons/{course_info['lecture_id']}"
    )
    
    # API endpoint for manual download (only for videos)
    if attachment_id and attachment_kind == 'video':
        admin_urls.append(
            f"Manual video download: https://{frontend_domain}/api/v1/attachments/{attachment_id}/hotmart_video_download_link"
        )
    
    # Add direct download URL if provided
    if url:
        admin_urls.append(f"Direct download attempt: {url}")
    
    # Return URLs formatted for separate logging
    return "\n".join(admin_urls)

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
                # Only log retries, not initial requests
                if retries > 0:
                    logger.debug(f"Retrying URL: {url} (Retry {retries})")
                
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

async def rename_if_needed(directory: pathlib.Path, new_filename: str, attachment_id: str) -> None:
    """
    Checks if files with the attachment ID exist, and if so:
    1. If multiple files exist, keeps only the newest one with same size
    2. Renames the kept file to the new filename
    Ignores .partial files as they are temporary download files.
    """
    # Find all files containing the attachment ID, excluding .partial files
    matching_files = [
        file for file in directory.iterdir()
        if (file.is_file() and 
            f"_{attachment_id}_" in file.name and 
            not file.name.endswith('.partial'))
    ]

    if len(matching_files) > 1:
        # Group files by size
        files_by_size = {}
        for file in matching_files:
            size = file.stat().st_size
            if size not in files_by_size:
                files_by_size[size] = []
            files_by_size[size].append(file)

        # For each size group, keep only the newest file
        for size, files in files_by_size.items():
            if len(files) > 1:
                # Sort by modification time, newest first
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                newest_file = files[0]
                
                # Remove all but the newest file
                for file in files[1:]:
                    try:
                        file.unlink()
                        logger.info(f"Removed duplicate file: {file}")
                    except OSError as e:
                        logger.error(f"Error removing duplicate file {file}: {e}")

        # After cleanup, get the remaining file
        matching_files = [
            file for file in directory.iterdir()
            if (file.is_file() and 
                f"_{attachment_id}_" in file.name and 
                not file.name.endswith('.partial'))
        ]

    # Proceed with renaming if we have a file
    if matching_files:
        existing_file = matching_files[0]
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
    url: str, 
    file_path: pathlib.Path, 
    semaphore: asyncio.Semaphore,
    course_info: Optional[Dict[str, Any]] = None,
    verify: bool = False
) -> bool:
    """
    Asynchronously downloads a file using aiohttp with a bounded semaphore for concurrency.
    Downloads to a .partial file first, then renames on successful completion.
    For small files (<1MB), always downloads fresh to avoid partial file issues.
    
    Args:
        url: The URL to download from
        file_path: Where to save the file
        semaphore: Concurrency limiter
        course_info: Optional dict containing course/lecture context
        verify: Whether to verify existing files with HEAD request
    """
    if not url:
        logger.error("Skipping download: Missing URL.")
        return False

    # Create partial download path
    partial_path = file_path.with_suffix(file_path.suffix + '.partial')
    SMALL_FILE_THRESHOLD = 1024 * 1024  # 1MB threshold for small files
    RESUME_SAFETY_MARGIN = 1024 * 1024  # 1MB safety margin for resuming
    start_pos = 0
    file_size = 0
    supports_resume = False

    async with semaphore:
        try:
            timeout = aiohttp.ClientTimeout(total=3600, connect=60, sock_read=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Do HEAD request to get file size
                async with session.head(url, headers={"Accept-Ranges": "bytes"}) as head_response:
                    if head_response.status == 403:
                        # Handle 403 Forbidden error
                        attachment_id = course_info.get('attachment_id') if course_info else None
                        attachment_kind = course_info.get('attachment_kind')
                        admin_urls = format_admin_urls(course_info, attachment_id, attachment_kind, url)
                        
                        logger.error(f"Access forbidden (403) for: {format_filename_for_log(file_path.name)}")
                        for url_line in admin_urls.split('\n'):
                            logger.error(url_line)
                        
                        if file_path.exists():
                            file_path.unlink()
                        return False
                    
                    supports_resume = "Accept-Ranges" in head_response.headers
                    file_size = int(head_response.headers.get("Content-Length", 0))
                    logger.debug(
                        f"HEAD request for {format_filename_for_log(file_path.name)}: "
                        f"size={file_size:,} bytes, supports_resume={supports_resume}"
                    )
                    
                    # For small files, always start fresh
                    if file_size < SMALL_FILE_THRESHOLD:
                        if partial_path.exists():
                            partial_path.unlink()
                        # If final file exists and we're not verifying, skip download
                        if file_path.exists() and not verify:
                            actual_size = file_path.stat().st_size
                            if actual_size == file_size:
                                logger.info(f"Small file verified complete: {format_filename_for_log(file_path.name)}")
                                return True
                            # For small files, if size mismatch, remove and redownload
                            logger.info(f"Size mismatch for small file, redownloading: {format_filename_for_log(file_path.name)}")
                            file_path.unlink()
                
                # Start the actual download
                headers = {"Range": f"bytes={start_pos}-"} if start_pos > 0 else {}
                async with session.get(url, headers=headers) as response:
                    if response.status == 403:
                        # Handle 403 Forbidden error
                        attachment_id = course_info.get('attachment_id') if course_info else None
                        attachment_kind = course_info.get('attachment_kind')
                        admin_urls = format_admin_urls(course_info, attachment_id, attachment_kind, url)
                        
                        logger.error(f"Access forbidden (403) for: {format_filename_for_log(file_path.name)}")
                        for url_line in admin_urls.split('\n'):
                            logger.error(url_line)
                        
                        if file_path.exists():
                            file_path.unlink()
                        return False
                    elif response.status >= 400:
                        error_text = await response.text()
                        attachment_id = course_info.get('attachment_id') if course_info else None
                        attachment_kind = course_info.get('attachment_kind')
                        admin_urls = format_admin_urls(course_info, attachment_id, attachment_kind, url)
                        
                        logger.error(f"Download failed [{response.status}]: {format_filename_for_log(file_path.name)}")
                        for url_line in admin_urls.split('\n'):
                            logger.error(url_line)
                        
                        if file_path.exists():
                            file_path.unlink()
                        return False

                    # For small files, download directly to final location
                    output_path = file_path if file_size < SMALL_FILE_THRESHOLD else partial_path
                    
                    try:
                        with open(output_path, "wb") as out_file:
                            chunk_size = 8 * 1024 * 1024  # 8MB instead of 16MB
                            downloaded = 0
                            
                            logger.info(
                                f"Downloading {format_filename_for_log(file_path.name)} "
                                f"({file_size / (1024*1024):.2f} MB)"
                            )
                            last_log_time = time.time()

                            async for chunk in response.content.iter_chunked(chunk_size):
                                if not chunk:
                                    break
                                out_file.write(chunk)
                                downloaded += len(chunk)

                                # Log progress every 10 seconds or every chunk if <10s
                                now = time.time()
                                if now - last_log_time >= 10:
                                    if file_size:
                                        progress = (downloaded / file_size) * 100
                                        logger.debug(f"Progress: {progress:.1f}% for {format_filename_for_log(file_path.name)}")
                                    last_log_time = now

                            # Ensure all data is written to disk
                            out_file.flush()
                            os.fsync(out_file.fileno())

                        # For larger files, verify and rename partial file
                        if file_size >= SMALL_FILE_THRESHOLD:
                            actual_size = partial_path.stat().st_size
                            if actual_size != file_size:
                                logger.error(
                                    f"File size mismatch for {format_filename_for_log(file_path.name)}. "
                                    f"Expected: {file_size:,}, Got: {actual_size:,}"
                                )
                                return False

                            # Rename partial file to final filename
                            if file_path.exists():
                                file_path.unlink()
                            partial_path.rename(file_path)

                        logger.info(
                            f"Completed: {format_filename_for_log(file_path.name)} - "
                            f"{course_info.get('course_name', 'Unknown')} - "
                            f"Module: {course_info.get('module_name', 'Unknown')}"
                        )
                        return True

                    except OSError as e:
                        logger.error(f"OS Error while writing file {format_filename_for_log(file_path.name)}: {e}")
                        return False

        except Exception as e:
            logger.error(f"Error downloading {format_filename_for_log(file_path.name)}: {e}")
            if file_path.exists():
                file_path.unlink()
            # if partial_path.exists():
            #     partial_path.unlink()
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
    attachment_kind: str  # Add attachment type
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
            'attachment_id': self.attachment_id,
            'attachment_kind': self.attachment_kind  # Include attachment type in context
        }

@dataclass
class DownloadFailure:
    course_id: int
    course_name: str
    attachment_id: int
    filename: str
    actual_size: Optional[int]
    expected_size: Optional[int]
    view_lecture_url: str
    manual_video_url: Optional[str]
    direct_download_url: str
    error_type: str  # e.g. "size_mismatch", "download_failed", etc.

class DownloadManager:
    """Centralized download manager for handling concurrent downloads"""
    def __init__(self, max_concurrent: int = MAX_CONCURRENT_DOWNLOADS):
        self.queue: Queue[DownloadTask] = Queue()
        self.max_concurrent = max_concurrent
        self.current_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(self.current_concurrent)
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self._stop = False
        self._consumers: List[asyncio.Task] = []
        self._started = False
        self.failed_downloads: Set[int] = set()  # Track actual failed downloads
        self.completed_downloads: Set[int] = set()  # Track successful downloads
        self._active_count = 0
        self.failures: List[DownloadFailure] = []
        self.consecutive_successes: int = 0  # track consecutive successful downloads

    def get_status(self) -> str:
        """Returns current download manager status"""
        self.active_downloads = {
            id_: task for id_, task in self.active_downloads.items() 
            if not task.done()
        }
        status = (
            f"Active downloads: {len(self.active_downloads)}, "
            f"Queue size: {self.queue.qsize()}"
        )
        
        if self.completed_downloads:
            status += f", Completed: {len(self.completed_downloads)}"
        
        # Only include failed downloads if there are actual failures
        if self.failed_downloads:
            status += f", Failed downloads: {len(self.failed_downloads)}"
            
        return status

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

    def reduce_concurrency_to_one(self) -> None:
        """
        Temporarily reduce concurrency to 1.
        Resets the current semaphore to a single slot.
        """
        self.current_concurrent = 1
        self.semaphore = asyncio.Semaphore(self.current_concurrent)
        self.consecutive_successes = 0
        logger.warning("Reduced concurrency to 1 due to cancelled download.")

    def restore_max_concurrency_if_ready(self) -> None:
        """
        If we have at least 2 consecutive successes, restore concurrency to the original max.
        """
        if self.current_concurrent < self.max_concurrent and self.consecutive_successes >= 2:
            self.current_concurrent = self.max_concurrent
            self.semaphore = asyncio.Semaphore(self.current_concurrent)
            logger.warning(f"Restored concurrency to max ({self.max_concurrent}).")

    async def _consumer_worker(self, worker_id: str) -> None:
        """Worker that processes download tasks from the queue"""
        while not self._stop:
            task = None
            try:
                task = await self.queue.get()
                if task is None:
                    self.queue.task_done()
                    break

                # Skip if this task previously failed
                if task.attachment_id in self.failed_downloads:
                    logger.debug(f"Skipping previously failed download: {task.attachment_name}")
                    self.queue.task_done()
                    continue

                # Add retry logic for cancelled downloads
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        download_task = asyncio.create_task(
                            self._process_download(task)
                        )
                        self.active_downloads[task.attachment_id] = download_task

                        success = await download_task
                        if success:
                            self.completed_downloads.add(task.attachment_id)
                            self.consecutive_successes += 1  # increment on success
                            # Try restoring concurrency if we had reduced it
                            self.restore_max_concurrency_if_ready()

                            logger.debug(
                                f"Download completed successfully: {task.attachment_name} - {self.get_status()}"
                            )
                            break
                        else:
                            self.failed_downloads.add(task.attachment_id)
                            logger.debug(
                                f"Download failed: {str(task.file_path)[11:]} {task.attachment_name} - {self.get_status()}"
                            )
                            break

                    except asyncio.CancelledError:
                        # reduce concurrency and reset success count
                        self.reduce_concurrency_to_one()

                        retry_count += 1
                        wait_time = 5 * (2 ** retry_count)
                        admin_urls = format_admin_urls(
                            course_info={
                                'course_id': task.course_id,
                                'course_name': task.course_name,
                                'module_id': task.module_id,
                                'module_name': task.module_name,
                                'lecture_id': task.lecture_id,
                                'lecture_name': task.lecture_name,
                                'attachment_id': task.attachment_id,
                                'attachment_kind': task.attachment_kind
                            },
                            attachment_id=task.attachment_id,
                            attachment_kind=task.attachment_kind,
                            url=task.url
                        )
                        if retry_count < max_retries:
                            logger.warning(
                                f"Download cancelled for {str(task.file_path)[11:]} {task.attachment_name} - "
                                f"Retrying in {wait_time}s (Attempt {retry_count}/{max_retries})"
                            )
                            for url_line in admin_urls.split('\n'):
                                logger.debug(url_line)
                            try:
                                await asyncio.sleep(wait_time)
                            except asyncio.CancelledError:
                                logger.warning("Retry wait interrupted, proceeding with next attempt immediately")
                            continue
                        else:
                            logger.error(
                                f"Download permanently cancelled for {str(task.file_path)[11:]} {task.attachment_name} "
                                f"after {max_retries} attempts"
                            )
                            for url_line in admin_urls.split('\n'):
                                logger.error(url_line)
                            self.failed_downloads.add(task.attachment_id)
                            break

                    except Exception as e:
                        logger.error(f"Error downloading {task.attachment_name}: {e} - {self.get_status()}")
                        self.failed_downloads.add(task.attachment_id)
                        break

                self.queue.task_done()
                status = self.get_status()
                logger.debug(f"Task completed - {status}")

                if self.queue.empty() and not self.active_downloads:
                    if self.failed_downloads:
                        logger.error(f"All downloads completed with some failures - {status}")
                    else:
                        logger.info(f"All downloads completed successfully - {status}")

            except asyncio.CancelledError:
                if task:
                    self.queue.task_done()
                break
            except Exception as e:
                if task:
                    self.queue.task_done()
                logger.error(f"Error in consumer {worker_id}: {e} - {self.get_status()}")

    async def _process_download(self, task: DownloadTask) -> bool:
        """Process a single download task"""
        try:
            logger.debug(f"Processing download: {str(task.file_path)}")
            # Get actual file size from server first
            async with aiohttp.ClientSession() as session:
                async with session.head(task.url) as response:
                    if 'Content-Length' in response.headers:
                        task.file_size = int(response.headers['Content-Length'])
                        logger.debug(f"Server reports size {task.file_size:,} bytes for attachment {task.attachment_id}")

            # Now check existing file with correct size
            if os.path.exists(task.file_path):
                file_size = os.path.getsize(task.file_path)
                if task.file_size and file_size == task.file_size:
                    logger.info(f"Skipping attachment {task.attachment_id} - file already exists with correct size")
                    self.completed_downloads.add(task.attachment_id)
                    return True
                elif task.file_size:  # Only log mismatch if we have an expected size
                    logger.warning(f"Size mismatch for attachment {task.attachment_id} - "
                                 f"expected: {task.file_size:,}, actual: {file_size:,}")

            # Actually perform the download
            success = await download_file(
                url=task.url,
                file_path=task.file_path,
                semaphore=self.semaphore,
                course_info=task.to_context_dict(),
                verify=True
            )

            if success:
                self.completed_downloads.add(task.attachment_id)
                return True
            else:
                self.failed_downloads.add(task.attachment_id)
                # Add to failures list for summary
                frontend_domain = os.environ.get("TEACHABLE_FRONTEND_DOMAIN", "your-teachable-domain.com")
                view_lecture_url = f"https://{frontend_domain}/admin-app/courses/{task.course_id}/curriculum/lessons/{task.lecture_id}"
                manual_video_url = None
                if task.attachment_kind == 'video':
                    manual_video_url = f"https://{frontend_domain}/api/v1/attachments/{task.attachment_id}/hotmart_video_download_link"
                
                self.failures.append(DownloadFailure(
                    course_id=task.course_id,
                    course_name=task.course_name or "Unknown",
                    attachment_id=task.attachment_id,
                    filename=task.file_path.name,
                    actual_size=os.path.getsize(task.file_path) if os.path.exists(task.file_path) else None,
                    expected_size=task.file_size,
                    view_lecture_url=view_lecture_url,
                    manual_video_url=manual_video_url,
                    direct_download_url=task.url,
                    error_type="download_failed"
                ))
                return False

        except asyncio.CancelledError:
            # Add failure record for cancelled downloads
            frontend_domain = os.environ.get("TEACHABLE_FRONTEND_DOMAIN", "your-teachable-domain.com")
            view_lecture_url = f"https://{frontend_domain}/admin-app/courses/{task.course_id}/curriculum/lessons/{task.lecture_id}"
            manual_video_url = None
            if task.attachment_kind == 'video':
                manual_video_url = f"https://{frontend_domain}/api/v1/attachments/{task.attachment_id}/hotmart_video_download_link"
            
            self.failures.append(DownloadFailure(
                course_id=task.course_id,
                course_name=task.course_name or "Unknown",
                attachment_id=task.attachment_id,
                filename=task.file_path.name,
                actual_size=os.path.getsize(task.file_path) if os.path.exists(task.file_path) else None,
                expected_size=task.file_size,
                view_lecture_url=view_lecture_url,
                manual_video_url=manual_video_url,
                direct_download_url=task.url,
                error_type="cancelled"
            ))
            raise

    def print_failure_summary(self) -> None:
        """Print a summary of all download failures to console"""
        if not self.failures:
            return

        print("\nDownload Failures Summary:")
        print("=" * 80)
        
        # Group failures by course
        failures_by_course = defaultdict(list)
        for failure in self.failures:
            failures_by_course[(failure.course_id, failure.course_name)].append(failure)
        
        for (course_id, course_name), failures in failures_by_course.items():
            print(f"\nCourse: {course_name} (ID: {course_id})")
            print("-" * 80)
            
            for failure in failures:
                print(f"\nFile: {failure.filename}")
                print(f"Attachment ID: {failure.attachment_id}")
                if failure.actual_size is not None:
                    print(f"Size on disk: {failure.actual_size:,} bytes")
                if failure.expected_size is not None:
                    print(f"Expected size: {failure.expected_size:,} bytes")
                print(f"Error type: {failure.error_type}")
                print("\nRelevant URLs:")
                print(f"  View lecture: {failure.view_lecture_url}")
                if failure.manual_video_url:
                    print(f"  Manual video download: {failure.manual_video_url}")
                print(f"  Direct download: {failure.direct_download_url}")
                print("-" * 40)
        
        print("\n" + "=" * 80)

    async def wait_for_downloads(self) -> None:
        """
        Wait for all queued downloads to complete, including retries.
        Modified to keep waiting while new tasks are spawned.
        """
        while True:
            # Wait for queue to be empty
            queue_empty_task = asyncio.create_task(self.queue.join())
            try:
                await asyncio.wait_for(queue_empty_task, timeout=30)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for queue tasks - {self.get_status()}")
                # If not done, we can reduce concurrency or keep waiting
                continue

            # Check for active downloads
            active_tasks = [t for t in self.active_downloads.values() if not t.done()]
            if active_tasks:
                logger.warning(f"Waiting for {len(active_tasks)} active downloads to finish...")
                # Attempt to gather them with a small timeout
                try:
                    await asyncio.wait_for(asyncio.gather(*active_tasks, return_exceptions=True), timeout=30)
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for active downloads - possibly retry logic. Continuing to wait.")
                continue

            # If we get here, queue is empty and no active tasks remain
            break

        self.active_downloads.clear()
        if self.failed_downloads:
            logger.info(f"Download manager completed with some failures - {self.get_status()}")
        else:
            logger.info(f"Download manager completed successfully - {self.get_status()}")

async def process_course(
    api_client: TeachableAPIClient,
    course_id: int,
    module_id: Optional[int],
    lecture_id: Optional[int],
    output_dir: pathlib.Path,
    valid_types: List[str],
    download_manager: DownloadManager,
    existing_course_name: Optional[str] = None,
    csv_only: bool = False
) -> None:
    """Modified to support csv-only mode"""
    # Initialize download_tasks set at the start
    download_tasks = set()  # Track download tasks for this course
    
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

    # Check for rename only if we have the existing name
    if existing_course_name and existing_course_name != course_name:
        rename_course_directory(output_dir, course_id, existing_course_name, course_name)
        course_dirname = f"{course_id} - {safe_filename(course_name)}"
        course_dir = output_dir / course_dirname

    # Download course cover image if available and not in csv-only mode
    if not csv_only and (image_url := course_data.get("image_url")):
        # Extract extension from URL or default to .jpg
        ext = pathlib.Path(image_url).suffix
        if not ext or ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'  # Default extension if none found or not recognized
            
        cover_filename = f"{course_id} - {safe_filename(course_name)} - Cover{ext}"
        cover_path = course_dir / cover_filename
        
        if not cover_path.exists():
            # Queue the cover image download
            download_task = DownloadTask(
                url=image_url,
                file_path=cover_path,
                course_id=course_id,
                lecture_id=0,  # Not applicable for cover image
                attachment_id=0,  # Not applicable for cover image
                attachment_name="Course Cover",
                attachment_kind="image",
                file_size=None,
                course_name=course_name,
                module_id=None,
                module_name=None,
                lecture_name=None
            )
            task = asyncio.create_task(download_manager.add_task(download_task))
            download_tasks.add(task)
            logger.info(f"Queued download of course cover image: {cover_filename}")

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

    async def queue_download(attachment: Dict[str, Any], 
                           file_path: pathlib.Path,
                           lecture: Dict[str, Any]) -> None:
        """Helper to queue a download and track its task"""
        if url := attachment.get("url"):
            # First check if we need to rename any existing files
            await rename_if_needed(
                file_path.parent,
                file_path.name,
                str(attachment["id"])
            )
            
            download_task = DownloadTask(
                url=url,
                file_path=file_path,
                course_id=course_id,
                lecture_id=lecture["id"],
                attachment_id=attachment["id"],
                attachment_name=attachment.get("name", ""),
                attachment_kind=attachment.get("kind", ""),  # Include attachment type
                file_size=attachment.get("media_duration"),
                course_name=course_name,
                module_id=lecture["section_id"],
                module_name=lecture["name"],
                lecture_name=lecture["name"]
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

                # Process attachments and queue downloads only if not in csv-only mode
                for attachment in lecture["attachments"]:
                    attachment_kind = attachment.get("kind")
                    
                    # Handle text and quiz content directly from the API response
                    if not csv_only and attachment_kind in ["text", "code_embed", "code_display"] and attachment.get("text"):
                        filename = f"M{section_position:02d}_L{lecture['position']:02d}_A{attachment['position']:02d}_{attachment['id']}_Text.html"
                        file_path = course_dir / filename
                        
                        # Check for renames before saving
                        await rename_if_needed(
                            file_path.parent,
                            file_path.name,
                            str(attachment["id"])
                        )
                        
                        # Save the HTML content
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(attachment["text"])
                        logger.info(f"      Saved text content to {filename}")
                    
                    # Handle quiz content
                    elif not csv_only and attachment_kind == "quiz" and attachment.get("quiz"):
                        filename = f"M{section_position:02d}_L{lecture['position']:02d}_A{attachment['position']:02d}_{attachment['id']}_Quiz.json"
                        file_path = course_dir / filename
                        
                        # Check for renames before saving
                        await rename_if_needed(
                            file_path.parent,
                            file_path.name,
                            str(attachment["id"])
                        )
                        
                        # Save the quiz content
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(attachment["quiz"], f, indent=2)
                        logger.info(f"      Saved quiz content to {filename}")

                    # Continue with regular attachment processing
                    if not attachment_kind or attachment_kind not in valid_types:
                        continue

                    attachment_name = normalize_utf_filename(attachment.get("name") or "")
                    filename = f"M{section_position:02d}_L{lecture['position']:02d}_A{attachment['position']:02d}_{attachment['id']}_{safe_filename(attachment_name)}"
                    file_path = course_dir / filename

                    # Queue download only if not in csv-only mode
                    if not csv_only:
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

        # Wait for downloads only if not in csv-only mode
        if not csv_only and download_tasks:
            logger.info(f"Waiting for {len(download_tasks)} downloads to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*download_tasks, return_exceptions=True),
                    timeout=30
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for downloads to complete; proceeding.")
            logger.info("All downloads completed for this course")

    except Exception as e:
        logger.error(f"Error processing course {course_id}: {e}")
        raise

async def process_courses(
    api_client: TeachableAPIClient,
    course_ids: List[int],
    args,
    download_manager: DownloadManager,
    course_names: Dict[int, str]
) -> None:
    """Process multiple courses with shared configuration"""
    # Get optional args with defaults
    module_id = getattr(args, 'module_id', None)
    lecture_id = getattr(args, 'lecture_id', None)
    
    for course_id in course_ids:
        await process_course(
            api_client=api_client,
            course_id=course_id,
            module_id=module_id,
            lecture_id=lecture_id,
            output_dir=args.output,
            valid_types=args.types,
            download_manager=download_manager,
            existing_course_name=course_names.get(course_id),
            csv_only=args.csv_only
        )
    
    # Only wait for downloads if not in csv-only mode
    if not args.csv_only:
        await download_manager.wait_for_downloads()

async def get_user_details(api_client: TeachableAPIClient, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch details for a specific user and enrich the data with additional fields.
    
    Args:
        api_client: The API client instance
        user_id: The ID of the user to fetch
    
    Returns:
        Optional[Dict[str, Any]]: Enriched user data or None if fetch fails
    """
    try:
        user_data = await api_client.get(f"/users/{user_id}")
        if not user_data:
            logger.debug(f"API returned no data for user {user_id}")
            return None
            
        # Debug log the raw response
        logger.debug(f"Raw API response for user {user_id}: {json.dumps(user_data)[:200]}...")
            
        # The API returns the user object directly, not wrapped in a "user" key
        user = user_data
        if not user:
            logger.debug(f"No user data found in response for user {user_id}")
            return None
            
        # Use UTC directly since we're on Python 3.12
        user["date_added"] = datetime.now(UTC).isoformat()
        
        # Add admin_url to each course
        frontend_domain = os.environ.get("TEACHABLE_FRONTEND_DOMAIN")
        if frontend_domain and "courses" in user:
            for course in user["courses"]:
                course["admin_url"] = (
                    f"https://{frontend_domain}/admin/users/{user_id}/reports"
                    f"?course_id={course['course_id']}&page=1&limit=10"
                )
        
        return user
        
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        logger.debug(f"Error details for user {user_id}: {traceback.format_exc()}")
        return None

async def process_user(
    api_client: TeachableAPIClient,
    user_id: int,
    users_file: pathlib.Path,
    existing_users: Dict[int, datetime]
) -> None:
    """
    Process a single user: fetch details and save to NDJSON if needed.
    """
    try:
        # Check if user exists and is recent enough
        if user_id in existing_users:
            date_added = existing_users[user_id]
            if datetime.now(UTC) - date_added < timedelta(days=7):
                logger.debug(f"Skipping user {user_id} - data is less than 7 days old")
                return

        # Fetch and enrich user details
        user_data = await get_user_details(api_client, user_id)
        if not user_data:
            logger.warning(f"No data returned for user {user_id}")
            return

        # Append to NDJSON file
        try:
            with open(users_file, "a", encoding="utf-8") as f:
                json_line = json.dumps(user_data)
                f.write(json_line + "\n")
                f.flush()  # Ensure write is committed to disk
                os.fsync(f.fileno())  # Force write to disk
                logger.info(f"Saved user {user_id} ({user_data.get('name', 'Unknown')}) to {users_file}")
        except Exception as e:
            logger.error(f"Error saving user {user_id} to NDJSON: {str(e)}")
            raise  # Re-raise to be caught by outer try
            
    except Exception as e:
        logger.error(f"Failed to process user {user_id}: {str(e)}")
        logger.debug(f"Error details for user {user_id}: {traceback.format_exc()}")
        raise  # Re-raise to be caught by semaphore wrapper

def load_existing_users(users_file: pathlib.Path) -> Dict[int, datetime]:
    """
    Load existing users from NDJSON file with their date_added.
    """
    existing_users = {}
    if not users_file.exists():
        return existing_users

    try:
        with open(users_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    user_data = json.loads(line)
                    user_id = user_data.get("id")
                    date_added_str = user_data.get("date_added")
                    if user_id and date_added_str:
                        # Parse ISO format date with timezone
                        date_added = datetime.fromisoformat(date_added_str)
                        # Ensure UTC
                        if date_added.tzinfo is None:
                            date_added = date_added.replace(tzinfo=timezone.UTC)
                        existing_users[user_id] = date_added
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON at line {line_num}: {str(e)}")
                    continue
                except ValueError as e:
                    logger.warning(f"Invalid date format at line {line_num}: {str(e)}")
                    continue
    except Exception as e:
        logger.error(f"Error loading existing users: {str(e)}")
        logger.debug(f"Error details: {traceback.format_exc()}")

    return existing_users

async def get_all_users(api_client: TeachableAPIClient, output_dir: pathlib.Path) -> None:
    """
    Fetch all users and save them to NDJSON file.
    Uses concurrent processing to fetch user details while getting next pages.
    
    Args:
        api_client: The API client instance
        output_dir: Directory to save the users file
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    users_file = output_dir / "users.ndjson"
    
    # Load existing users
    existing_users = load_existing_users(users_file)
    logger.info(f"Loaded {len(existing_users)} existing users from {users_file}")

    # Create semaphores for API calls
    page_semaphore = asyncio.Semaphore(1)  # One page at a time
    user_semaphore = asyncio.Semaphore(API_MAX_CONCURRENT_CALLS - 1)  # Leave one slot for page fetching
    
    page = 1
    per_page = 100
    active_tasks: Set[asyncio.Task] = set()
    total_processed = 0
    
    while True:
        try:
            async with page_semaphore:
                logger.info(f"Fetching {per_page} users from page {page}...")
                data = await api_client.get("/users", params={"page": page, "per": per_page})
                
                if not data or "users" not in data:
                    break
                    
                users = data["users"]
                if not users:
                    break

                logger.info(f"Processing {len(users)} users from page {page}")
                
                # Start processing users from this page concurrently
                for user in users:
                    user_id = user.get("id")
                    if user_id:
                        # Create task with user semaphore
                        task = asyncio.create_task(
                            process_user_with_semaphore(
                                api_client, 
                                user_id, 
                                users_file, 
                                existing_users, 
                                user_semaphore
                            )
                        )
                        active_tasks.add(task)
                        task.add_done_callback(active_tasks.discard)
                        total_processed += 1

                # Check if we've processed all pages
                meta = data.get("meta", {})
                total_pages = meta.get("number_of_pages", 1)
                if page >= total_pages:
                    break
                
                # Stop after 2 pages (for testing)
                # if page >= 2:
                #     break
                    
                page += 1
                
                # Wait for some tasks to complete if we have too many
                if len(active_tasks) >= API_MAX_CONCURRENT_CALLS * 2:
                    completed, pending = await asyncio.wait(
                        active_tasks, 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    logger.info(
                        f"Completed batch of {len(completed)} user fetches, "
                        f"{len(pending)} pending, "
                        f"total processed: {total_processed}"
                    )
                
        except Exception as e:
            logger.error(f"Error processing page {page}: {e}")
            break

    # Wait for all remaining user processing to complete
    if active_tasks:
        logger.info(f"Waiting for {len(active_tasks)} remaining user fetches to complete...")
        try:
            await asyncio.gather(*active_tasks)
        except Exception as e:
            logger.error(f"Error while waiting for remaining tasks: {e}")

    # Verify file was created and has content
    if users_file.exists():
        try:
            with open(users_file, "r") as f:
                line_count = sum(1 for _ in f)
            logger.info(f"Completed fetching all users. Saved {line_count} users to {users_file}")
        except Exception as e:
            logger.error(f"Error counting lines in output file: {e}")
    else:
        logger.error(f"No output file was created at {users_file}")

async def process_user_with_semaphore(
    api_client: TeachableAPIClient,
    user_id: int,
    users_file: pathlib.Path,
    existing_users: Dict[int, datetime],
    semaphore: asyncio.Semaphore
) -> None:
    """
    Wrapper for process_user that uses a semaphore for concurrency control.
    """
    async with semaphore:
        await process_user(api_client, user_id, users_file, existing_users)

async def main() -> None:
    """Main function with the new get-users command"""
    import argparse
    parser = argparse.ArgumentParser(description="Manage and download course data from Teachable.")
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")

    # Fetch-all command
    parser_fetch_all = subparsers.add_parser("fetch-all", help="Fetch and save all courses")
    parser_fetch_all.add_argument("--output", "-o", type=pathlib.Path, default=".", help="Directory to save the all courses CSV")
    parser_fetch_all.add_argument("--csv-only", action="store_true", help="Only generate CSV file, skip downloading files")

    # Process command
    parser_process = subparsers.add_parser("process", help="Process and download data for specific courses")
    parser_process.add_argument("course_ids", metavar="course_id", type=int, nargs="+", help="One or more Course IDs to process")
    parser_process.add_argument("--module_id", type=int, default=None, help="Optional module ID to filter processing")
    parser_process.add_argument("--lecture_id", type=int, default=None, help="Optional lecture ID to filter processing")
    parser_process.add_argument("--output", "-o", type=pathlib.Path, default=".", help="Directory to save course data")
    parser_process.add_argument("--csv-only", action="store_true", help="Only generate course_data.csv files, skip downloading files")

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

    # Add new get-users command
    parser_get_users = subparsers.add_parser(
        "get-users",
        help="Fetch all users and save to NDJSON file"
    )
    parser_get_users.add_argument(
        "--output", 
        "-o", 
        type=pathlib.Path,
        default=".",
        help="Directory to save the users NDJSON file"
    )

    args = parser.parse_args()

    # Convert 'pdf' to 'pdf_embed'
    if "pdf" in args.types:
        args.types.append("pdf_embed")
        args.types.remove("pdf")

    download_manager = DownloadManager(MAX_CONCURRENT_DOWNLOADS)
    
    try:
        # Start the download manager consumers only if we're not in csv-only mode
        if not (hasattr(args, 'csv_only') and args.csv_only):
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
                    # Fetch and save all courses
                    all_courses = await api_client.get_all_courses()
                    file_path = args.output / "all_courses_data.csv"
                    save_data_to_csv(all_courses, file_path)
                    logger.info(f"All courses saved to {file_path}")

                    if not args.csv_only:
                        # Process all courses if not csv-only
                        course_names = {c["id"]: c["name"] for c in all_courses}
                        course_ids = [c["id"] for c in all_courses]
                        await process_courses(
                            api_client=api_client,
                            course_ids=course_ids,
                            args=args,
                            download_manager=download_manager,
                            course_names=course_names
                        )
                except asyncio.CancelledError:
                    logger.info("Operation interrupted. Progress saved.")
                    if not args.csv_only:
                        logger.info("Waiting for active downloads to complete...")
                        download_manager.stop()
                    return
            elif args.operation == "process":
                try:
                    # Fetch all courses once at the beginning
                    logger.info("Fetching all courses...")
                    all_courses = await api_client.get_all_courses()
                    file_path = args.output / "all_courses_data.csv"
                    save_data_to_csv(all_courses, file_path)
                    logger.info(f"All courses saved to {file_path}")
                                        
                    course_names = {c["id"]: c["name"] for c in all_courses}

                    await process_courses(
                        api_client=api_client,
                        course_ids=args.course_ids,
                        args=args,
                        download_manager=download_manager,
                        course_names=course_names
                    )
                except asyncio.CancelledError:
                    logger.info("Processing interrupted.")
                    if not args.csv_only:
                        logger.info("Waiting for active downloads to complete...")
                        download_manager.stop()
                    return
            elif args.operation == "get-users":
                await get_all_users(api_client, args.output)

        logger.info("All tasks completed successfully.")
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down gracefully...")
        if not (hasattr(args, 'csv_only') and args.csv_only):
            download_manager.stop()
    finally:
        if not (hasattr(args, 'csv_only') and args.csv_only):
            await download_manager.wait_for_downloads()
            if download_manager.failures:
                download_manager.print_failure_summary()
        logger.info("Cleanup complete.")

# Updated entry point with proper signal handling for Windows
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down gracefully...")

async def handle_gateway_timeout(response: aiohttp.ClientResponse, retry_count: int = 3) -> None:
    """
    Handle 504 Gateway Timeout errors by implementing a waiting period.
    
    Args:
        response: The response object from the failed request
        retry_count: Number of retries before giving up (default: 3)
    """
    if response.status == 504:
        wait_time = 300  # 5 minutes in seconds
        logger.warning(f"Received 504 Gateway Timeout. Waiting {wait_time} seconds before retry. Attempts remaining: {retry_count}")
        await asyncio.sleep(wait_time)
        return True
    return False

async def get(url: str, headers: dict = None, retry_count: int = 3) -> dict:
    """
    Make a GET request to the API with retry logic for various error conditions.
    
    Args:
        url: The URL to make the request to
        headers: Request headers
        retry_count: Number of retries before giving up
    
    Returns:
        dict: The JSON response from the API
    """
    async with aiohttp.ClientSession() as session:
        while retry_count > 0:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    # Handle rate limiting
                    if response.status == 429:
                        await handle_rate_limit(response)
                        retry_count -= 1
                        continue
                        
                    # Handle gateway timeout
                    if response.status == 504:
                        should_retry = await handle_gateway_timeout(response, retry_count)
                        if should_retry:
                            retry_count -= 1
                            continue
                    
                    # Log other errors
                    error_text = await response.text()
                    logger.error(f"Error response for URL {url}: {response.status} - {error_text}")
                    raise ApiError(f"API request failed with status {response.status}")
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if retry_count <= 1:
                    logger.error(f"Failed to fetch {url} after all retries: {str(e)}")
                    raise
                logger.warning(f"Request failed, retrying... ({retry_count-1} attempts remaining): {str(e)}")
                retry_count -= 1
                await asyncio.sleep(5)  # Short delay before retry
                
    raise ApiError("Maximum retries exceeded")