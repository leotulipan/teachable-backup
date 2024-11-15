# https://chat.openai.com/c/3ed42491-1ef9-4aea-ad37-32ff55da547d
# api playground https://docs.teachable.com/reference/showlecture
import requests
import csv
from dotenv import load_dotenv
import os
import sys
import time
import re
import argparse

MAX_RETRIES = 5  # maximum number of retries
DELAY_FACTOR = 3  # delay multiplier
INITIAL_DELAY = 30  # initial delay in seconds

# Change the current working directory to the directory of the script
# script_dir = os.path.dirname(os.path.abspath(__file__))
# os.chdir(script_dir)

load_dotenv()
API_KEY = os.getenv("TEACHABLE_API_KEY")
HEADERS = {
    "accept": "application/json",
    "apiKey": API_KEY
}

BASE_URL = "https://developers.teachable.com/v1"

def safe_filename(filename: str) -> str:
    """
    Sanitize a filename by removing unsafe characters and enforcing length limits.

    Args:
        filename (str): The original filename to sanitize

    Returns:
        str: A sanitized filename that is safe for file system operations, 
             truncated to 30 characters
    """

    if not filename:
        return ""

    # Remove unsafe characters
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # no commas
    filename = filename.replace(',', '')
    
    # _-_ to -
    filename = filename.replace('_-_', '-')
    
    # Ensure filename is not longer than 30 characters
    return filename[:30]

def safe_dirname(filename: str) -> str:
    """
    Sanitize a directory name by removing unsafe characters and enforcing length limits.

    Args:
        filename (str): The original directory name to sanitize

    Returns:
        str: A sanitized directory name that is safe for file system operations,
             truncated to 255 characters
    """

    # Remove unsafe characters
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # no commas
    filename = filename.replace(',', '')
    
    # _-_ to -
    filename = filename.replace('_-_', '-')
    
    # Ensure filename is not longer than 255 characters
    return filename[:255]

def get_course_name(course_id: int) -> str:
    """
    Fetch the name of a course using its ID.

    Args:
        course_id (int): The ID of the course to look up

    Returns:
        str: The name of the course
    """
    url = f"{BASE_URL}/courses/{course_id}"
    response = handle_rate_limit(url, HEADERS)
    data = response.json()
    return data["course"]["name"]

def handle_rate_limit(url: str, headers: dict) -> requests.Response:
    """
    Make an API request with automatic rate limit handling.

    Args:
        url (str): The API endpoint URL
        headers (dict): Request headers including API key

    Returns:
        requests.Response: The API response object after successful request
    """
    while True:
        response = requests.get(url, headers=headers)
        
        # If rate limit is not reached, break the loop
        if response.status_code != 429:
            break
        
        # If rate limit is reached, get the reset time from headers and wait
        try:
            reset_time = int(response.headers.get("RateLimit-Reset", 0))
            print(f"Rate limit reached. Retrying in {reset_time} seconds...")
            time.sleep(reset_time)
        except ValueError:
            print("Rate limit reached, but reset time is not provided. Retrying in 20 seconds...")
            time.sleep(20)
            
    return response

def fetch_course_id(course_name: str) -> int | None:
    """
    Fetch the course ID for a given course name.

    Args:
        course_name (str): The name of the course to look up

    Returns:
        int | None: The course ID if found, None otherwise
    """
    url = f"{BASE_URL}/courses?name={course_name}"
    response = handle_rate_limit(url, HEADERS)
    data = response.json()
    if data.get("courses"):
        return data["courses"][0]["id"]
    return None

def fetch_courses() -> list[dict]:
    """
    Fetch all available courses from the Teachable platform.

    Returns:
        list[dict]: List of course dictionaries containing:
            - id (int): Course ID
            - name (str): Course name
            - heading (str): Course heading
            - is_published (bool): Publication status
    """
    courses = []
    page = 1
    per_page = 20 # that is the max
    
    while True:
        url = f"{BASE_URL}/courses?page={page}&per={per_page}"
        response = handle_rate_limit(url, HEADERS)
        data = response.json()
        
        for course in data["courses"]:
            courses.append({
                "id": course["id"],
                "name": course["name"],
                "heading": course["heading"],
                "is_published": course["is_published"]
            })
        
        if data["meta"]["number_of_pages"] <= page:
            break
        
        page += 1
    
    return courses

