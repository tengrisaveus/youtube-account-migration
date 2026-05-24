import json
from auth import get_service

def get_all_subscriptions(yt):

    subs = []
    page_token = None

    while True:
        response = yt.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            subs.append({
                "channel_id": item["snippet"]["resourceId"]["channelId"],
                "title": item["snippet"]["title"],
            })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return subs

def get_all_playlists(yt):

    playlists = []
    page_token = None

    while True:
        response = yt.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            playlist_id = item["id"]
            playlists.append({
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "videos": get_playlist_videos(yt, playlist_id),
            })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return playlists


def get_playlist_videos(yt, playlist_id):
    
    video_ids = []
    page_token = None

    while True:
        response = yt.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return video_ids

def main():

    yt = get_service("token_source.json")
    print("Fetching subscriptions...")
    subscriptions = get_all_subscriptions(yt)
    print(f"  {len(subscriptions)} subscriptions found.")

    print("Fetching playlists...")
    playlists = get_all_playlists(yt)
    print(f"  {len(playlists)} playlists found.")

    data = {
        "subscriptions": subscriptions,
        "playlists": playlists,
    }

    with open("export.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\nDone. Data saved to 'export.json'.")

if __name__ == "__main__":
    main()
