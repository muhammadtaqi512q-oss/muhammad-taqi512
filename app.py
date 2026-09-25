import os
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from duckduckgo_search import DDGS

app = Flask(__name__, template_folder=".")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def search_image():
    data = request.json or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required"}), 400

    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(prompt, max_results=12))
            if results:
                images = [{"url": r.get("image"), "title": r.get("title")} for r in results if r.get("image")]
                return jsonify({"success": True, "images": images})
            return jsonify({"success": False, "error": "No images found for this prompt."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/download", methods=["GET"])
def download_image():
    image_url = request.args.get("url")
    if not image_url:
        return "Image URL missing", 400

    try:
        res = requests.get(image_url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code == 200:
            filename = "LYRA_Image.jpg"
            return send_file(
                io.BytesIO(res.content),
                mimetype="image/jpeg",
                as_attachment=True,
                download_name=filename
            )
        return "Failed to fetch image from source server.", 400
    except Exception as e:
        return f"Download error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
