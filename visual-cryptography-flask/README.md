# Visual Cryptography — Flask App

A complete Flask web app that turns any image into **two visual cryptography shares** and shows their **stacked reveal**.

## ✨ Features
- Upload PNG/JPG
- Adjustable black/white threshold
- Generates **Share 1**, **Share 2**, and **Revealed Secret**
- Download each image
- JSON API at `/api/generate` for frontend integrations

## 🧰 Setup

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open: http://127.0.0.1:5000

## 🧪 API Test
```bash
curl -X POST -F "image=@sample.png" -F "threshold=128" http://127.0.0.1:5000/api/generate
```

## 🐳 Optional: Docker
```bash
docker build -t vc-flask .
docker run -p 5000:5000 vc-flask
```

## Notes
- Output shares are **2×** width and height of the thresholded input.
- For best results use high-contrast images or logos.