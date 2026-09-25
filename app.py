import os
import io
import re
import requests
import urllib.parse
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__, template_folder=".")

def fetch_ai_videos(prompt, max_results=6):
    """Free public AI-generated video clips fetcher without API key"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    # AI intent add karne ke liye prompt search URL build karein
    search_query = f"{prompt} ai generated"
    encoded_query = urllib.parse.quote(search_query)
    url = f"https://www.pexels.com/search/videos/{encoded_query}/"
    
    videos = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Extract video source elements
            for video_tag in soup.find_all("video"):
                source = video_tag.find("source")
                if source and source.get("src"):
                    video_url = source.get("src")
                    # High quality mp4 link
                    if ".mp4" in video_url:
                        poster = video_tag.get("poster", "")
                        videos.append({
                            "video_url": video_url,
                            "poster": poster,
                            "title": f"AI Video: {prompt}"
                        })
                        if len(videos) >= max_results:
                            break
    except Exception as e:
        print(f"Pexels Video Scraping Error: {e}")

    # Fallback to direct Pixabay AI search if Pexels returns empty
    if not videos:
        try:
            pixabay_url = f"https://pixabay.com/videos/search/{encoded_query}/"
            res = requests.get(pixabay_url, headers=headers, timeout=10)
            if res.status_code == 200:
                matches = re.findall(r'https://cdn\.pixabay\.com/video/[^"]+\.mp4', res.text)
                unique_matches = list(set(matches))
                for v_url in unique_matches[:max_results]:
                    videos.append({
                        "video_url": v_url,
                        "poster": "",
                        "title": f"AI Generated: {prompt}"
                    })
        except Exception as e:
            print(f"Pixabay Fallback Error: {e}")

    return videos

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def search_video():
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Prompt zaroori hai"}), 400

    videos = fetch_ai_videos(prompt)
    if videos:
        return jsonify({"success": True, "videos": videos})
    
    return jsonify({"success": False, "error": "AI Videos nahi mili. Koi dusra prompt try karein."}), 404

@app.route("/api/download", methods=["GET"])
def download_video():
    video_url = request.args.get("url")
    if not video_url:
        return "Video URL missing", 400

    try:
        res = requests.get(video_url, stream=True, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        if res.status_code == 200:
            return send_file(
                io.BytesIO(res.content),
                mimetype="video/mp4",
                as_attachment=True,
                download_name="LYRA_AI_Video.mp4"
            )
        return "Video download fail ho gaya.", 400
    except Exception as e:
        return f"Download Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
