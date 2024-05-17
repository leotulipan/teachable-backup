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
API_KEY = os.getenv("API_KEY")
HEADERS = {
    "accept": "application/json",
    "apiKey": API_KEY
}

BASE_URL = "https://developers.teachable.com/v1"

def safe_filename(filename):

    if not filename:
        return ""

    # Remove unsafe characters
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Ensure filename is not longer than 30 characters
    return filename[:30]


def handle_rate_limit(url, headers):
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


def fetch_course_id(course_name):
    
    url = f"{BASE_URL}/courses?name={course_name}"
    response = handle_rate_limit(url, HEADERS)
    data = response.json()
    if data.get("courses"):
        return data["courses"][0]["id"]
    return None
def fetch_courses():
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

def save_course_list_to_csv(courses):

    # Dynamically generate fieldnames from courses
    fieldnames = courses[0].keys()

    with open('course_list.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(courses)


def get_course_details(course_id):
    url = f"{BASE_URL}/courses/{course_id}"
    response = handle_rate_limit(url, HEADERS)
    return response.json()


def get_lecture_details(course_id, lecture_id):
    url = f"{BASE_URL}/courses/{course_id}/lectures/{lecture_id}"
    response = handle_rate_limit(url, HEADERS)
    return response.json()


def save_text_attachment_as_html(attachment_id, text_content):
    with open(f"{attachment_id}.html", "w", encoding="utf-8") as file:
        file.write(text_content)


def save_to_csv(rows):
    with open('course_data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            "course_id", 
            "course_name", 
            "lecture_section_id", 
            "lecture_section_position",
            "lecture_section_name", 
            "lecture_id", 
            "lecture_position", 
            "lecture_name", 
            "lecture_is_published", 
            "lecture_attachment_id",
            "lecture_attachment_position",
            "lecture_attachment_name", 
            "lecture_attachment_kind", 
            "lecture_attachmenturl"
        ])
        writer.writerows(rows)


def get_course_csv(course_name, section_name):
    # course_name = "Fachausbildung zum Coach für Ketogene Ernährung"
    # section_name = "" # "Modul 3"
    course_id = fetch_course_id(course_name)
    print(f"Fetching details for course ID: {course_id}")
    course_details = get_course_details(course_id)

    rows = []
    for section in course_details["course"]["lecture_sections"]:
        #  The condition not section_name will be True if section_name is empty (or None), and section['name'] == section_name will be True if the names match. The or operator ensures that the code inside the if block will execute if either of the conditions is True.
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

                    row = [
                        course_id,
                        course_details["course"]["name"],
                        section["id"],
                        section["position"],
                        section["name"],
                        lecture_details["lecture"]["id"],
                        lecture_details["lecture"]["position"],
                        lecture_details["lecture"]["name"],
                        lecture_details["lecture"]["is_published"],
                        attachment["id"],
                        attachment["position"],
                        attachment["name"],
                        attachment["kind"],
                        attachment["url"]
                    ]
                    rows.append(row)
        else:
            print(f"Skipping section: {section['name']}")
            
    save_to_csv(rows)

def download_attachments(types, section=None):
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
        reader = csv.DictReader(file)
        for row in reader:
            # Check if section is set and matches
            if section and row['lecture_section_name'] != section:
                continue
            
            # Check if attachment kind is in valid types
            if row['lecture_attachment_kind'] not in valid_types:
                continue
            

            # Download and save the file
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    response = requests.get(row['lecture_attachmenturl'], stream=True)
                    response.raise_for_status()  # Raise error on failed requests

                    filename = f"{row['lecture_section_position'].zfill(2)}_{row['lecture_position'].zfill(2)}_{str(int(row['lecture_attachment_position'])).zfill(2)}_{row['lecture_attachment_id']}_{row['lecture_attachment_name']}"

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



def main():
    parser = argparse.ArgumentParser(description="Fetch course details from Teachable API.")
    
    parser.add_argument('--course', default="Fachausbildung zum Coach für Ketogene Ernährung", help="Name of the course.")
    parser.add_argument('--section', default=None, help="Name of the section.")
    parser.add_argument('--download', action='store_true', help="Flag to download attachments.")
    parser.add_argument('--types', choices=['pdf', 'file', 'image', 'video'], nargs='*', default=['pdf', 'file', 'image', 'video'], help="Types of attachments to download.")

    
    args = parser.parse_args()
    
    if args.download:
        download_attachments(args.types, args.section)
    elif not args.course and not args.section:
        # if no argument is passed, fetch courses and save to csv
        courses = fetch_courses()
        save_course_list_to_csv(courses)
        print("Course list saved to course_list.csv")
        # print the first 5 courses
        for course in courses[:5]:
            print(course)
    else:
        get_course_csv(args.course, args.section)


if __name__ == "__main__":
    main()
