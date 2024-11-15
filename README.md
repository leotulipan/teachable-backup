# Download course content from Teachable platform

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