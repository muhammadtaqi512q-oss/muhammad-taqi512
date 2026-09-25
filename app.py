import os
import io
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__, template_folder=".")

def fetch_google_images(prompt, max_results=12):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://www.google.com/search?q={prompt}&tbm=isch"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        images = []
        
        script_tags = soup.find_all("script")
        for script in script_tags:
            if script.string and "AF_initDataCallback" in script.string:
                matches = re.findall(r'\["(https?://[^"]+)",\s*\d+,\s*\d+\]', script.string)
                for img_url in matches:
                    if not any(bad in img_url for bad in ["gstatic.com", "google.com", "googleusercontent.com"]):
                        images.append({"url": img_url, "title": prompt})
                        if len(images) >= max_results:
                            break
            if len(images) >= max_results:
                break
                
        if not images:
            for img in soup.find_all("img"):
                src = img.get("src") or img.get("data-src")
                if src and src.startswith("http") and "gstatic" not in src:
                    images.append({"url": src, "title": prompt})
                    if len(images) >= max_results:
                        break

        return images
    except Exception as e:
        print(f"Error scraping Google: {e}")
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

    images = fetch_google_images(prompt)
    if images:
        return jsonify({"success": True, "images": images})
    return jsonify({"success": False, "error": "Google se koi image nahi mili."}), 404

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
                download_name="LYRA_Google_Image.jpg"
            )
        return "Failed to fetch image from source server.", 400
    except Exception as e:
        return f"Download error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
