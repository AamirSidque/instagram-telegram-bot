import instaloader
import json
import os
import requests
import glob

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

L = instaloader.Instaloader(save_metadata=False, download_comments=False)

def send_photo(path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': open(path, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    r = requests.post(url, data=data, files=files)
    print("PHOTO RESPONSE:", r.text)

def send_video(path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendVideo"
    files = {'video': open(path, 'rb')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    r = requests.post(url, data=data, files=files)
    print("VIDEO RESPONSE:", r.text)

# Load actress list
with open("actresses.txt", "r") as f:
    actresses = [a.strip() for a in f.readlines() if a.strip()]

# Load posted memory
posted = {}
if os.path.exists("posted.json"):
    posted = json.load(open("posted.json"))

# Ensure media folder exists
if not os.path.exists("media"):
    os.mkdir("media")

for username in actresses:
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        post = next(profile.get_posts())
        shortcode = post.shortcode

        # skip if already processed
        if posted.get(username) == shortcode:
            print("Already posted:", username)
            continue

        caption = post.caption if post.caption else f"Update from {username}"

        # clear previous downloads
        for f in glob.glob("media/*"):
            os.remove(f)

        # download new post
        L.download_post(post, target="media")

        # find downloaded file
        media_files = glob.glob(f"media/*{shortcode}*")

        if not media_files:
            print("No media found for", username)
            continue

        media_file = [m for m in media_files if m.endswith(".mp4") or m.endswith(".jpg")]

        if not media_file:
            print("Valid media not found", username)
            continue

        media_file = media_file[0]

        if media_file.endswith(".mp4"):
            send_video(media_file, caption)
        else:
            send_photo(media_file, caption)

        posted[username] = shortcode
        json.dump(posted, open("posted.json", "w"))

    except Exception as e:
        print("Error with", username, e)
