import os
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
import requests

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")
TIMEOUT = (3.05, 30)

def error_message(response):
    try: return response.json().get("detail", response.text)
    except ValueError: return response.text or f"HTTP {response.status_code}"

@app.get("/healthz")
def healthz(): return {"status": "ok"}

@app.get("/")
def index():
    params = {"q": request.args.get("q", ""), "category": request.args.get("category", "")}
    try:
        response = requests.get(f"{BACKEND_URL}/api/documents", params=params, timeout=TIMEOUT); response.raise_for_status()
        documents = response.json()
    except requests.RequestException as exc:
        app.logger.exception("Backend request failed"); flash(f"Could not load documents: {exc}", "danger"); documents = []
    return render_template("index.html", documents=documents, q=params["q"], category=params["category"])

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET": return render_template("upload.html")
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Choose a file.", "warning"); return redirect(url_for("upload"))
    data = {"title": request.form.get("title", ""), "category": request.form.get("category", "")}
    try:
        response = requests.post(f"{BACKEND_URL}/api/documents/upload", data=data,
            files={"file": (uploaded.filename, uploaded.stream, uploaded.mimetype)}, timeout=(3.05, 60))
        if response.ok: flash("Document uploaded.", "success"); return redirect(url_for("index"))
        flash(error_message(response), "danger")
    except requests.RequestException as exc: flash(f"Upload failed: {exc}", "danger")
    return redirect(url_for("upload"))

@app.get("/documents/<int:document_id>/download")
def download(document_id):
    try:
        response = requests.get(f"{BACKEND_URL}/api/documents/{document_id}/download", stream=True, timeout=(3.05, 60)); response.raise_for_status()
        disposition = response.headers.get("Content-Disposition", "")
        filename = disposition.split("filename=")[-1].strip('"') if "filename=" in disposition else f"document-{document_id}"
        return send_file(response.raw, mimetype=response.headers.get("Content-Type"), as_attachment=True, download_name=filename)
    except requests.RequestException as exc: flash(f"Download failed: {exc}", "danger"); return redirect(url_for("index"))

@app.post("/documents/<int:document_id>/delete")
def delete(document_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/documents/{document_id}", timeout=TIMEOUT)
        if response.status_code == 204: flash("Document deleted.", "success")
        else: flash(error_message(response), "danger")
    except requests.RequestException as exc: flash(f"Delete failed: {exc}", "danger")
    return redirect(url_for("index"))
