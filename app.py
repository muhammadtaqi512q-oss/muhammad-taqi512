import os
import io
import urllib.parse
import requests
import yt_dlp
from flask import Flask, render_template, request, jsonify, send_file

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

@app.route("/api/download_yt", methods=["GET"])
def download_youtube_video():
    video_id = request.args.get("id")
    if not video_id:
        return "Video ID missing", 400

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    output_path = f"/tmp/{video_id}.mp4"

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        # Download video to local server temporary storage
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        if os.path.exists(output_path):
            return send_file(
                output_path,
                mimetype="video/mp4",
                as_attachment=True,
                download_name=f"LYRA_{video_id}.mp4"
            )
        return "Download file process failed.", 400
    except Exception as e:
        return f"Direct download error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
