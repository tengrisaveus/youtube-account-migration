from auth import get_service

yt = get_service("token_source.json")
me = yt.channels().list(part="snippet", mine=True).execute()
print("Connected channel:", me["items"][0]["snippet"]["title"])