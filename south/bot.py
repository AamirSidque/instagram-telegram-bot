import instaloader
import json
import os
import time
import glob
import requests
from requests.cookies import create_cookie


TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SESSIONID = os.getenv("IG_SESSIONID")

BATCH_SIZE = 10

# ----- LOGIN -----

L = instaloader.Instaloader(save_metadata=False, download_comments=False)

cookie = create_cookie(name="sessionid", value=SESSIONID)
L.context._session.cookies.set_cookie(cookie)

# Optional but helps stability
L.context._session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.instagram.com/",
    "X-Requested-With": "XMLHttpRequest"
})

print("Logged user:", L.test_login())


print("Logged user:", L.test_login())

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

# -------- Load Actress List --------
with open("actresses.txt") as f:
    actresses = [a.strip() for a in f.readlines() if a.strip()]

# -------- Load State --------
if os.path.exists("state.json"):
    state = json.load(open("state.json"))
else:
    state = {"batch_index": 0}

batch_index = state["batch_index"]
start = batch_index * BATCH_SIZE
end = start + BATCH_SIZE

batch = actresses[start:end]
print(f"Processing batch {batch_index+1}: {start} -> {end}")

# -------- Posted Memory --------
posted = {}
if os.path.exists("posted.json"):
    posted = json.load(open("posted.json"))

if not os.path.exists("media"):
    os.mkdir("media")

# -------- PROCESS EACH ACTRESS --------
for username in batch:
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        post = next(profile.get_posts())
        shortcode = post.shortcode
        
        # Skip duplicates
        if posted.get(username) == shortcode:
            print("No new post for", username)
            continue
        
        # Caption
        actress_name = username.replace("_", " ").title()
        post_time = post.date_utc.strftime("%d %B %Y, %I:%M %p")
        raw_caption = post.caption if post.caption else "No caption"
        
        caption = f"""Actress: {actress_name}
Caption: {raw_caption[:500]}
Time: {post_time}"""
        
        # Clear old files
        for f in glob.glob("media/*"):
            os.remove(f)

        # Download
        L.download_post(post, target="media")

        media_files = [
            f for f in glob.glob("media/*")
            if f.endswith(".jpg") or f.endswith(".mp4")
        ]
        
        if not media_files:
            print("No media found for", username)
            continue
        
        media_files.sort(key=os.path.getmtime)
        media_file = media_files[-1]

        if media_file.endswith(".mp4"):
            send_video(media_file, caption)
        else:
            send_photo(media_file, caption)

        posted[username] = shortcode
        json.dump(posted, open("posted.json", "w"))

        time.sleep(6)   # Safety delay

    except Exception as e:
        print("Error with", username, e)

# -------- Rotate Batch --------
batch_index += 1
if batch_index >= (len(actresses) // BATCH_SIZE) + 1:
    batch_index = 0

state["batch_index"] = batch_index
json.dump(state, open("state.json", "w"))

print("Next batch:", batch_index + 1)
