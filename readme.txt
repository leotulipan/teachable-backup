import requests

url = "https://developers.teachable.com/v1/courses?name=Fachausbildung%20zum%20Coach%20f%C3%BCr%20Ketogene%20Ern%C3%A4hrung"

headers = {
    "accept": "application/json",
    "apiKey": "a4FeOmHTvNtPBzRdlB28P39SUB8rdUuC"
}

response = requests.get(url, headers=headers)

#{
#  "courses": [
#    {
#      "id": 249837,
#      "description": "",
#      "name": "Fachausbildung zum Coach für Ketogene Ernährung",
#      "heading": "Fachfortbildung für ErnährungsberaterInnen, DiätologInnen, Diätassitentinnen, ÄrtzInnen",
#      "is_published": true,
#      "image_url": "https://www.filepicker.io/api/file/zoMapMMcQM6V7DrYbmJ4"
#    }
#  ],
#  "meta": {
#    "total": 1,
#    "page": 1,
#    "from": 1,
#    "to": 1,
#    "per_page": 20,
#    "number_of_pages": 1
#  }
#}

# Now get all the details for this courses_id

url = "https://developers.teachable.com/v1/courses/249837"

#{
#  "course": {
#    "id": 249837,
#    "description": "",
#    "name": "Fachausbildung zum Coach für Ketogene Ernährung",
#    "heading": "Fachfortbildung für ErnährungsberaterInnen, DiätologInnen, Diätassitentinnen, ÄrtzInnen",
#    "is_published": true,
#    "image_url": "https://www.filepicker.io/api/file/zoMapMMcQM6V7DrYbmJ4",
#    "lecture_sections": [
#      {
#        "id": 984810,
#        "name": "Modul 5",
#        "is_published": true,
#        "position": 6,
#        "lectures": [
#          {
#            "id": 5323555,
#            "position": 1
#          },
#          {
#            "id": 5206717,
#            "position": 2
#          },
#          {
#            "id": 5206716,
#            "position": 3
#          },
#          {
#            "id": 6744593,
#            "position": 4
#          },
#          {
#            "id": 5206719,
#            "position": 5
#          }
#        ]
#      }

#find all lectures inside each section. save the id (example 984810) and name (eg. Modul 5) and the position and id of the lectures

# loop all lecture ids

url = "https://developers.teachable.com/v1/courses/249837/lectures/5206717"

# {
#   "lecture": {
#     "id": 5206717,
#     "name": "Ketogene Ernährung vs therapeutische Ketose",
#     "position": 2,
#     "is_published": true,
#     "lecture_section_id": 984810,
#     "attachments": [
#       {
#         "id": 13491712,
#         "name": "_KetoCoach_ketogene_Diaet_therapeutische_Ketose.mkv",
#         "kind": "video",
#         "url": "https://www.filepicker.io/api/file/qgIyudd4R1a85NavhpZj",
#         "text": null,
#         "position": 1,
#         "file_size": 0,
#         "file_extension": "mkv"
#       },
#       {
#         "id": 13491714,
#         "name": "_KetoCoach_Ketogene_Diaet_therapeutische_Ketose.pdf",
#         "kind": "pdf_embed",
#         "url": "https://www.filepicker.io/api/file/0k5Ww0TSRRmesQZ66g6B",
#         "text": null,
#         "position": 2,
#         "file_size": 0,
#         "file_extension": "pdf"
#       }
#     ]
#   }
# }

# save the name, is_published, position
# from each attachment save
#   name, kind, url

# create csv, one row for each attachment

# columns:
# course_id
# course_name
# lecture_section_id
# lecture_section_name
# lecture_section_position
# lecture_id
# lecture_position
# lecture_name
# lecture_is_published
# lecture_attachment_id
# lecture_attachment_kind
# lecture_attachmenturl









/v1/courses/249837/lectures/9172679 wird zu:
https://kurse.juliatulipan.com/admin-app/courses/249837/curriculum/lessons/9172679

1 Lecture:

