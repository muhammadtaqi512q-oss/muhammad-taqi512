import os
import io
import re
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__, template_folder=".")

def fetch_youtube_thumbnails(prompt, max_results=12):
    """Directly fetch YouTube video IDs and return high-res thumbnails without API key"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    encoded_prompt = urllib.parse.quote(prompt)
    youtube_url = f"https://www.youtube.com/results?search_query={encoded_prompt}"
    
    try:
        res = requests.get(youtube_url, headers=headers, timeout=10)
        if res.status_code != 200:
            return []

        # Extract Video IDs using Regex from YouTube initial payload
        video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', res.text)
        
        # Unique IDs filter
        unique_ids = []
        for v_id in video_ids:
            if v_id not in unique_ids:
                unique_ids.append(v_id)
            if len(unique_ids) >= max_results:
                break

        images = []
        for v_id in unique_ids:
            # YouTube HD Thumbnail standard URL
            thumb_url = f"https://img.youtube.com/vi/{v_id}/maxresdefault.jpg"
            images.append({
                "url": thumb_url,
                "title": f"YouTube Video: {v_id}",
                "watch_url": f"https://www.youtube.com/watch?v={v_id}"
            })

        return images
    except Exception as e:
        print(f"YouTube Fetch Error: {e}")
        return []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def search_image():
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    images = fetch_youtube_thumbnails(prompt)
    if images:
        return jsonify({"success": True, "images": images})
    
    return jsonify({"success": False, "error": "YouTube se thumbnails nahi mil sakay."}), 404

@app.route("/api/download", methods=["GET"])
def download_image():
    image_url = request.args.get("url")
    if not image_url:
        return "Image URL missing", 400

    try:
        res = requests.get(image_url, timeout=12, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # If HD thumbnail (maxresdefault) is unavailable, fallback to hqdefault
        if res.status_code != 200 and "maxresdefault" in image_url:
            fallback_url = image_url.replace("maxresdefault", "hqdefault")
            res = requests.get(fallback_url, timeout=12)

        if res.status_code == 200:
            return send_file(
                io.BytesIO(res.content),
                mimetype="image/jpeg",
                as_attachment=True,
                download_name="YouTube_Thumbnail.jpg"
            )
        return "Failed to fetch image", 400
    except Exception as e:
        return f"Download error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
