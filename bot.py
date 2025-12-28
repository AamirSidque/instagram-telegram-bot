import instaloader
import json
import os
import requests
import glob

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SESSIONID = os.getenv("IG_SESSIONID")

L = instaloader.Instaloader(
    save_metadata=False,
    download_comments=False,
    post_metadata_txt_pattern=""
)

# login bypass block
L.context._session.cookies.set("sessionid", SESSIONID)
L.context._session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

def send_photo(path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': open(path, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    print(requests.post(url, data=data, files=files).text)

def send_video(path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    files = {'video': open(path, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    print(requests.post(url, data=data, files=files).text)

# Load actresses list
with open("actresses.txt") as f:
    actresses = [a.strip() for a in f.readlines() if a.strip()]

# Load posted
posted = {}
if os.path.exists("posted.json"):
    posted = json.load(open("posted.json"))

if not os.path.exists("media"):
    os.mkdir("media")

for username in actresses:
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        post = next(profile.get_posts())
        shortcode = post.shortcode

        if posted.get(username) == shortcode:
            print("Already posted:", username)
            continue

        caption = post.caption or f"Update from {username}"

        # clear old
        for f in glob.glob("media/*"):
            os.remove(f)

        L.download_post(post, target="media")

        media_files = [
            f for f in glob.glob("media/*")
            if f.endswith(".mp4") or f.endswith(".jpg")
        ]
        
        if not media_files:
            print("No media found for", username)
            continue
        
        media_files.sort(key=os.path.getmtime)   # newest first
        media_file = media_files[-1]


        if media_file.endswith(".mp4"):
            send_video(media_file, caption)
        else:
            send_photo(media_file, caption)

        posted[username] = shortcode
        json.dump(posted, open("posted.json", "w"))

    except Exception as e:
        print("Error with", username, e)