{
  "lecture": {
    "id": 9172679,
    "name": "NAFLD - die nichtalkoholbedingte Fettleber Grundlagen",
    "position": 1,
    "is_published": true,
    "lecture_section_id": 1458078,
    "attachments": [
      {
        "id": 18386212,
        "name": "NAFLD #1 KC.mkv",
        "kind": "video",
        "url": "https://www.filepicker.io/api/file/8Sysz8lJStaHJuNUxfrW",
        "text": null,
        "position": 1,
        "file_size": 0,
        "file_extension": "mkv"
      },
      {
        "id": 18386217,
        "name": "NAFLD #1 U.pdf",
        "kind": "pdf_embed",
        "url": "https://www.filepicker.io/api/file/lVOEcdET8KMFTQ6B24Rc",
        "text": null,
        "position": 2,
        "file_size": 0,
        "file_extension": "pdf"
      }
    ]
  }

/v1/courses/{course_id} via https://docs.teachable.com/reference/showcourse


{
  "course": {
    "id": 249837,
    "description": "<p><br>\n</p>\n<h1>Ausbildungsziel</h1>\n<p>Die Ausbildung „Coach für ketogene Ernährung“ ist als Erweiterung und Festigung bereits bestehenden Grundlagenwissens zu Low-Carb aber vor allem als umfassender Einstieg in die ketogene Ernährung gedacht. Ziel der Ausbildung ist es sowohl die historischen Hintergründe, biochemische Grundlagen, theoretischen Wissen zu vermitteln und vor allem eine Anleitung zur praktischen Umsetzung zu geben.\n</p>\n<h1>Ausbildung</h1>\n<p>Die Ausbildung zum „Coach für ketogene Ernährung“ ist als Fernstudium geplant und erfordert keine Präsenzzeiten. Die Lehrinhalte werden über eine online Lernplattform angeboten und bestehen aus Videolektionen, Arbeitsblättern und Folien im PDF-Format. Alle Videos sind mit Untertitel versehen.\n</p>\n<p>Im Rahmen der Ausbildung ist eine schriftliche Hausarbeit zu erstellen sowie eine schriftliche Prüfung abzulegen.\n</p>\n<p>Während der Ausbildungszeit werden Sie fachlich und persönlich von uns betreut.\n</p>\n<h1>Ausbildungsbeginn und Abschluss</h1>\n<p>Die Ausbildung kann jederzeit begonnen werden. Die Inhalte werden auf einer Lernplattform bereitgestellt und das Lerntempo kann den persönlichen Bedürfnissen angepasst werden. Die Inhalte sind in Module und Lektionen unterteilt, welche in Chargen freigeschalten werden. Die Ausbildung dauert mindestens 6 Monate muss spätestens nach 18 Monaten abgeschlossen werden.\n</p>\n<p>Abgeschlossen ist die Ausbildung dann, wenn Sie die Hausarbeit, die Abschlussarbeit sowie die schriftliche Prüfung mit einer positiven Endnote abgegeben haben. Außerdem muss ein Nachweis der Trainerkompetenz erbracht worden sein.\n</p>\n<p>Prüfungstermine werden dreimal im Jahr angeboten. Da die Prüfung online abgehalten wird, und die meisten berufstätig sind, wird sie immer abends und/ oder am Wochenende stattfinden.\n</p>\n<p>HINWEIS FÜR ÖSTERREICH\n</p>\n<p>Bitte beachten Sie, dass die Ernährungsberatung in Österreich bestimmten Berufsgruppen vorbehalten ist. Der vorliegende Experten/innenlehrgang dient der fachlichen Weiterbildung, aus der Teilnahme am Lehrgang leitet sich keine Berufsberechtigung für Ernährungsberatung ab.\n</p>\n<h1>Voraussetzung</h1>\n<p>Die Ausbildung zum zertifizierten Coach für ketogene Ernährung richtete sich an folgende Berufsgruppen: Ärzte und Ärztinnen, DiätologInnen und ÖkotrophologInnen, wie auch im ernährungsmedizinischen Bereich tätige PharmazeutInnen, SportwissenschafterInnen, ErnährungswissenschafterInnen, DiätassistentInnen, DiabetesberaterInnen, ErnährungsberaterInnen mit einem Abschluss an einem anerkannten Ausbildungsinstitut im In- oder Ausland, PhysiotherapeutInnen und Diplomiertes Gesundheits- und Krankenpflegepersonal.\n</p>\n<p>Sollte keine der oben genannten Berufsbezeichnungen auf Sie zutreffen, kann ein Antrag auf die Feststellung der individuellen Befähigung zur Teilnahme gestellt werden.\n</p>\n<p><strong>Nachweis der Trainerkompetenz bzw. Coachausbildung:</strong>\n</p>\n<p>Für den Abschluss der Ausbildung ist ein Nachweis über Beratungserfahrung (min. 1 Jahr Berufserfahrung) oder eine Fortbildung zu Beratungstechniken im Ausmaß von 20 UE zu erbringen.\n</p>\n<p>Eigenverantwortung, selbständiges Denken und Handeln sind Grundvoraussetzungen. Insbesondere während der Ausbildung ist eine intensive Auseinandersetzung mit den Themen gefragt. Das Lesen von Fachliteratur aus den Themenkomplexen ist äußerst empfehlenswert.\n</p>\n<h1>DozentInnen</h1>\n<h2>Daniela Pfeifer, Diätologin</h2>\n<p>„Tu deinem Leib etwas Gutes, damit deine Seele Lust hat, darin zu wohnen.“ Teresa von Ávila\n</p>\n<p>Daniela Pfeifer ist Diätologin, TCM-Therapeutin, Ernährungsberaterin nach der TCM, Buchautorin, Referentin und Unternehmerin.\n</p>\n<p>Sie ist seit vielen Jahren selbständige Diätologin und hat sich der Verbreitung sowie „Entmythifizierung“ der LowCarb und Ketogenen Ernährung verschrieben. Zahlreiche Vorträge, Kurse und Webinare für Fachleute und Laien, sowie mittlerweile 7 Bücher zu diesen Themen, ermöglichen es ihr das umfangreiche Wissen weiterzuverbreiten.\n</p>\n<p>Kontakt: daniela-pfeifer.at; info@daniela-pfeifer.at; Facebook: lowcarbgoodies\n</p>\n<h2>Mag. Julia Tulipan, Biologin</h2>\n<p>\"Nothing in biology makes sense, except in light of evolution.\" - Christian Theodosius Dobzhansky\n</p>\n<p>Julia Tulipan ist Biologin, Dipl. Personal Fitness und Health Trainerin, Buchautorin, Referent und Unternehmerin. Coach für evolutionäre Gesundheit und ketogene Ernährung.\n</p>\n<p>Julia Tulipan ist selbstständiger Ernährungscoach in Wien. Sie schreibt ein sehr erfolgreiches Blog und produziert eine deutsche Podcast-Show: die Evolution Radio Show.\n</p>\n<p>Julia Tulipan hat eine ausgeprägte wissenschaftliche Orientierung, aus diesem Grund macht sie zurzeit den Master in klinischer Ernährungsmedizin an der Donauuniversität Krems.\n</p>\n<p>Kontakt: www.JuliaTulipan.com; julia@juliatulipan.com; Facebook: PaleoLC\n</p>",
    "name": "Fachausbildung zum Coach für Ketogene Ernährung",
    "heading": "Fachfortbildung für ErnährungsberaterInnen, DiätologInnen, Diätassitentinnen, ÄrtzInnen",
    "is_published": true,
    "image_url": "https://www.filepicker.io/api/file/zoMapMMcQM6V7DrYbmJ4",
    "lecture_sections": [
      {
        "id": 984810,
        "name": "Modul 5",
        "is_published": true,
        "position": 6,
        "lectures": [
          {
            "id": 5323555,
            "position": 1
          },
          {
            "id": 5206717,
            "position": 2
          },
          {
            "id": 5206716,
            "position": 3
          },
          {
            "id": 6744593,
            "position": 4
          },
          {
            "id": 5206719,
            "position": 5
          }
        ]
      },
      {
        "id": 1923657,
        "name": "Weitere Ideen zu Inhalten - nur Intern als Ideenspeicher",
        "is_published": true,
        "position": 17,
        "lectures": [
          {
            "id": 5234256,
            "position": 1
          },
          {
            "id": 5234208,
            "position": 2
          },
          {
            "id": 6202309,
            "position": 3
          },
          {
            "id": 6142724,
            "position": 4
          },
          {
            "id": 5234204,
            "position": 5
          },
          {
            "id": 5234205,
            "position": 6
          },
          {
            "id": 20139425,
            "position": 7
          }
        ]
      },
      {
        "id": 984807,
        "name": "Modul 2",
        "is_published": true,
        "position": 3,
        "lectures": [
          {
            "id": 4127085,
            "position": 1
          }
        ]
      },
      {
        "id": 6331940,
        "name": "Modul 15 Wissenschaftliches Arbeiten",
        "is_published": true,
        "position": 16,
        "lectures": [
          {
            "id": 34127745,
            "position": 1
          },
          {
            "id": 34127792,
            "position": 2
          },
          {
            "id": 34127797,
            "position": 3
          },
          {
            "id": 34127850,
            "position": 4
          }
        ]
      },
      {
        "id": 2511504,
        "name": "Live Q&A Aufzeichnungen",
        "is_published": true,
        "position": 22,
        "lectures": [
          {
            "id": 12944469,
            "position": 1
          },
          {
            "id": 12972635,
            "position": 2
          },
          {
            "id": 12037709,
            "position": 3
          },
          {
            "id": 13975343,
            "position": 4
          },
          {
            "id": 23169335,
            "position": 5
          },
          {
            "id": 24642515,
            "position": 6
          },
          {
            "id": 24837640,
            "position": 7
          },
          {
            "id": 28689624,
            "position": 8
          },
          {
            "id": 30126546,
            "position": 9
          },
          {
            "id": 31687721,
            "position": 10
          },
          {
            "id": 32403258,
            "position": 11
          },
          {
            "id": 33375651,
            "position": 12
          },
          {
            "id": 33892509,
            "position": 13
          },
          {
            "id": 35567057,
            "position": 14
          },
          {
            "id": 37272675,
            "position": 15
          },
          {
            "id": 38004243,
            "position": 16
          },
          {
            "id": 38609403,
            "position": 17
          },
          {
            "id": 39273847,
            "position": 18
          },
          {
            "id": 39725436,
            "position": 19
          },
          {
            "id": 40830694,
            "position": 20
          },
          {
            "id": 41698018,
            "position": 21
          },
          {
            "id": 42307923,
            "position": 22
          },
          {
            "id": 43270233,
            "position": 23
          },
          {
            "id": 43867130,
            "position": 24
          },
          {
            "id": 44461025,
            "position": 25
          },
          {
            "id": 44903352,
            "position": 26
          },
          {
            "id": 45406020,
            "position": 27
          },
          {
            "id": 45876316,
            "position": 28
          },
          {
            "id": 46461583,
            "position": 29
          },
          {
            "id": 47023344,
            "position": 30
          },
          {
            "id": 47515690,
            "position": 31
          },
          {
            "id": 48110216,
            "position": 32
          },
          {
            "id": 48580601,
            "position": 33
          },
          {
            "id": 49065791,
            "position": 34
          }
        ]
      },
      {
        "id": 1458072,
        "name": "Modul 7",
        "is_published": true,
        "position": 8,
        "lectures": [
          {
            "id": 5206725,
            "position": 1
          },
          {
            "id": 5206722,
            "position": 2
          },
          {
            "id": 5206720,
            "position": 3
          },
          {
            "id": 8438908,
            "position": 4
          },
          {
            "id": 8438955,
            "position": 5
          },
          {
            "id": 6969406,
            "position": 6
          },
          {
            "id": 5234158,
            "position": 7
          },
          {
            "id": 5234160,
            "position": 8
          },
          {
            "id": 8439026,
            "position": 9
          },
          {
            "id": 8439067,
            "position": 10
          },
          {
            "id": 8439086,
            "position": 11
          },
          {
            "id": 5234162,
            "position": 12
          },
          {
            "id": 5234183,
            "position": 13
          },
          {
            "id": 8439226,
            "position": 14
          }
        ]
      },
      {
        "id": 984809,
        "name": "Modul 4",
        "is_published": true,
        "position": 5,
        "lectures": [
          {
            "id": 5206710,
            "position": 1
          },
          {
            "id": 5358727,
            "position": 2
          },
          {
            "id": 5206711,
            "position": 3
          },
          {
            "id": 5298355,
            "position": 4
          },
          {
            "id": 6193285,
            "position": 5
          },
          {
            "id": 5206712,
            "position": 6
          },
          {
            "id": 5206713,
            "position": 7
          },
          {
            "id": 5206714,
            "position": 8
          },
          {
            "id": 6654176,
            "position": 9
          },
          {
            "id": 6079120,
            "position": 10
          },
          {
            "id": 6079110,
            "position": 11
          },
          {
            "id": 6079131,
            "position": 12
          }
        ]
      },
      {
        "id": 1458075,
        "name": "Modul 9",
        "is_published": true,
        "position": 10,
        "lectures": [
          {
            "id": 4127088,
            "position": 1
          },
          {
            "id": 6118382,
            "position": 2
          },
          {
            "id": 8615966,
            "position": 3
          },
          {
            "id": 8616109,
            "position": 4
          },
          {
            "id": 5206727,
            "position": 5
          },
          {
            "id": 6202330,
            "position": 6
          },
          {
            "id": 8644952,
            "position": 7
          }
        ]
      },
      {
        "id": 1458079,
        "name": "Modul 13",
        "is_published": true,
        "position": 14,
        "lectures": [
          {
            "id": 5234249,
            "position": 1
          },
          {
            "id": 5234250,
            "position": 2
          },
          {
            "id": 4127089,
            "position": 3
          },
          {
            "id": 8645156,
            "position": 4
          },
          {
            "id": 9187798,
            "position": 5
          },
          {
            "id": 9363217,
            "position": 6
          },
          {
            "id": 9376752,
            "position": 7
          },
          {
            "id": 6039666,
            "position": 8
          },
          {
            "id": 9376820,
            "position": 9
          },
          {
            "id": 9475526,
            "position": 10
          }
        ]
      },
      {
        "id": 1458080,
        "name": "Modul 14",
        "is_published": true,
        "position": 15,
        "lectures": [
          {
            "id": 5234258,
            "position": 1
          },
          {
            "id": 9475504,
            "position": 2
          },
          {
            "id": 9475509,
            "position": 3
          },
          {
            "id": 8644981,
            "position": 4
          },
          {
            "id": 5234255,
            "position": 5
          },
          {
            "id": 9475716,
            "position": 6
          },
          {
            "id": 9475719,
            "position": 7
          },
          {
            "id": 5234251,
            "position": 8
          },
          {
            "id": 9475897,
            "position": 9
          },
          {
            "id": 5234252,
            "position": 10
          }
        ]
      },
      {
        "id": 6907527,
        "name": "Deep Dive Proteine",
        "is_published": true,
        "position": 23,
        "lectures": [
          {
            "id": 37241829,
            "position": 1
          },
          {
            "id": 37241836,
            "position": 2
          }
        ]
      },
      {
        "id": 926062,
        "name": "Modul 1",
        "is_published": true,
        "position": 2,
        "lectures": [
          {
            "id": 5206646,
            "position": 1
          },
          {
            "id": 6066711,
            "position": 2
          },
          {
            "id": 6067949,
            "position": 3
          },
          {
            "id": 5282441,
            "position": 4
          },
          {
            "id": 6078869,
            "position": 5
          },
          {
            "id": 5282443,
            "position": 6
          },
          {
            "id": 5206647,
            "position": 7
          },
          {
            "id": 5282450,
            "position": 8
          },
          {
            "id": 5282464,
            "position": 9
          },
          {
            "id": 5206651,
            "position": 10
          },
          {
            "id": 5206683,
            "position": 11
          },
          {
            "id": 6180638,
            "position": 12
          },
          {
            "id": 6180944,
            "position": 13
          },
          {
            "id": 6180962,
            "position": 14
          },
          {
            "id": 5206652,
            "position": 15
          },
          {
            "id": 5721938,
            "position": 16
          },
          {
            "id": 5722146,
            "position": 17
          }
        ]
      },
      {
        "id": 984808,
        "name": "Modul 3",
        "is_published": true,
        "position": 4,
        "lectures": [
          {
            "id": 4127116,
            "position": 1
          },
          {
            "id": 5206703,
            "position": 2
          },
          {
            "id": 5322782,
            "position": 3
          },
          {
            "id": 6142715,
            "position": 4
          },
          {
            "id": 5206707,
            "position": 5
          },
          {
            "id": 4127084,
            "position": 6
          },
          {
            "id": 6176705,
            "position": 7
          },
          {
            "id": 6176712,
            "position": 8
          },
          {
            "id": 6142705,
            "position": 9
          },
          {
            "id": 6118369,
            "position": 10
          },
          {
            "id": 6118362,
            "position": 11
          },
          {
            "id": 6202324,
            "position": 12
          }
        ]
      },
      {
        "id": 984826,
        "name": "Ressourcen und Infographiken zum Downloaden",
        "is_published": true,
        "position": 19,
        "lectures": [
          {
            "id": 4127114,
            "position": 1
          },
          {
            "id": 5234314,
            "position": 2
          },
          {
            "id": 4127113,
            "position": 3
          },
          {
            "id": 6118694,
            "position": 4
          },
          {
            "id": 9187861,
            "position": 5
          },
          {
            "id": 8883975,
            "position": 6
          },
          {
            "id": 9187927,
            "position": 7
          },
          {
            "id": 9210584,
            "position": 8
          },
          {
            "id": 9210586,
            "position": 9
          },
          {
            "id": 9210588,
            "position": 10
          },
          {
            "id": 9553230,
            "position": 11
          },
          {
            "id": 11935207,
            "position": 12
          }
        ]
      },
      {
        "id": 1368491,
        "name": "Dokumentationen I Vorträge I Inspiration",
        "is_published": true,
        "position": 21,
        "lectures": [
          {
            "id": 5721980,
            "position": 1
          },
          {
            "id": 5721985,
            "position": 2
          },
          {
            "id": 5721988,
            "position": 3
          },
          {
            "id": 6004712,
            "position": 4
          },
          {
            "id": 6044107,
            "position": 5
          },
          {
            "id": 6202151,
            "position": 6
          },
          {
            "id": 6202176,
            "position": 7
          },
          {
            "id": 9187884,
            "position": 8
          }
        ]
      },
      {
        "id": 984812,
        "name": "Produkte und Hilfmittel",
        "is_published": true,
        "position": 18,
        "lectures": [
          {
            "id": 5358970,
            "position": 1
          },
          {
            "id": 4127092,
            "position": 2
          },
          {
            "id": 5358967,
            "position": 3
          },
          {
            "id": 5234263,
            "position": 4
          },
          {
            "id": 5234304,
            "position": 5
          },
          {
            "id": 5234268,
            "position": 6
          },
          {
            "id": 5234272,
            "position": 7
          },
          {
            "id": 5234274,
            "position": 8
          },
          {
            "id": 5234280,
            "position": 9
          },
          {
            "id": 5234306,
            "position": 10
          },
          {
            "id": 5234307,
            "position": 11
          }
        ]
      },
      {
        "id": 1458076,
        "name": "Modul 10",
        "is_published": true,
        "position": 11,
        "lectures": [
          {
            "id": 5234191,
            "position": 1
          },
          {
            "id": 8645013,
            "position": 2
          },
          {
            "id": 8873284,
            "position": 3
          },
          {
            "id": 8616141,
            "position": 4
          },
          {
            "id": 5234203,
            "position": 5
          },
          {
            "id": 8484218,
            "position": 6
          },
          {
            "id": 8728813,
            "position": 7
          },
          {
            "id": 8731686,
            "position": 8
          },
          {
            "id": 38083225,
            "position": 9
          }
        ]
      },
      {
        "id": 984811,
        "name": "Modul 6",
        "is_published": true,
        "position": 7,
        "lectures": [
          {
            "id": 5206726,
            "position": 1
          },
          {
            "id": 5206787,
            "position": 2
          },
          {
            "id": 6117502,
            "position": 3
          },
          {
            "id": 5282224,
            "position": 4
          }
        ]
      },
      {
        "id": 984813,
        "name": "Bonus-Material",
        "is_published": true,
        "position": 20,
        "lectures": [
          {
            "id": 4127094,
            "position": 1
          },
          {
            "id": 5234312,
            "position": 2
          },
          {
            "id": 5365707,
            "position": 3
          },
          {
            "id": 5365877,
            "position": 4
          },
          {
            "id": 5558479,
            "position": 5
          },
          {
            "id": 6134625,
            "position": 6
          },
          {
            "id": 9376806,
            "position": 7
          },
          {
            "id": 10443079,
            "position": 8
          }
        ]
      },
      {
        "id": 984820,
        "name": "Willkommen zur Fachausbildung zum LowCarb und Keto Coach",
        "is_published": true,
        "position": 1,
        "lectures": [
          {
            "id": 5234346,
            "position": 1
          },
          {
            "id": 5234356,
            "position": 2
          },
          {
            "id": 5234359,
            "position": 3
          },
          {
            "id": 11153313,
            "position": 4
          },
          {
            "id": 14177851,
            "position": 5
          },
          {
            "id": 5282360,
            "position": 6
          },
          {
            "id": 5282370,
            "position": 7
          },
          {
            "id": 12037710,
            "position": 8
          }
        ]
      },
      {
        "id": 1458073,
        "name": "Modul 8",
        "is_published": true,
        "position": 9,
        "lectures": [
          {
            "id": 5234185,
            "position": 1
          },
          {
            "id": 8485330,
            "position": 2
          },
          {
            "id": 8485328,
            "position": 3
          },
          {
            "id": 5234188,
            "position": 4
          },
          {
            "id": 8440144,
            "position": 5
          },
          {
            "id": 8440239,
            "position": 6
          },
          {
            "id": 8440622,
            "position": 7
          },
          {
            "id": 5234194,
            "position": 8
          }
        ]
      },
      {
        "id": 1458077,
        "name": "Modul 11",
        "is_published": true,
        "position": 12,
        "lectures": [
          {
            "id": 8616144,
            "position": 1
          },
          {
            "id": 5234222,
            "position": 2
          },
          {
            "id": 9022510,
            "position": 3
          },
          {
            "id": 6164881,
            "position": 4
          },
          {
            "id": 9060511,
            "position": 5
          },
          {
            "id": 9060555,
            "position": 6
          }
        ]
      },
      {
        "id": 1458078,
        "name": "Modul 12",
        "is_published": true,
        "position": 13,
        "lectures": [
          {
            "id": 9172679,
            "position": 1
          },
          {
            "id": 9172691,
            "position": 2
          },
          {
            "id": 9172705,
            "position": 3
          },
          {
            "id": 9172722,
            "position": 4
          },
          {
            "id": 9172730,
            "position": 5
          },
          {
            "id": 9172741,
            "position": 6
          }
        ]
      }
    ],
    "author_bio": {
      "profile_image_url": null,
      "bio": null,
      "name": "Daniela Pfeifer & Julia Tulipan",
      "user_id": 2296818
    }
  }
}