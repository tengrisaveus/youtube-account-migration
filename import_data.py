# import_data.py
import json
import os
import time
from googleapiclient.errors import HttpError
from auth import get_service

PROGRESS_FILE = "progress.json"
WATCHLATER_TITLE = "Watch Later (migrated)"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "subscribed": [],
        "created_playlists": {},
        "added_videos": {},   
    }


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

class QuotaExceeded(Exception):
    pass


def is_quota_error(error: HttpError) -> bool:
    reason = ""
    try:
        reason = error.error_details[0].get("reason", "")
    except (AttributeError, IndexError, KeyError):
        pass
    return "quota" in reason.lower() or error.resp.status == 403

def import_subscriptions(yt, subscriptions, progress):
    done = set(progress["subscribed"])
    for sub in subscriptions:
        channel_id = sub["channel_id"]
        if channel_id in done:
            continue

        try:
            yt.subscriptions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": channel_id,
                        }
                    }
                },
            ).execute()
            progress["subscribed"].append(channel_id)
            save_progress(progress)
            print(f"  Subscribed: {sub['title']}")
            time.sleep(0.2)

        except HttpError as e:
            if is_quota_error(e):
                raise QuotaExceeded()
            print(f"  SKIPPED ({sub['title']}): {e.resp.status}")
            progress["subscribed"].append(channel_id)
            save_progress(progress)

def get_or_create_playlist(yt, title, description, progress):
    """Return the playlist's ID if it was already created, otherwise create it."""
    if title in progress["created_playlists"]:
        return progress["created_playlists"][title]

    response = yt.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": "private"},
        },
    ).execute()

    new_id = response["id"]
    progress["created_playlists"][title] = new_id
    save_progress(progress)
    print(f"Playlist created: {title}")
    return new_id


def add_videos_to_playlist(yt, playlist_id, title, video_ids, progress):
    already = set(progress["added_videos"].get(title, []))
    for vid in video_ids:
        if vid in already:
            continue

        try:
            yt.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": vid,
                        },
                    }
                },
            ).execute()
            progress["added_videos"].setdefault(title, []).append(vid)
            save_progress(progress)
            time.sleep(0.2)

        except HttpError as e:
            if is_quota_error(e):
                raise QuotaExceeded()
            print(f"  Video skipped ({vid}): {e.resp.status}")
            progress["added_videos"].setdefault(title, []).append(vid)
            save_progress(progress)
    print(f"  '{title}' done ({len(video_ids)} videos processed).")


def import_playlists(yt, playlists, progress):
    for pl in playlists:
        pid = get_or_create_playlist(yt, pl["title"], pl["description"], progress)
        add_videos_to_playlist(yt, pid, pl["title"], pl["videos"], progress)

def import_watchlater(yt, progress):
    if not os.path.exists("watchlater_ids.txt"):
        print("watchlater_ids.txt not found, skipping.")
        return

    ids = [l.strip() for l in open("watchlater_ids.txt", encoding="utf-16")
           if l.strip()]
    pid = get_or_create_playlist(yt, WATCHLATER_TITLE,
                                 "Watch Later migrated from the source account.",
                                 progress)
    add_videos_to_playlist(yt, pid, WATCHLATER_TITLE, ids, progress)

def main():

    yt = get_service("token_dest.json")

    with open("export.json", encoding="utf-8") as f:
        data = json.load(f)

    progress = load_progress()

    try:
        print("Importing subscriptions...")
        import_subscriptions(yt, data["subscriptions"], progress)

        print("\nImporting playlists...")
        import_playlists(yt, data["playlists"], progress)

        print("\nImporting Watch Later...")
        import_watchlater(yt, progress)

        print("\n✅ ALL DONE. Migration complete.")

    except QuotaExceeded:
        print("\n⏸️  Daily quota exhausted. Progress saved.")
        print("    Run 'python import_data.py' again tomorrow (once the quota "
              "resets); it will resume from where it stopped.")


if __name__ == "__main__":
    main()
