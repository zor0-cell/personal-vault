import os
import json
import shutil
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "vault-secret-key-change-this")

# ─── Config ──────────────────────────────────────────────────────────────────
USERNAME = os.environ.get("VAULT_USER", "NASA")
PASSWORD = os.environ.get("VAULT_PASS", "jarvis2026")
MAX_ATTEMPTS = 3
UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── Attempts tracker (in-memory) ────────────────────────────────────────────
attempt_store = {"count": 0, "wiped": False}

# ─── Auth decorator ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# ─── Auth routes ─────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    if attempt_store["wiped"]:
        return jsonify({"error": "VAULT WIPED", "wiped": True}), 403

    data = request.get_json()
    user = data.get("username", "")
    pwd = data.get("password", "")

    if user == USERNAME and pwd == PASSWORD:
        session["logged_in"] = True
        attempt_store["count"] = 0
        return jsonify({"success": True})
    else:
        attempt_store["count"] += 1
        remaining = MAX_ATTEMPTS - attempt_store["count"]

        if attempt_store["count"] >= MAX_ATTEMPTS:
            # WIPE ALL FILES
            attempt_store["wiped"] = True
            if os.path.exists(UPLOAD_FOLDER):
                shutil.rmtree(UPLOAD_FOLDER)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            return jsonify({"error": "VAULT WIPED — все файлы удалены!", "wiped": True}), 403

        return jsonify({
            "error": f"Неверные данные. Осталось попыток: {remaining}",
            "remaining": remaining
        }), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "logged_in": bool(session.get("logged_in")),
        "wiped": attempt_store["wiped"]
    })

# ─── File routes ─────────────────────────────────────────────────────────────
@app.route("/api/files", methods=["GET"])
@login_required
def list_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            # Read metadata if exists
            meta_path = filepath + ".meta"
            original_name = filename
            mime_type = "application/octet-stream"
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                    original_name = meta.get("original_name", filename)
                    mime_type = meta.get("mime_type", "application/octet-stream")
            files.append({
                "id": filename,
                "name": original_name,
                "size": stat.st_size,
                "date": stat.st_mtime * 1000,
                "type": mime_type,
            })
    files.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(files)

@app.route("/api/upload", methods=["POST"])
@login_required
def upload():
    if "files" not in request.files:
        return jsonify({"error": "No files"}), 400

    uploaded = []
    for file in request.files.getlist("files"):
        if file.filename == "":
            continue
        original_name = file.filename
        safe_name = secure_filename(original_name)
        # Make unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        stored_name = f"{timestamp}_{safe_name}"
        filepath = os.path.join(UPLOAD_FOLDER, stored_name)
        file.save(filepath)
        # Save metadata
        meta = {"original_name": original_name, "mime_type": file.content_type or "application/octet-stream"}
        with open(filepath + ".meta", "w") as f:
            json.dump(meta, f)
        uploaded.append(original_name)

    return jsonify({"success": True, "uploaded": uploaded})

@app.route("/api/files/<file_id>", methods=["DELETE"])
@login_required
def delete_file(file_id):
    # Security: only allow safe filenames
    safe_id = secure_filename(file_id)
    filepath = os.path.join(UPLOAD_FOLDER, safe_id)
    meta_path = filepath + ".meta"
    if os.path.exists(filepath):
        os.remove(filepath)
        if os.path.exists(meta_path):
            os.remove(meta_path)
        return jsonify({"success": True})
    return jsonify({"error": "File not found"}), 404

@app.route("/api/download/<file_id>")
@login_required
def download_file(file_id):
    safe_id = secure_filename(file_id)
    meta_path = os.path.join(UPLOAD_FOLDER, safe_id + ".meta")
    original_name = safe_id
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
            original_name = meta.get("original_name", safe_id)
    return send_from_directory(UPLOAD_FOLDER, safe_id, as_attachment=True, download_name=original_name)

@app.route("/api/preview/<file_id>")
@login_required
def preview_file(file_id):
    safe_id = secure_filename(file_id)
    meta_path = os.path.join(UPLOAD_FOLDER, safe_id + ".meta")
    mime = "application/octet-stream"
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
            mime = meta.get("mime_type", mime)
    return send_from_directory(UPLOAD_FOLDER, safe_id, mimetype=mime)

# ─── Serve frontend ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
