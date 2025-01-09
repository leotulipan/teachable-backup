# Teachable API documentation and examples

API Reference with direct testing here

<https://docs.teachable.com/reference/listcourses>

## Public URLS

Course ID: 42072
Admin Course URL: <https://kurse.juliatulipan.com/admin-app/courses/42072/curriculum>

Lecture ID: 640163
Course ID: 42072
Admin Lecture URL: <https://kurse.juliatulipan.com/admin-app/courses/42072/curriculum/lessons/640163>

## Fetch a specific course by ID

<https://developers.teachable.com/v1/courses/{course_id}>

```python
import requests

url = "https://developers.teachable.com/v1/courses/42072"

headers = {
    "accept": "application/json",
    "apiKey": ""
}

response = requests.get(url, headers=headers)

print(response.text)
```

```json
{
  "course": {
    "id": 42072,
    "description": "<ul>\n\t<li>Hauptnährstoffe – Fett, Eiweiß,\nKohlenhydrate\n\t</li>\n\t<li>Funktion</li>\n\t<li>Struktur</li>\n\t<li>Energiegewinnung in der Zelle\n\t<ul>\n\t\t<li>Glykolyse</li>\n\t\t<li>Citrat-Zyklus</li>\n\t\t<li>Elektronentransportkette</li>\n\t</ul></li>\n\t<li>Transport im Körper</li>\n\t<li>Absorption in die Zelle</li>\n\t<li>Gastrointestinale Verdauung</li>\n\t<li>Ketone</li>\n\t<li>Lipoproteine</li>\n</ul>",
    "name": "Makronährstoffe  - Eiweiß, Fett, Kohlenhydrate und Ketone",
    "heading": "Makronährstoffe - Verdauung, Absorbtion und Energiegewinnung",
    "is_published": true,
    "image_url": "https://d2vvqscadf4c1f.cloudfront.net/KwgheWNnRCuAEB0ooqTL_Kurs%20Thumbnail%20Teachable.jpg",
    "lecture_sections": [
      {
        "id": 148634,
        "name": "Herzlich Willkommen",
        "is_published": true,
        "position": 1,
        "lectures": [
          {
            "id": 627981,
            "position": 1,
            "is_published": true
          },
          {
            "id": 680407,
            "position": 2,
            "is_published": true
          }
        ]
      },
      {
        "id": 157368,
        "name": "Modul 5: Nahrungsinduzierte Ketose",
        "is_published": false,
        "position": 6,
        "lectures": [
          {
            "id": 640163,
            "position": 1,
            "is_published": true
          },
          {
            "id": 640165,
            "position": 2,
            "is_published": false
          },
          {
            "id": 640166,
            "position": 3,
            "is_published": false
          },
          {
            "id": 640164,
            "position": 4,
            "is_published": false
          },
          {
            "id": 717462,
            "position": 5,
            "is_published": true
          },
          {
            "id": 717464,
            "position": 6,
            "is_published": true
          },
          {
            "id": 717466,
            "position": 7,
            "is_published": true
          },
          {
            "id": 717469,
            "position": 8,
            "is_published": true
          }
        ]
      },
      {
        "id": 157365,
        "name": "Modul 2: Fette",
        "is_published": true,
        "position": 3,
        "lectures": [
          {
            "id": 640141,
            "position": 1,
            "is_published": true
          },
          {
            "id": 640144,
            "position": 2,
            "is_published": true
          },
          {
            "id": 640145,
            "position": 3,
            "is_published": true
          },
          {
            "id": 640149,
            "position": 4,
            "is_published": true
          },
          {
            "id": 640142,
            "position": 5,
            "is_published": true
          },
          {
            "id": 640147,
            "position": 6,
            "is_published": false
          }
        ]
      },
      {
        "id": 157366,
        "name": "Modul 3: Proteine",
        "is_published": true,
        "position": 4,
        "lectures": [
          {
            "id": 640151,
            "position": 1,
            "is_published": true
          },
          {
            "id": 640154,
            "position": 2,
            "is_published": true
          },
          {
            "id": 640152,
            "position": 3,
            "is_published": true
          },
          {
            "id": 640155,
            "position": 4,
            "is_published": false
          }
        ]
      },
      {
        "id": 157367,
        "name": "Modul 4: Energiegewinnung in der tierischen Zelle",
        "is_published": true,
        "position": 5,
        "lectures": [
          {
            "id": 714847,
            "position": 1,
            "is_published": true
          },
          {
            "id": 640159,
            "position": 2,
            "is_published": true
          },
          {
            "id": 640162,
            "position": 3,
            "is_published": true
          },
          {
            "id": 714863,
            "position": 4,
            "is_published": true
          },
          {
            "id": 640156,
            "position": 5,
            "is_published": true
          },
          {
            "id": 640157,
            "position": 6,
            "is_published": false
          },
          {
            "id": 640160,
            "position": 7,
            "is_published": false
          },
          {
            "id": 640161,
            "position": 8,
            "is_published": false
          }
        ]
      },
      {
        "id": 157364,
        "name": "Modul 1: Kohlenhydrate",
        "is_published": true,
        "position": 2,
        "lectures": [
          {
            "id": 640133,
            "position": 1,
            "is_published": true
          },
          {
            "id": 640134,
            "position": 2,
            "is_published": true
          },
          {
            "id": 640136,
            "position": 3,
            "is_published": true
          },
          {
            "id": 640137,
            "position": 4,
            "is_published": true
          },
          {
            "id": 640138,
            "position": 5,
            "is_published": true
          },
          {
            "id": 787451,
            "position": 6,
            "is_published": true
          }
        ]
      }
    ],
    "author_bio": {
      "profile_image_url": "https://www.filepicker.io/api/file/WIqawd7TAGjkCaZlVVxw",
      "bio": "<p>Mag. Julia Tulipan ist Biologin und Ernährungswissenschaftlerin, Bloggerin, Autorin, Sprecherin, Unternehmerin und Wissenschafts-Nerd.\n</p>\n<p><span style=\"font-family:Arial;\">Als Coach hilft sie jetzt anderen auf ihrem Weg zu Gesundheit und Wohlbefinden. Und unterstützt leistungsstarke Menschen dabei, ihr Potenzial zu entfalten. Sie schreibt einen der beliebtesten deutschen Blogs über den Low-Carb- und Keto-Lebensstil. </span>\n</p>\n<p><span style=\"font-family:Arial;\">Sie ist Gründungsmitglied des Ess-Wissen Club für Praktiker (EWiP), einer Mitgliederplattform für Gesundheitsfachleute, Coaches, Krankenschwestern und Ärzte. Im Rahmen von EWiP gehen sie und ihre Mitgründer Studien und wissenschaftliche Arbeiten durch, bereiten Infografiken, Folien und Materialien für Ihre Arbeit mit Kunden vor.</span>\n</p>\n<p><span style=\"font-family:Arial;\">Neben ihren unternehmerischen Bestrebungen ist sie im Herzen Wissenschaftlerin.</span>\n</p>\n<p><br>\n</p>",
      "name": "Mag. Julia Tulipan MSc.",
      "user_id": null
    }
  }
}
```

