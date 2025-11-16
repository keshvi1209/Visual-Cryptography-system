import io
import base64
import random
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import numpy as np

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me")  # needed for flash messages
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB upload limit

def to_bw(img, threshold=128):
    """Convert input image to strict black/white (0 or 255)."""
    # Convert to grayscale, then threshold
    gray = img.convert("L")
    arr = np.array(gray, dtype=np.uint8)
    bw = (arr > threshold).astype(np.uint8) * 255
    return bw

def generate_shares_from_bw(bw_arr):
    """Generate two VC shares and the stacked result from a 0/255 numpy array."""
    height, width = bw_arr.shape
    patterns = [
        np.array([[0, 255], [255, 0]], dtype=np.uint8),
        np.array([[255, 0], [0, 255]], dtype=np.uint8),
    ]

    share1 = np.zeros((height * 2, width * 2), dtype=np.uint8)
    share2 = np.zeros((height * 2, width * 2), dtype=np.uint8)

    for i in range(height):
        for j in range(width):
            pixel = bw_arr[i, j]
            pat = random.choice(patterns)
            # Debug logging
            try:
                if pixel == 255:  # white pixel -> complementary patterns
                    share1[i*2:i*2+2, j*2:j*2+2] = pat
                    share2[i*2:i*2+2, j*2:j*2+2] = 255 - pat
                else:  # black pixel -> same pattern
                    share1[i*2:i*2+2, j*2:j*2+2] = pat
                    share2[i*2:i*2+2, j*2:j*2+2] = pat
            except Exception as e:
                print(f"Error at i={i}, j={j}: {e}")
                raise

    stacked = np.minimum(share1, share2)
    return share1, share2, stacked

def arr_to_b64_png(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        flash("Please choose an image to upload.")
        return redirect(url_for("index"))
    file = request.files["image"]
    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    try:
        img = Image.open(file.stream)
        img.thumbnail((500, 500))
    except Exception:
        flash("Could not open image. Try PNG or JPG.")
        return redirect(url_for("index"))

    threshold = request.form.get("threshold", type=int) or 128
    # convert to pure B/W
    bw = to_bw(img, threshold=threshold)
    try:
        s1, s2, stacked = generate_shares_from_bw(bw)
    except Exception as e:
        print(f"Error in generate_shares_from_bw: {e}")
        flash("Internal error during share generation.")
        return redirect(url_for("index"))

    # Encode all images to base64 for embedding
    bw_b64 = arr_to_b64_png(bw)
    s1_b64 = arr_to_b64_png(s1)
    s2_b64 = arr_to_b64_png(s2)
    stacked_b64 = arr_to_b64_png(stacked)

    return render_template(
        "result.html",
        original=bw_b64,
        share1=s1_b64,
        share2=s2_b64,
        stacked=stacked_b64,
        width=bw.shape[1],
        height=bw.shape[0],
        threshold=threshold
    )

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """JSON API: returns base64 images for frontend apps (e.g., React)."""
    if "image" not in request.files:
        return {"error": "image field required"}, 400

    file = request.files["image"]
    try:
        img = Image.open(file.stream)
    except Exception:
        return {"error": "invalid image"}, 400

    threshold = int(request.form.get("threshold", 128))
    bw = to_bw(img, threshold=threshold)
    s1, s2, stacked = generate_shares_from_bw(bw)

    return {
        "original": arr_to_b64_png(bw),
        "share1": arr_to_b64_png(s1),
        "share2": arr_to_b64_png(s2),
        "stacked": arr_to_b64_png(stacked),
        "meta": {"width": int(bw.shape[1]), "height": int(bw.shape[0]), "threshold": threshold}
    }

if __name__ == "__main__":
    app.run(debug=True)