def save_course_list_to_csv(courses: list[dict]) -> None:
    """
    Save the list of courses to a CSV file.

    Args:
        courses (list[dict]): List of course dictionaries to save
    """

    # Dynamically generate fieldnames from courses
    fieldnames = courses[0].keys()

    with open("all_courses_data.csv", 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writeheader()
        writer.writerows(courses)

def get_course_details(course_id: int) -> dict:
    """
    Fetch detailed information about a specific course.

    Args:
        course_id (int): The ID of the course

    Returns:
        dict: Detailed course information including sections and lectures
    """
    url = f"{BASE_URL}/courses/{course_id}"
    response = handle_rate_limit(url, HEADERS)
    return response.json()

def get_lecture_details(course_id: int, lecture_id: int) -> dict:
    """
    Fetch detailed information about a specific lecture.

    Args:
        course_id (int): The ID of the course containing the lecture
        lecture_id (int): The ID of the lecture

    Returns:
        dict: Detailed lecture information including attachments
    """
    url = f"{BASE_URL}/courses/{course_id}/lectures/{lecture_id}"
    response = handle_rate_limit(url, HEADERS)
    return response.json()

def save_text_attachment_as_html(attachment_id: str, text_content: str) -> None:
    """
    Save a text attachment as an HTML file.

    Args:
        attachment_id (str): Identifier for the attachment
        text_content (str): The text content to save as HTML
    """
    with open(f"{attachment_id}.html", "w", encoding="utf-8") as file:
        file.write(text_content)

def clean_text(text: str) -> str:
    """
    Clean text by handling encoding issues.

    Args:
        text (str): The text to clean

    Returns:
        str: The cleaned text, encoded and decoded using windows-1252
    """
    return text.encode('windows-1252', errors='replace').decode('windows-1252')

def save_to_csv(course_content: list[dict]) -> None:
    """
    Save course content to a CSV file.

    Args:
        course_content (list[dict]): List of dictionaries containing course content
    """
    
    for row in course_content:
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = clean_text(value)

    course_content = sorted(course_content, key=lambda x: (x['section_position'], x['lecture_position']))
    # Dynamically generate fieldnames from courses
    fieldnames = course_content[0].keys()
    
    # previously used windows-1252
    with open(f"course_data.csv", 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)

        writer.writeheader()
        writer.writerows(course_content)
         

    # with open('course_data.csv', 'w', newline='', encoding='utf-8') as file:
    #     writer = csv.writer(file)
    #     writer.writerow([
    #         "course_id", 
    #         "course_name", 
    #         "lecture_section_id", 
    #         "lecture_section_position",
    #         "lecture_section_name", 
    #         "lecture_id", 
    #         "lecture_position", 
    #         "lecture_name", 
    #         "lecture_is_published", 
    #         "lecture_attachment_id",
    #         "lecture_attachment_position",
    #         "lecture_attachment_name", 
    #         "lecture_attachment_kind", 
    #         "lecture_attachmenturl"
    #     ])
    #     writer.writerows(rows)        

def get_course_csv(course_name: str | None = None, course_id: int | None = None, section_name: str | None = None) -> None:
    """
    Generate a CSV file containing course details and save attachments.

    Args:
        course_name (str, optional): Name of the course
        course_id (int, optional): ID of the course
        section_name (str, optional): Name of the section to filter by

    Raises:
        ValueError: If neither course_name nor course_id is provided, or if both are provided
    """
    if not course_name and not course_id:
        raise ValueError("Either course_name or course_id must be provided.")
    
    if course_name and course_id:
        raise ValueError("Only one of course_name or course_id should be provided.")
    
    if course_name:
        course_id = fetch_course_id(course_name)
    
    print(f"Fetching details for course ID: {course_id}")
    course_details = get_course_details(course_id)

    rows = []
    for section in course_details["course"]["lecture_sections"]:
        if not section_name or section['name'] == section_name:
            print(f"Processing section: {section['name']}")
            for lecture in section["lectures"]:
                lecture_details = get_lecture_details(course_id, lecture["id"])
                
                if 'lecture' not in lecture_details:
                    print(f"Error fetching details for lecture ID: {lecture['id']}. Skipping...")
                    print(lecture)
                    print("details")
                    print(lecture_details)
                    continue

                for attachment in lecture_details["lecture"]["attachments"]:
                    if (attachment["kind"] == "text" or attachment["kind"] == "code_embed") and attachment["text"]:
                        save_text_attachment_as_html(
                            f"{str(section['position']).zfill(2)}_{str(lecture['position']).zfill(2)}_{str(attachment['position']).zfill(2)}_{attachment['id']}_{safe_filename(attachment['name'])}", 
                            f"{attachment['text']}"
                        )

                    row = {
                        "course_id": course_id,
                        "course_name": course_details["course"]["name"],
                        "section_id": section["id"],
                        "section_position": section["position"],
                        "section_name": section["name"],
                        "lecture_id": lecture_details["lecture"]["id"],
                        "lecture_position": lecture_details["lecture"]["position"],
                        "lecture_name": lecture_details["lecture"]["name"],
                        "lecture_is_published": lecture_details["lecture"]["is_published"],
                        "attachment_id": attachment["id"],
                        "attachment_position": attachment["position"],
                        "attachment_name": attachment["name"],
                        "attachment_kind": attachment["kind"],
                        "attachment_url": attachment["url"]
                    }
                    rows.append(row)
        else:
            print(f"Skipping section: {section['name']}")
            
    save_to_csv(rows)

def download_attachments(types: list[str], section: str | None = None) -> None:
    """
    Download course attachments based on specified types and section.

    Args:
        types (list[str]): List of attachment types to download ('pdf', 'file', 'image', 'video')
        section (str, optional): Section name to filter downloads by
    """
    # Check if "course_data.csv" exists
    if not os.path.exists("course_data.csv"):
        raise FileNotFoundError("course_data.csv not found in the current working directory.")
    
    # Mapping for argparse types to CSV 'lecture_attachment_kind' values
    type_mapping = {
        'pdf': 'pdf_embed',
        'file': 'file',
        'image': 'image',
        'video': 'video'
    }
    
    # Filter out types based on user input
    valid_types = [type_mapping[t] for t in types]
    
    with open('course_data.csv', 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';', quotechar='"')
        for row in reader:
            # Check if section is set and matches
            if section and row['section_name'] != section:
                continue
            
            # Check if attachment kind is in valid types
            if row['attachment_kind'] not in valid_types:
                continue
            

            # Download and save the file
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    response = requests.get(row['attachment_url'], stream=True)
                    response.raise_for_status()  # Raise error on failed requests

                    filename = f"{row['section_position'].zfill(2)}_{row['lecture_position'].zfill(2)}_{str(int(row['attachment_position'])).zfill(2)}_{row['attachment_id']}_{row['attachment_name']}"

                    # Check if file exists and has size greater than 0
                    if os.path.exists(filename) and os.path.getsize(filename) > 0:
                        print(f"File {filename} already exists and has content. Skipping download.")
                        break  # exit the loop if file is already there and has content
                    
                    print(f"Downloading: {filename}")
                    with open(filename, 'wb') as out_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            out_file.write(chunk)
                    
                    print(f"Downloaded: {filename}")
                    break  # exit the loop if download was successful

                except KeyboardInterrupt:
                    # Handle keyboard interrupt (Ctrl+C)
                    print(f"Interrupted! Deleting partial file: {filename}")
                    os.remove(filename)
                    raise

                except (ConnectionResetError, requests.exceptions.ChunkedEncodingError) as e:
                    retries += 1
                    delay = INITIAL_DELAY * (DELAY_FACTOR ** retries)
                    if retries < MAX_RETRIES:
                        print(f"Error occurred while downloading {filename}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print(f"Failed to download {filename} after {MAX_RETRIES} attempts.")
                        sys.exit(1)

def process_course(course_name: str, section_name: str | None) -> None:
    """
    Process a course by creating a directory and generating course data.

    Args:
        course_name (str): Name of the course to process
        section_name (str, optional): Name of the section to filter by
    """
    course_dirname = safe_dirname(course_name)
    if os.path.exists(os.path.join(course_dirname, 'course_data.csv')):
        print(f"'course_data.csv' already exists in '{course_dirname}'. Skipping...")
        return
    print(f"Fetching course details for: '{course_name}'")
    os.makedirs(course_dirname, exist_ok=True)
    os.chdir(course_dirname)
    get_course_csv(course_name=course_name, section_name=section_name)
    os.chdir('..')

def main() -> None:
    """
    Main function to handle command-line arguments and execute course operations.
    
    Supports the following operations:
    - Fetch and save list of all courses
    - Process specific courses by name or ID
    - Download course attachments
    - Filter operations by section
    """
    parser = argparse.ArgumentParser(description="Fetch course details from Teachable API.")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--course', "-c", default=None, help="Name of the course. e.g. 'Fachausbildung zum Coach für Ketogene Ernährung'")
    group.add_argument('--id', "-i", default=None, help="Alternative: Course ID.")
    parser.add_argument('--section', "-s", default=None, help="Name of the section.")
    parser.add_argument('--download', "-d", action='store_true', help="Flag to download attachments.")
    parser.add_argument('--types', "-t", choices=['pdf', 'file', 'image', 'video'], nargs='*', default=['pdf', 'file', 'image', 'video'], help="Types of attachments to download.")
    parser.add_argument('--all', '-a', action='store_true', help="Flag to fetch details for all courses.")

    
    args = parser.parse_args()
    
    if args.download:
        if args.id:
            args.course = get_course_name(args.id)
        process_course(args.course, args.section)
        # print(f"Fetching course details for: '{args.course}'")
        course_dirname = safe_dirname(args.course)
        # os.makedirs(course_dirname, exist_ok=True)
        os.chdir(course_dirname)
        download_attachments(args.types, args.section)
    elif not args.id and not args.course and not args.section:
        # if no argument is passed, fetch courses and save to csv
        courses = fetch_courses()
        save_course_list_to_csv(courses)
        print("Course list saved to course_list.csv")
        # print the first 5 courses
        for course in courses[:5]:
            print(course)
        if args.all:
            # fetch details for all courses
            for course in courses:
                args.course = get_course_name(course['id'])
                process_course(args.course, args.section)
    else:
        if args.id:
            args.course = get_course_name(args.id)
        process_course(args.course, args.section)


if __name__ == "__main__":
    main()
