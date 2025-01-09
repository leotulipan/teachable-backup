# Download course content from Teachable platform

**Teachable Backup Script**

## Prerequisites

- uv version 0.5 or later. Install instructions [here](https://docs.astral.sh/uv/getting-started/installation/)

```ps1
winget install --id=astral-sh.uv  -e
# update if installed previously
uv self update
# activate venv
uv venv
```

## Folder Structure

workspace_root/
├── .cursorrules
└── teachable/
    ├── .venv/
    ├── README.md
    ├── pyproject.toml
    ├── uv.lock
    └── download_teachable_courses.py

#### **Purpose**

The script is designed to interact with the Teachable API to:

1. **Fetch Course Data:** Retrieve detailed information about a specific course, its sections, lectures, and attachments.
2. **Save Data to CSV:** Organize and store the fetched data into a structured CSV file for backup or analysis purposes.
3. **Download Attachments:** Download various types of attachments associated with lectures, such as PDFs, videos, images, and files, based on user-specified criteria.

#### **Key Features**

1. **Configuration and Setup:**
   - **Environment Variables:** Utilizes the `dotenv` library to securely load the Teachable API key (`API_KEY`) from a `.env` file, ensuring sensitive information is not hard-coded.
   - **Working Directory Management:** Changes the current working directory to the script’s directory to ensure all file operations are relative to the script's location.

2. **API Interaction:**
   - **Base URL:** Interacts with the Teachable API using the base URL `https://developers.teachable.com/v1`.
   - **Headers:** Sets appropriate request headers, including `accept: application/json` and the loaded `apiKey`.
   - **Rate Limiting Handling:** Implements a mechanism to handle API rate limits by detecting `429` responses and waiting for the specified `RateLimit-Reset` time before retrying the request.

3. **Data Retrieval Functions:**
   - **`fetch_course_id(course_name)`:**
     - **Purpose:** Retrieves the unique ID of a course based on its name.
     - **Process:** Sends a GET request to the `/courses` endpoint with the course name as a query parameter.
     - **Error Handling:** Exits the script with an error message if the course is not found or if the request fails.

   - **`get_course_details(course_id)`:**
     - **Purpose:** Fetches detailed information about a specific course, including its sections and lectures.
     - **Process:** Sends a GET request to `/courses/{course_id}`.
     - **Error Handling:** Exits the script with an error message if the request fails.

   - **`fetch_lecture_details(course_id, lecture_id)`:**
     - **Purpose:** Retrieves detailed information about a specific lecture, including its attachments.
     - **Process:** Sends a GET request to `/courses/{course_id}/lectures/{lecture_id}`.
     - **Error Handling:** Prints an error message and skips the lecture if the request fails or the response structure is unexpected.

4. **Data Processing and Saving:**
   - **`safe_filename(filename)`:**
     - **Purpose:** Sanitizes attachment names to create safe and standardized filenames.
     - **Process:** Removes unsafe characters, replaces spaces with underscores, and truncates the filename to 30 characters.
     - **Usage:** Ensures filenames are filesystem-friendly and consistent.

   - **`save_text_attachment_as_html(filename, text_content)`:**
     - **Purpose:** Saves text-based attachments as `.html` files.
     - **Process:** Writes the text content of the attachment to an HTML file with a sanitized filename.

   - **`save_to_csv(rows)`:**
     - **Purpose:** Saves the collected course data into a CSV file named `course_data.csv`.
     - **Process:** Writes headers and rows to the CSV, ensuring proper encoding (`utf-8`) to handle special characters.

   - **`get_course_csv(course_name, section_name=None)`:**
     - **Purpose:** Orchestrates the process of fetching course data and saving it to a CSV file.
     - **Process:**
       - Retrieves the course ID.
       - Fetches detailed course information.
       - Iterates through lecture sections and lectures.
       - Collects attachment details and saves text attachments as HTML files.
       - Compiles all relevant data into rows and saves them to the CSV.

5. **Attachment Downloading:**
   - **`download_attachments(types, section=None)`:**
     - **Purpose:** Downloads attachments based on specified types and, optionally, a specific section.
     - **Process:**
       - Checks for the existence of `course_data.csv`.
       - Maps user-specified types (e.g., `pdf`, `file`, `image`, `video`) to the corresponding `lecture_attachment_kind` values used in the CSV.
       - Iterates through each row in the CSV:
         - Filters rows based on the specified section and attachment types.
         - Constructs a standardized filename for each attachment.
         - Checks if the file already exists and is non-empty to avoid redundant downloads.
         - Implements a retry mechanism with exponential backoff for handling network issues and rate limits.
         - Handles interruptions (`Ctrl+C`) gracefully by deleting partially downloaded files and exiting the script.
         - Downloads the attachment and saves it with the constructed filename.

6. **Error Handling and Resilience:**
   - **API Rate Limits:** Detects when the API rate limit is reached and waits for the reset time before retrying requests.
   - **Network Issues:** Implements retries with exponential backoff for transient network errors such as connection resets, timeouts, and chunked encoding errors.
   - **Graceful Interruptions:** Catches `KeyboardInterrupt` exceptions to handle user-initiated script interruptions, ensuring partial downloads are cleaned up.
   - **File Existence Checks:** Avoids downloading files that already exist and are complete, enhancing efficiency and preventing unnecessary network usage.
   - **Comprehensive Exception Handling:** Differentiates between various types of exceptions to provide specific error messages and handle them appropriately.

7. **Command-Line Interface (CLI):**
   - **Argument Parsing with `argparse`:**
     - **`--course`:** Specifies the name of the course to fetch (default: `"Fachausbildung zum Coach für Ketogene Ernährung"`).
     - **`--section`:** Specifies the name of the section to process (optional).
     - **`--download`:** A flag to trigger the downloading of attachments instead of fetching course data.
     - **`--types`:** Specifies the types of attachments to download (`pdf`, `file`, `image`, `video`). Defaults to all types if not provided.
   - **Usage Patterns:**
     - **Fetch Course Data and Save to CSV:**

       ```bash
       python get_keto_coach_lectures.py
       ```

     - **Fetch Specific Course and Section:**

       ```bash
       python get_keto_coach_lectures.py --course "Your Course Name" --section "Modul 3"
       ```

     - **Download Attachments of Specific Types:**

       ```bash
       python get_keto_coach_lectures.py --download --types image pdf
       ```

     - **Download Attachments from a Specific Section:**

       ```bash
       python get_keto_coach_lectures.py --download --section "Modul 3"
       ```

     - **Combine Type and Section Filters:**

       ```bash
       python get_keto_coach_lectures.py --download --types image pdf --section "Modul 3"
       ```

8. **File Naming Convention:**
   - **Pattern:**

     ```
     {lecture_section_position}_{lecture_position}_{attachment_position}_{attachment_id}_{safe_attachment_name}
     ```

   - **Details:**
     - **`lecture_section_position`**: Zero-padded to two digits (e.g., `01`, `02`).
     - **`lecture_position`**: Zero-padded to two digits.
     - **`attachment_position`**: Zero-padded to two digits.
     - **`attachment_id`**: Unique identifier of the attachment.
     - **`safe_attachment_name`**: Sanitized attachment name, truncated to 30 characters and spaces replaced with underscores.

9. **Script Execution Flow:**
   - **Initialization:**
     - Loads environment variables and sets up headers.
     - Changes the working directory to the script’s location.
   - **Argument Parsing:**
     - Parses command-line arguments to determine whether to fetch data or download attachments.
   - **Action Execution:**
     - **If `--download` is set:**
       - Calls `download_attachments` with specified types and section.
     - **Else:**
       - Calls `get_course_csv` to fetch course data and save it to CSV.
   - **Termination:**
     - Exits gracefully upon successful completion or when encountering unrecoverable errors.

10. **Additional Considerations:**
    - **Timeouts:** Sets a timeout for HTTP requests to prevent indefinite hanging during downloads.
    - **Logging:** Prints informative messages to the console to track progress, errors, and actions taken.
    - **Extensibility:** Designed to be easily extendable for additional features, such as handling more attachment types or integrating with other storage solutions.

#### **Implementation Steps**

1. **Setup Environment:**
   - **Install Required Libraries:**

     ```bash
     pip install requests python-dotenv
     ```

   - **Create a `.env` File:**
     - Place a `.env` file in the same directory as the script containing:

       ```
       API_KEY=your_actual_api_key
       ```

     - Replace `your_actual_api_key` with your Teachable API key.

2. **Define Helper Functions:**
   - **Filename Sanitization:** `safe_filename` ensures all attachment filenames are safe and standardized.
   - **Rate Limiting:** `handle_rate_limit` manages API rate limits by detecting `429` responses and implementing wait times.
   - **Data Retrieval:** Functions like `fetch_course_id`, `get_course_details`, and `fetch_lecture_details` interact with the Teachable API to retrieve necessary data.
   - **Data Saving:** `save_text_attachment_as_html` and `save_to_csv` handle the storage of fetched data into files.

3. **Fetch and Save Course Data:**
   - **Retrieve Course ID:** Using the course name to get the unique course ID.
   - **Get Course Details:** Fetching detailed information about the course, including sections and lectures.
   - **Process Lectures and Attachments:** Iterating through sections and lectures to collect attachment data and save text attachments as HTML files.
   - **Compile and Save CSV:** Organizing all collected data into a CSV file with appropriate headers and encoding.

4. **Download Attachments:**
   - **Read CSV Data:** Loads `course_data.csv` to identify which attachments need to be downloaded based on user-specified types and sections.
   - **Construct Filenames:** Generates standardized filenames for each attachment.
   - **Check for Existing Files:** Skips downloading if the file already exists and is non-empty.
   - **Download with Retries:** Attempts to download each attachment, implementing retries with exponential backoff in case of network issues or rate limits.
   - **Handle Interruptions:** Cleans up partially downloaded files if the user interrupts the script (e.g., pressing `Ctrl+C`).

5. **Command-Line Interface:**
   - **Argument Parsing:** Utilizes `argparse` to handle user inputs for course name, section name, download flag, and attachment types.
   - **Execution Flow:** Determines whether to fetch course data or download attachments based on the provided arguments.

6. **Execution and Termination:**
   - **Run the Script:** Execute the script using Python with the desired command-line arguments.
   - **Graceful Exit:** Ensures the script exits cleanly after completing its tasks or when encountering critical errors.

#### **Error Handling Strategies**

- **API Rate Limits:** Detects and waits appropriately when the API rate limit is exceeded, ensuring compliance with Teachable's usage policies.
- **Network Resilience:** Implements retries with increasing delays to handle transient network issues, enhancing the script's robustness.
- **User Interruptions:** Captures `KeyboardInterrupt` events to clean up partial downloads and exit gracefully, preventing corrupted files.
- **File Operations:** Checks for the existence and integrity of files before attempting downloads, avoiding unnecessary network usage and ensuring data consistency.
- **Comprehensive Exception Handling:** Differentiates between various exception types to provide specific and actionable error messages, aiding in troubleshooting and maintaining script stability.

#### **Usage Examples**

- **Fetch and Save All Course Data:**

  ```bash
  python get_keto_coach_lectures.py
  ```

- **Fetch and Save Data for a Specific Section:**

  ```bash
  python get_keto_coach_lectures.py --course "Fachausbildung zum Coach für Ketogene Ernährung" --section "Modul 3"
  ```

- **Download All Types of Attachments:**

  ```bash
  python get_keto_coach_lectures.py --download
  ```

- **Download Specific Types of Attachments (e.g., Images and PDFs):**

  ```bash
  python get_keto_coach_lectures.py --download --types image pdf
  ```

- **Download Attachments from a Specific Section:**

  ```bash
  python get_keto_coach_lectures.py --download --section "Modul 3"
  ```

- **Combine Type and Section Filters:**

  ```bash
  python get_keto_coach_lectures.py --download --types image pdf --section "Modul 3"
  ```

## SRT Subtitles (Secret API)

Web Frontend does call <https://kurse.juliatulipan.com/api/v1/courses/42072/lectures/627981/attachments>

the reply attachments does have a attachments['captions']['language'] field to check for presence of captions

but:

```bash
curl --request GET --url https://developers.teachable.com/v1/courses/42072/lectures/627981/attachments      --header 'accept: application/json'      --header 'apiKey: x'
```

only gets us:

```json
{"message":"no Route matched with those values"}
```

```json
{
    "attachments": [
        {
            "created_at": "2015-12-22T08:05:43Z",
            "code_syntax": null,
            "content_type": "video/mp4",
            "audio_type": "video/mp4",
            "should_be_uploaded_to_wistia?": true,
            "data": null,
            "schema": null,
            "full_url": "https://kurse.juliatulipan.com/courses/42072/lectures/627981",
            "cdn_url": "https://cdn.fs.teachablecdn.com/EOtFBqjQNU7TQr7oXRzA",
            "alt_text": null,
            "flagged_as_decorative": null,
            "url": "https://d2vvqscadf4c1f.cloudfront.net/Oe8GCCVZSieIyYxaZAgn_07%20Einleitung%20Hauptn%C3%A4hrstoffe.mp4",
            "host_id": null,
            "source": "user",
            "kind": "video",
            "name": "07 Einleitung Hauptnährstoffe.mp4",
            "host": "wistia",
            "position": 1,
            "attachable_id": 627981,
            "is_published": true,
            "downloadable": false,
            "text": null,
            "attachable_type": "Lecture",
            "thumbnail_url": "https://fast.wistia.com/assets/images/zebra/elements/dashed-thumbnail.png",
            "meta": {
                "class": "attachment",
                "url": null,
                "name": "07 Einleitung Hauptnährstoffe.mp4",
                "description": "",
                "image_url": null,
                "status": "ready"
            },
            "embeddable": true,
            "id": 1208195,
            "display_text": "",
            "plain_text_html": "",
            "duration": 54,
            "captions": [
                {
                    "id": 2388500,
                    "caption_text": "WEBVTT\n\n1\n00:00:00.569 --\u003e 00:00:05.694 \nHerzlich willkommen zum Kurs Nährstoffgrundlagen, die Makronährstoffe.\n\n2\n00:00:05.734 --\u003e 00:00:09.799 \nIn diesem Kurs besprechen wir\n\n3\n00:00:09.819 --\u003e 00:00:13.743 \ndie drei Hauptnährstoffe oder die drei Makronährstoffe\n\n4\n00:00:13.823 --\u003e 00:00:19.070 \nEiweiß, Fett und Kohlenhydrate und zwar besprechen\n\n5\n00:00:19.110 --\u003e 00:00:22.512 \nwir für jeden der Makronährstoffe ganz genau, was ist die\n\n6\n00:00:22.552 --\u003e 00:00:26.214 \nFunktion im Körper, wie schaut die Absorption\n\n7\n00:00:26.254 --\u003e 00:00:30.417 \naus, die Verdauung, was passiert da mit dem Körper.\n\n8\n00:00:30.437 --\u003e 00:00:34.659 \nWenn wir dann uns sozusagen durch den Verdauungstrakt\n\n9\n00:00:34.679 --\u003e 00:00:38.116 \ngekämpft haben, Schauen wir uns dann an, wie auch\n\n10\n00:00:38.156 --\u003e 00:00:41.519 \ndie Energiegewinnung auf Zellniveau ausschaut.\n\n11\n00:00:41.559 --\u003e 00:00:44.682 \nUnterscheidet sich das, ob das jetzt Kohlenhydrate,\n\n12\n00:00:44.722 --\u003e 00:00:48.806 \nFett oder Protein ist.\n\n13\n00:00:48.886 --\u003e 00:00:53.009 \nUnd ganz zum Schluss besprechen wir auch noch kurz\n\n14\n00:00:53.029 --\u003e 00:00:53.650 \ndie Ketose.\n\n",
                    "language": "DE",
                    "attachment_id": 1208195,
                    "created_at": "2024-05-19T09:34:32Z",
                    "updated_at": "2024-07-09T08:18:58Z",
                    "school_id": 31070,
                    "options": {},
                    "hotmart_subtitle_id": "gL64Y4beRG",
                    "url": "https://contentplayer.hotmart.com/video/5Z13eMgEqX/subtitle/5Z13eMgEqX-1716111278255_DE.vtt?Policy=eyJTdGF0ZW1lbnQiOiBbeyJSZXNvdXJjZSI6Imh0dHBzOi8vY29udGVudHBsYXllci5ob3RtYXJ0LmNvbS92aWRlby81WjEzZU1nRXFYL3N1YnRpdGxlLzVaMTNlTWdFcVgtMTcxNjExMTI3ODI1NV9ERS52dHQiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3MzIxMzk2OTJ9fX1dfQ__\u0026Signature=fy8FasQiZR85y1-xwdGXuRl7VpwW35M3cvoYWlpfDy~A73d~S8m1lwLZAmJWaKRol6BTjMVv5zi-s2Ikpsqv8nvOb~GSuBQdlfAnWAUqOmxZNun1U2GVKiff19Janh1VbsEXjKZCcjuy-61R2aXpJ7fYHYivTRMuQKFe8kEb9MQmaoLasZiziWwLEaWdsPsqxBBdtrHPwcAbwhEmL1GRG52PjsGKcLFjs4staE~sTPXimiHLYRcuowAo1Jqj~VPIJOv~9i0gROZmVL7jH5L3y3qggkktg9bafnbBUZEvgtOBYO0RgwToU38~L5KA48IE9qEt3NvJ1vYq~VBatnHTOA__\u0026Key-Pair-Id=APKAI5B7FH6BVZPMJLUQ"
                }
            ],
            "hotmart_host_id": "5Z13eMgEqX",
            "should_upload_to_hotmart?": false,
            "hotmart_video_download_ready": true,
            "hotmart_url": "/api/v1/attachments/1208195/hotmart_video_download_link",
            "download_url": "/api/v1/attachments/1208195/download"
        },
        {
            "created_at": "2024-01-11T13:59:12Z",
            "code_syntax": null,
            "content_type": null,
            "audio_type": null,
            "should_be_uploaded_to_wistia?": false,
            "data": null,
            "schema": null,
            "full_url": "https://kurse.juliatulipan.com/courses/42072/lectures/627981",
            "cdn_url": null,
            "alt_text": null,
            "flagged_as_decorative": null,
            "url": null,
            "host_id": null,
            "source": "user",
            "kind": "text",
            "name": null,
            "host": null,
            "position": 2,
            "attachable_id": 627981,
            "is_published": true,
            "downloadable": false,
            "text": "\u003cp\u003eTranskript\u003c/p\u003e\u003cp\u003eHerzlich Willkommen zum Kurs Nährstoffgrundlagen. Die Makronährstoffe. \u003c/p\u003e\u003cp\u003eIn diesem diesem Kurs besprechen wir die drei Hauptnährstoffe: Eiweiß, Fett und Kohlenhydrate. \u003c/p\u003e\u003cp\u003eUnd zwar besprechen wir für jeden der Makronnährstoffe ganz genau. \u003c/p\u003e\u003cul\u003e\u003cli class=\"\"\u003eWas ist die Funktion im Körper? \u003c/li\u003e\u003cli class=\"\"\u003eWie schaut die Absorption aus? \u003c/li\u003e\u003cli class=\"\"\u003eDie Verdauung? \u003c/li\u003e\u003cli class=\"\"\u003eWas passiert dann mit dem Körper, wenn wir dann uns sozusagen durch den Verdauungstrakt gekämpft haben? \u003c/li\u003e\u003cli class=\"\"\u003eSchauen wir uns dann an, wie auch die Energiegewinnung auf Zellniveau ausschaut? Unterscheidet sich das, ob das jetzt Kohlenhydrate, Fett oder oder Protein ist. \u003c/li\u003e\u003c/ul\u003e\u003cp\u003eUnd ganz zum Schluss besprechen wir auch noch kurz die Ketose.\u003c/p\u003e",
            "attachable_type": "Lecture",
            "thumbnail_url": null,
            "meta": {
                "class": "attachment",
                "url": null,
                "name": null,
                "description": "",
                "image_url": null,
                "status": null
            },
            "embeddable": false,
            "id": 94649945,
            "display_text": "\u003cp\u003eTranskript\u003c/p\u003e\u003cp\u003eHerzlich Willkommen zum Kurs Nährstoffgrundlagen. Die Makronährstoffe. \u003c/p\u003e\u003cp\u003eIn diesem diesem Kurs besprechen wir die drei Hauptnährstoffe: Eiweiß, Fett und Kohlenhydrate. \u003c/p\u003e\u003cp\u003eUnd zwar besprechen wir für jeden der Makronnährstoffe ganz genau. \u003c/p\u003e\u003cul\u003e\n\u003cli class=\"\"\u003eWas ist die Funktion im Körper? \u003c/li\u003e\n\u003cli class=\"\"\u003eWie schaut die Absorption aus? \u003c/li\u003e\n\u003cli class=\"\"\u003eDie Verdauung? \u003c/li\u003e\n\u003cli class=\"\"\u003eWas passiert dann mit dem Körper, wenn wir dann uns sozusagen durch den Verdauungstrakt gekämpft haben? \u003c/li\u003e\n\u003cli class=\"\"\u003eSchauen wir uns dann an, wie auch die Energiegewinnung auf Zellniveau ausschaut? Unterscheidet sich das, ob das jetzt Kohlenhydrate, Fett oder oder Protein ist. \u003c/li\u003e\n\u003c/ul\u003e\u003cp\u003eUnd ganz zum Schluss besprechen wir auch noch kurz die Ketose.\u003c/p\u003e",
            "plain_text_html": "TranskriptHerzlich Willkommen zum Kurs Nährstoffgrundlagen. Die Makronährstoffe. In diesem diesem Kurs besprechen wir die drei Hauptnährstoffe: Eiweiß, Fett und Kohlenhydrate. Und zwar besprechen wir für jeden der Makronnährstoffe ganz genau. Was ist die Funktion im Körper? Wie schaut die Absorption aus? Die Verdauung? Was passiert dann mit dem Körper, wenn wir dann uns sozusagen durch den Verdauungstrakt gekämpft haben? Schauen wir uns dann an, wie auch die Energiegewinnung auf Zellniveau ausschaut? Unterscheidet sich das, ob das...",
            "text_constructor": {
                "id": 17646295,
                "constructor": {
                    "ops": [
                        {
                            "insert": "Transkript\nHerzlich Willkommen zum Kurs Nährstoffgrundlagen. Die Makronährstoffe. \nIn diesem diesem Kurs besprechen wir die drei Hauptnährstoffe: Eiweiß, Fett und Kohlenhydrate. \nUnd zwar besprechen wir für jeden der Makronnährstoffe ganz genau. \nWas ist die Funktion im Körper? "
                        },
                        {
                            "insert": "\n",
                            "attributes": {
                                "list": "bullet"
                            }
                        },
                        {
                            "insert": "Wie schaut die Absorption aus? "
                        },
                        {
                            "insert": "\n",
                            "attributes": {
                                "list": "bullet"
                            }
                        },
                        {
                            "insert": "Die Verdauung? "
                        },
                        {
                            "insert": "\n",
                            "attributes": {
                                "list": "bullet"
                            }
                        },
                        {
                            "insert": "Was passiert dann mit dem Körper, wenn wir dann uns sozusagen durch den Verdauungstrakt gekämpft haben? "
                        },
                        {
                            "insert": "\n",
                            "attributes": {
                                "list": "bullet"
                            }
                        },
                        {
                            "insert": "Schauen wir uns dann an, wie auch die Energiegewinnung auf Zellniveau ausschaut? Unterscheidet sich das, ob das jetzt Kohlenhydrate, Fett oder oder Protein ist. "
                        },
                        {
                            "insert": "\n",
                            "attributes": {
                                "list": "bullet"
                            }
                        },
                        {
                            "insert": "Und ganz zum Schluss besprechen wir auch noch kurz die Ketose.\n"
                        }
                    ]
                },
                "attachment_id": 94649945,
                "school_id": 31070,
                "created_at": "2024-01-11T13:59:13Z",
                "updated_at": "2024-01-11T13:59:13Z"
            },
            "download_url": "/api/v1/attachments/94649945/download"
        }
    ]
}
```
