import instaloader
import json
import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

L = instaloader.Instaloader(save_metadata=False, download_comments=False)

def send_photo(path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': open(path, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(url, data=data, files=files)

def send_video(path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    files = {'video': open(path, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(url, data=data, files=files)

with open("actresses.txt", "r") as f:
    actresses = [a.strip() for a in f.readlines() if a.strip()]

if os.path.exists("posted.json"):
    posted = json.load(open("posted.json"))
else:
    posted = {}

for username in actresses:
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        post = next(profile.get_posts())
        shortcode = post.shortcode

        if posted.get(username) == shortcode:
            continue

        caption = post.caption if post.caption else f"Update from {username}"
        filename = f"{username}_{shortcode}"

        L.download_post(post, target="media")

        for file in os.listdir("media"):
            if shortcode in file:
                media_path = os.path.join("media", file)

        if post.is_video:
            send_video(media_path, caption)
        else:
            send_photo(media_path, caption)

        posted[username] = shortcode
        json.dump(posted, open("posted.json", "w"))

    except Exception as e:
        print("Error:", username, e)
