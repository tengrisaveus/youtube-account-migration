# YouTube Account Migration

A Python tool to transfer ubscriptions, playlists, and the
Watch Later list from one YouTube account to another.

## Features

- Migrates all subscriptions (full list via pagination).
- Recreates playlists along with their videos.
- Resumable / idempotent import: stops when the API quota
  runs out and continues from where it left off on the next run, without
  creating duplicates.

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Google Cloud Setup

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com).
2. Enable the **YouTube Data API v3**.
3. Configure the OAuth consent screen and add the accounts you'll use
   as **test users**.
4. Create an OAuth client of type **Desktop app**, download the JSON,
   and save it as `client_secret.json` in the project folder.

## Usage

```bash
# 1. Export from the source account (sign in with the source account)
python export.py

# 2. Fetch Watch Later (requires browser cookies)
yt-dlp --cookies cookies.txt --flat-playlist --print id \
  "https://www.youtube.com/playlist?list=WL" > watchlater_ids.txt

# 3. Import into the target account (sign in with the target account)
python import_data.py
```

If the quota runs out, simply run `import_data.py` again the next day;
it resumes from where it stopped.

## Limitations

- The YouTube Data API allows 10,000 quota units per day; write operations
  cost 50 units each, so large accounts may span several days.
- The API cannot write to Watch Later; transferred videos are collected
  in a regular playlist instead.
- Deleted or private videos are skipped.