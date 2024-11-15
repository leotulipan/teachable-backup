# Teachable API documentation and examples

## Public URLS

Course ID: 42072
Admin Course URL: https://kurse.juliatulipan.com/admin-app/courses/42072/curriculum

Lecture ID: 640163
Course ID: 42072
Admin Lecture URL: https://kurse.juliatulipan.com/admin-app/courses/42072/curriculum/lessons/640163

## Fetch a specific course by ID

https://developers.teachable.com/v1/courses/{course_id}

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


## Fetch content of a specific course lecture.

https://developers.teachable.com/v1/courses/{course_id}/lectures/{lecture_id}

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
- subtitles are never shown in the export, even if they are available. e.g. https://kurse.juliatulipan.com/admin-app/courses/2221627/curriculum/lessons/49584165
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

https://developers.teachable.com/v1/courses/{course_id}/lectures/{lecture_id}/videos/{video_id}

example: https://developers.teachable.com/v1/courses/2221627/lectures/49584165/videos/91078841

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
