#!/usr/bin/env python3
"""
Script to convert users NDJSON data to a mentor tools CSV.

Requirements:
- The NDJSON file is provided with the -i/--input parameter.
- Only users with role "student" and enrolled in a specific course (via --course_id) are processed.
- The CSV contains: email, first_name, last_name (filled with the student's name), 
  courses (filled with the provided mentor tool courses string), order_billing_type ("single")
  and purchase_date (formatted as "YYYY-MM-DD HH:MM:SS").
- The output CSV is saved as "YYYY-MM-DD <course_id> mentor_tools.csv" in the same directory 
  as the input file.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger


def parse_timestamp(timestamp: str) -> str:
    """
    Converts an ISO timestamp (with a potential trailing 'Z') to 'YYYY-MM-DD HH:MM:SS' format.
    
    Args:
        timestamp: Enrollment timestamp from the NDJSON data.
    
    Returns:
        A formatted timestamp string.
    """
    # Replace 'Z' with '+00:00' to make it ISO 8601 compliant if necessary.
    if timestamp.endswith("Z"):
        timestamp = timestamp.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error parsing timestamp '{timestamp}': {e}")
        return ""


def load_users(input_file: Path) -> list[dict]:
    """
    Load users from the provided NDJSON file.
    
    Args:
        input_file: Path to the NDJSON file.
        
    Returns:
        A list of user dictionaries.
    """
    users = []
    with input_file.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                user = json.loads(line)
                users.append(user)
            except json.JSONDecodeError as e:
                logger.error(f"Skipping invalid JSON on line {line_num}: {e}")
    return users


def filter_students(users: list[dict], course_id: int) -> list[dict]:
    """
    Filters for students with role "student" that are enrolled in the provided course_id.
    
    For each matching student, extract:
      - email
      - name (splitted into first_name and last_name if applicable)
      - enrollment date (from the course enrollment data)
    
    Args:
        users: List of user dictionaries from the NDJSON file.
        course_id: Course ID to filter for.
        
    Returns:
        A list of records ready for CSV conversion.
    """
    filtered_records = []
    for user in users:
        if user.get("role") != "student":
            continue

        courses = user.get("courses", [])
        for course in courses:
            if course.get("course_id") == course_id:
                full_name = user.get("name", "")
                if full_name and len(full_name.split()) == 2:
                    first_name, last_name = full_name.split()
                else:
                    first_name, last_name = "", full_name

                record = {
                    "email": user.get("email", ""),
                    "first_name": first_name,
                    "last_name": last_name,
                    "courses": "",  # To be set later from the mentor_tool_courses parameter.
                    "order_billing_type": "single",
                    "purchase_date": parse_timestamp(course.get("enrolled_at", ""))
                }
                filtered_records.append(record)
                break  # Only take one matching enrollment per student.
    return filtered_records


def write_csv(records: list[dict], output_path: Path, mentor_tool_courses: str) -> None:
    """
    Write the filtered records to a CSV file using a semicolon as the delimiter.
    
    The CSV header is:
        email;first_name;last_name;courses;order_billing_type;purchase_date
    
    Args:
        records: List of processed records.
        output_path: Path to the output CSV file.
        mentor_tool_courses: Value to populate in the CSV 'courses' field.
    """
    # Set the courses field for each record.
    for rec in records:
        rec["courses"] = mentor_tool_courses

    headers = [
        "email",
        "first_name",
        "last_name",
        "courses",
        "order_billing_type",
        "purchase_date",
    ]
    
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=headers,
            delimiter=";",
            quotechar='"',
            quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"CSV file saved at: {output_path}")


def filter_admin_url_users(users: list[dict], course_id: int, admin_url_start_date: str) -> list[dict]:
    """
    Filters for users with role "student" for the given course_id where their enrolled_at date 
    is past the given start date.
 
    Args:
        users: List of user dictionaries from the NDJSON file.
        course_id: Course ID to filter for.
        admin_url_start_date: A date string in "YYYY-MM-DD" format.
 
    Returns:
        A list of records with keys: name, email, admin_url.
    """
    try:
        # Create timezone-aware datetime at midnight UTC using timezone instead of UTC
        start_date = datetime.strptime(admin_url_start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except Exception as e:
        logger.error(f"Invalid date format for admin-url-start-date '{admin_url_start_date}': {e}")
        return []

    admin_records = []
    for user in users:
        if user.get("role") != "student":
            continue
        
        courses = user.get("courses", [])
        for course in courses:
            if course.get("course_id") == course_id:
                enrolled_at_str = course.get("enrolled_at", "")
                if not enrolled_at_str:
                    continue
                try:
                    # Parse the ISO timestamp and ensure it's timezone-aware
                    dt = datetime.fromisoformat(enrolled_at_str.replace("Z", "+00:00"))
                except Exception as e:
                    logger.error(f"Error parsing enrolled_at timestamp '{enrolled_at_str}': {e}")
                    continue
                
                if dt >= start_date:
                    # Get the admin_url from the course-specific data
                    admin_url = course.get("admin_url", "")
                    if not admin_url:
                        continue
                        
                    record = {
                        "name": user.get("name", ""),
                        "email": user.get("email", ""),
                        "admin_url": admin_url
                    }
                    admin_records.append(record)
                    break  # Only take one matching enrollment per student
    return admin_records


def print_admin_urls(records: list[dict]) -> None:
    """
    Print admin URL records to stdout in a formatted way.
 
    Args:
        records: List of records with admin URL data.
    """
    if not records:
        logger.info("No matching admin URL records found for the given start date.")
        return

    print("\nAdmin URLs for enrolled students:")
    print("-" * 80)
    for record in records:
        print(f"Name: {record['name']}")
        print(f"Email: {record['email']}")
        print(f"Admin URL: {record['admin_url']}")
        print("-" * 80)


def main() -> None:
    """Main entry point for processing the NDJSON file and exporting data."""
    parser = argparse.ArgumentParser(
        description="Convert a users NDJSON backup to a mentor tools CSV for a given course."
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Path to the directory containing the users.ndjson file."
    )
    parser.add_argument(
        "-c", "--course_id",
        type=int,
        required=True,
        help="Course ID to filter only students that are enrolled in the course."
    )
    parser.add_argument(
        "-m", "--mentor_tool_courses",
        required=False,  # Changed to False since it's only needed for CSV output
        help="String to use for the 'courses' field in the CSV output."
    )
    parser.add_argument(
        "--admin-url-start-date",
        required=False,
        help="Optional. Only process users enrolled after this date (YYYY-MM-DD) for admin URL output."
    )

    args = parser.parse_args()

    # Verify that the input directory exists and users.ndjson is present.
    if not args.input.exists() or not args.input.is_dir():
        logger.error(f"Input path is not a valid directory: {args.input}")
        sys.exit(1)

    ndjson_file = args.input / "users.ndjson"
    if not ndjson_file.exists():
        logger.error(f"users.ndjson not found in the provided directory: {args.input}")
        sys.exit(1)

    users = load_users(ndjson_file)
    if not users:
        logger.error("No users could be loaded from the input file.")
        sys.exit(1)

    # If admin URL start date is provided, only process admin URLs and exit
    if args.admin_url_start_date:
        admin_records = filter_admin_url_users(users, args.course_id, args.admin_url_start_date)
        print_admin_urls(admin_records)
        sys.exit(0)

    # Otherwise process the mentor tools CSV
    # Check if mentor_tool_courses is provided for CSV generation
    if not args.mentor_tool_courses:
        logger.error("--mentor_tool_courses is required when generating CSV output")
        sys.exit(1)

    filtered_students = filter_students(users, args.course_id)
    logger.info(f"Found {len(filtered_students)} student(s) enrolled in course ID {args.course_id}.")

    if not filtered_students:
        logger.info("No matching student records found. Exiting.")
        sys.exit(0)

    # Construct the output CSV filename using the current date and course_id.
    current_date = datetime.now().strftime("%Y-%m-%d")
    output_filename = f"{current_date} {args.course_id} mentor_tools.csv"
    output_path = ndjson_file.parent / output_filename

    write_csv(filtered_students, output_path, args.mentor_tool_courses)


if __name__ == "__main__":
    main() 