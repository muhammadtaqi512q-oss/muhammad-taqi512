import os
import io
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__, template_folder=".")

def fetch_images_smart(prompt, max_results=12):
    """Google Direct Scraping with Unsplash Fallback Engine"""
    images = []
    
    # 1. Try Google Scraping with Desktop Browser Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    encoded_prompt = urllib.parse.quote(prompt)
    google_url = f"https://www.google.com/search?q={encoded_prompt}&tbm=isch"
    
    try:
        res = requests.get(google_url, headers=headers, timeout=8)
        if res.status_code == 200:
            # Regular Expression to match Google's image array payload
            pattern = r'\["(https?://[^"]+\.(?:png|jpg|jpeg|webp))",\s*\d+,\s*\d+\]'
            matches = re.findall(pattern, res.text, re.IGNORECASE)
            
            for img_url in matches:
                if not any(bad in img_url for bad in ["gstatic.com", "google.com", "googleapis.com"]):
                    images.append({"url": img_url, "title": prompt})
                    if len(images) >= max_results:
                        break
                        
            # Secondary check: BeautifulSoup for standard tags if regex yields few results
            if len(images) < 4:
                soup = BeautifulSoup(res.text, "html.parser")
                for img in soup.find_all("img"):
                    src = img.get("src") or img.get("data-src")
                    if src and src.startswith("http") and "gstatic" not in src:
                        images.append({"url": src, "title": prompt})
                        if len(images) >= max_results:
                            break
    except Exception as e:
        print(f"Google fetch exception: {e}")

    # 2. Fallback to High-Resolution Unsplash Engine if Google yields nothing
    if not images:
        print("Google blocking detected. Switching to Unsplash Fallback Engine...")
        try:
            for i in range(1, max_results + 1):
                fallback_url = f"https://source.unsplash.com/featured/800x600/?{encoded_prompt}&sig={i}"
                images.append({"url": fallback_url, "title": f"{prompt} - HD Result {i}"})
        except Exception as e:
            print(f"Fallback exception: {e}")

    return images

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def search_image():
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    images = fetch_images_smart(prompt)
    if images:
        return jsonify({"success": True, "images": images})
    
    return jsonify({"success": False, "error": "Image fetch nahi ho saki. Dobara try karein."}), 404

@app.route("/api/download", methods=["GET"])
def download_image():
    image_url = request.args.get("url")
    if not image_url:
        return "Image URL missing", 400

    try:
        res = requests.get(image_url, timeout=12, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if res.status_code == 200:
            return send_file(
                io.BytesIO(res.content),
                mimetype="image/jpeg",
                as_attachment=True,
                download_name="LYRA_Image.jpg"
            )
        return "Failed to fetch image from source server.", 400
    except Exception as e:
        return f"Download error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
