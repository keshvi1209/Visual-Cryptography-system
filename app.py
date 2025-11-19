import io
import base64
import random
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import numpy as np

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB upload limit


# ================================
# COLOR VISUAL CRYPTOGRAPHY LOGIC
# ================================

def generate_color_shares(img):
    """
    Generate two visual cryptography color shares using XOR.
    Share1 = random noise
    Share2 = Share1 XOR OriginalImage
    Stacked = Share1 XOR Share2 = Original image
    """
    img = img.convert("RGB")
    arr = np.array(img, dtype=np.uint8)

    height, width, _ = arr.shape

    # random noise
    share1 = np.random.randint(0, 256, size=(height, width, 3), dtype=np.uint8)

    # XOR with original to create share2
    share2 = np.bitwise_xor(arr, share1)

    # stacking produces original
    stacked = np.bitwise_xor(share1, share2)

    return share1, share2, stacked


def merge_two_shares_color(img1, img2):
    """
    Reconstruct original colored image from two shares using XOR.
    """
    arr1 = np.array(img1.convert("RGB"), dtype=np.uint8)
    arr2 = np.array(img2.convert("RGB"), dtype=np.uint8)

    if arr1.shape != arr2.shape:
        raise ValueError("Share sizes do not match.")

    stacked = np.bitwise_xor(arr1, arr2)
    return stacked


def arr_to_b64_png(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ================================
# ROUTES
# ================================

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
        img.thumbnail((600, 600))
    except Exception:
        flash("Invalid image format. Try PNG/JPG.")
        return redirect(url_for("index"))

    # ORIGINAL IMAGE
    original_b64 = arr_to_b64_png(np.array(img))

    # Create color shares
    s1, s2, stacked = generate_color_shares(img)

    # Convert to base64
    s1_b64 = arr_to_b64_png(s1)
    s2_b64 = arr_to_b64_png(s2)
    stacked_b64 = arr_to_b64_png(stacked)

    return render_template(
        "result.html",
        original=original_b64,
        share1=s1_b64,
        share2=s2_b64,
        stacked=stacked_b64
    )
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")
@app.route("/merge", methods=["GET", "POST"])
def merge():
    if request.method == "GET":
        return render_template("merge.html")

    if "share1" not in request.files or "share2" not in request.files:
        flash("Upload both share images.")
        return redirect(url_for("merge"))

    s1 = request.files["share1"]
    s2 = request.files["share2"]

    try:
        img1 = Image.open(s1.stream)
        img2 = Image.open(s2.stream)
    except:
        flash("Invalid share images.")
        return redirect(url_for("merge"))

    try:
        stacked = merge_two_shares_color(img1, img2)
    except Exception as e:
        flash(str(e))
        return redirect(url_for("merge"))

    stacked_b64 = arr_to_b64_png(stacked)

    return render_template("merge_result.html", stacked=stacked_b64)


if __name__ == "__main__":
    app.run(debug=True)