## Fetch content of a specific course lecture

<https://developers.teachable.com/v1/courses/{course_id}/lectures/{lecture_id}>

```python
import requests

url = "https://developers.teachable.com/v1/courses/42072/lectures/640163"

headers = {
    "accept": "application/json",
    "apiKey": ""
}

response = requests.get(url, headers=headers)

print(response.text)
```

Notes:

- file_size is always 0 for videos.
- subtitles are never shown in the export, even if they are available. e.g. <https://kurse.juliatulipan.com/admin-app/courses/2221627/curriculum/lessons/49584165>
  - We need to check the admin lecture url manually to find out if subtitles are available.
  - When we have non we will find the text "No subtitles" in a span following a span with text Subtitles:

    ```html
    <div class="AttachmentVideo_videoInfo__gMH5q"><svg width="24" height="24" class="AttachmentVideo_captionIcons__1qyGj"><use xlink:href="#icon__ClosedCaptionOn"></use></svg><span class="XSXtW">Subtitles:</span><span class="XSXtW">German (Deutsch)</span></div>
    <h1>Version without subtitles</h1>
    <div class="AttachmentVideo_videoInfo__gMH5q"><svg width="24" height="24" class="AttachmentVideo_captionIcons__1qyGj"><use xlink:href="#icon__ClosedCaptionOff"></use></svg><span class="XSXtW">No subtitles</span></div>
    ```

```json
{
  "lecture": {
    "id": 640163,
    "name": "Was sind Ketonkörper",
    "position": 1,
    "is_published": true,
    "lecture_section_id": 157368,
    "attachments": [
      {
        "id": 1353690,
        "name": "14-Energiegewinnung_ketose.wmv.mp4",
        "kind": "video",
        "url": "https://d2vvqscadf4c1f.cloudfront.net/4GYta7LQQdepH7rIf0YR_14-Energiegewinnung_ketose.wmv.mp4",
        "text": null,
        "position": 1,
        "file_size": 0,
        "file_extension": "mp4"
      }
    ]
  }
}
```

