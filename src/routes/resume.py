"""Resume upload and management routes"""
from flask import Blueprint, render_template, request, session, flash, url_for, redirect
from werkzeug.utils import secure_filename
import PyPDF2
import os
from src.models import Profile
from src.utils.database import get_db_connection

resume_bp = Blueprint('resume', __name__)

ALLOWED_EXTENSIONS = {"pdf", "txt"}
UPLOAD_FOLDER = "static/uploads"

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@resume_bp.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():
    if request.method == "POST":
        resume_text = request.form.get("resume_text", "").strip()
        resume_file = request.files.get("resume_file")

        extracted_text = ""

        if resume_file:
            filename = secure_filename(resume_file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            resume_file.save(filepath)

            ext = filename.rsplit(".", 1)[1].lower()
            if ext == "pdf":
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        extracted_text += page.extract_text() or ""

            elif ext == "txt":
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_text = f.read()

        elif resume_text:
            extracted_text = resume_text

        elif not resume_text and not resume_file:
            flash("Please upload a file or paste your resume text.", "warning")
            return redirect(url_for("resume.upload_resume"))
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET resume = ? WHERE id = ?", 
                      (extracted_text, session["user_id"]))
        db.commit()

        session["resume"] = extracted_text
        user_profile = Profile(
            username=session["username"],
            profile_type=session["profile_type"],
            password=None,
            id=session["user_id"],
            resume=session["resume"]
        )

        total_unread = cursor.execute("""
            SELECT COUNT(*)
            FROM chat_messages
            JOIN conversations ON chat_messages.conversation_id = conversations.id
            WHERE conversations.seller_id = ?
            AND chat_messages.sender_id != ?
            AND chat_messages.is_read = 0
        """, (session["user_id"], session["user_id"])).fetchone()[0]
        
        cursor.close()
        db.close()

        return render_template("mainpage_seller.html", profile=user_profile, total_unread=total_unread)

    else:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT resume FROM users WHERE id = ?", (session["user_id"],))
        row = cursor.fetchone()
        resume_value = row["resume"] if row and row["resume"] else ""
        cursor.close()
        db.close()

        user_profile = Profile(
            session["username"],
            session["profile_type"],
            None,
            session["user_id"],
            resume_value
        )

        return render_template("upload_resume.html", profile=user_profile)
