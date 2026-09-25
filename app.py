import os
import io
import urllib.parse
import requests
import yt_dlp
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder=".")

def fetch_youtube_ai_videos(prompt, max_results=4):
    """Fetch video streams directly from YouTube using yt-dlp"""
    search_query = f"{prompt} ai video generated"
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
    }
    
    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch{max_results}:{search_query}", download=False)
            
            if 'entries' in search_results:
                for entry in search_results['entries']:
                    if not entry:
                        continue
                    
                    v_id = entry.get('id')
                    title = entry.get('title', prompt)
                    
                    if v_id:
                        videos.append({
                            "video_id": v_id,
                            "embed_url": f"https://www.youtube.com/embed/{v_id}?autoplay=1&mute=1&loop=1&playlist={v_id}",
                            "watch_url": f"https://www.youtube.com/watch?v={v_id}",
                            "title": title
                        })
    except Exception as e:
        print(f"YouTube Engine Exception: {e}")

    return videos

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def search_video():
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    videos = fetch_youtube_ai_videos(prompt)
    if videos:
        return jsonify({"success": True, "videos": videos})
    
    return jsonify({"success": False, "error": "YouTube se koi video nahi mili. Please try another prompt."}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