## Fetch a specific video information

- use the attachment id from the lecture attachement of kind video
- we can download a video thumbnail with the url_thumbnail and
- we get the media_duration in seconds

<https://developers.teachable.com/v1/courses/{course_id}/lectures/{lecture_id}/videos/{video_id}>

example: <https://developers.teachable.com/v1/courses/2221627/lectures/49584165/videos/91078841>

```json
{
  "video": {
    "id": 1353690,
    "video_asset": {
      "url": "https://vod-akm.play.hotmart.com/video/NRkYovxVLe/hls/master-pkg-t-1649388880000.m3u8?hdnts=st%3D1731666672%7Eexp%3D1731667172%7Ehmac%3Dde70399b004b24de5fe31aed1cea1c74e51260faf3ec29102f7b02fe7eb6733c&app=aa2d356b-e2f0-45e8-9725-e0efc7b5d29c",
      "content_type": "application/x-mpegURL"
    },
    "status": "READY",
    "url_thumbnail": "https://img-akm.play.hotmart.com/video/NRkYovxVLe/thumbnail/9fe7e9e1-8552-4a21-90be-ae0e00d0002c.jpg?token=exp=1731667172~acl=%2fvideo%2fNRkYovxVLe%2fthumbnail%2f9fe7e9e1-8552-4a21-90be-ae0e00d0002c.jpg*~hmac=a58495e573f61702a300dd94e3729f4a715b62ccf2743117f7d17a550ce87e64",
    "media_type": "VIDEO",
    "media_duration": 154
  }
}
```

## Fetch an id list of quizzes in a specific course lecture

<https://developers.teachable.com/v1/courses/{course_id}/lectures/{lecture_id}/quizzes>

if empty, return an empty list:

```json
{
  "quiz_ids": []
}
```

## Return of quiz on lecture fetch

the above already mentioned endpoint

<https://developers.teachable.com/v1/courses/{course_id}/lectures/{lecture_id}>

if we want just the quiz we can : Fetch a specific quiz information.
<https://developers.teachable.com/v1/courses/{course_id}/lectures/{lecture_id}/quizzes/{quiz_id}>
note: {quiz_id} = attachment_id

```json
{
  "quiz": {
    "id": 94495069,
    "name": null,
    "kind": "quiz",
    "url": null,
    "text": null,
    "position": 5,
    "quiz": {
      "id": 2152473,
      "type": "Quiz",
      "questions": [
        {
          "question": "Was bezeichnet das Konzept von \"artgerecht\"?",
          "question_type": "single",
          "answers": [
            " Eine Ernährung, die ausschließlich auf Pflanzen basiert.",
            "Leben in Einklang mit unserer evolutionären Anpassung und der Ernährung, die uns geprägt hat.",
            "Die Nutzung moderner Technologien zur Verbesserung der Gesundheit.",
            " Eine Ernährung, die sich ausschließlich auf Fleisch konzentriert."
          ],
          "correct_answers": [
            "Leben in Einklang mit unserer evolutionären Anpassung und der Ernährung, die uns geprägt hat."
          ],
          "graded": true
        },
        {
          "question": "Welche Methoden werden verwendet, um zu bestimmen, was \"artgerecht\" ist?",
          "question_type": "single",
          "answers": [
            "Archäologische Funde und Vergleich mit unseren nächsten lebenden Verwandten.",
            "Astrologische Berechnungen und traditionelle Mythen.",
            "Moderne Diät-Trends und populärwissenschaftliche Bücher.",
            "Online-Umfragen und Fernsehdokumentationen."
          ],
          "correct_answers": [
            "Archäologische Funde und Vergleich mit unseren nächsten lebenden Verwandten."
          ],
          "graded": true
        },
        {
          "question": "Was ist die Hauptnahrung von Gorillas?",
          "question_type": "single",
          "answers": [
            "Fleisch und Fisch.",
            "Blätter, Früchte und Insekten.",
            "Körner und Samen.",
            " Künstliches Gorillafutter aus dem Zoo."
          ],
          "correct_answers": [
            "Blätter, Früchte und Insekten."
          ],
          "graded": true
        },
        {
          "question": "Welchen Anteil hat tierische Nahrung in der Ernährung von Schimpansen?",
          "question_type": "single",
          "answers": [
            "50-60%.",
            "0%",
            "3-5%",
            "25-30%"
          ],
          "correct_answers": [
            "3-5%"
          ],
          "graded": true
        }
      ]
    }
  }
}
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
