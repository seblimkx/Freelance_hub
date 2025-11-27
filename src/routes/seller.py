"""Seller-related routes"""
from flask import Blueprint, render_template, request, session, redirect
from src.models import Profile, freelance_post
from src.utils.database import get_db_connection
from src.config import SERVICE_TAGS
import os
from werkzeug.utils import secure_filename

seller_bp = Blueprint('seller', __name__)

@seller_bp.route("/seller", methods=["GET", "POST"])
def seller():
    db = get_db_connection()
    cursor = db.cursor()

    # Fetch current user's resume
    user_row = cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    # Fetch unread message count for this seller
    total_unread = cursor.execute("""
        SELECT COUNT(*)
        FROM chat_messages
        JOIN conversations ON chat_messages.conversation_id = conversations.id
        WHERE conversations.seller_id = ?
        AND chat_messages.sender_id != ?
        AND chat_messages.is_read = 0
    """, (session["user_id"], session["user_id"])).fetchone()[0]

    # Fetch the seller's services + include resume via JOIN
    user_tasks = cursor.execute("""
        SELECT services.id, services.title, services.description, 
               services.price, services.image_url, users.resume, users.username
        FROM services
        JOIN users ON services.user_id = users.id
        WHERE services.user_id = ?
    """, (session["user_id"],)).fetchall()

    user_posts = [
        freelance_post(
            row["title"],
            row["description"],
            row["price"],
            row["id"],
            row["resume"],
            row["username"], 
            row["image_url"]
        )
        for row in user_tasks
    ]

    session["profile_type"] = "seller"
    user_profile = Profile(
        username=session["username"],
        profile_type=session["profile_type"],
        password=None,
        id=session["user_id"],
        resume=user_row["resume"]
    )
    
    cursor.close()
    db.close()

    return render_template(
        "mainpage_seller.html",
        services=user_posts,
        profile=user_profile,
        tags=SERVICE_TAGS,
        total_unread=total_unread,
    )

@seller_bp.route("/add_service", methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        tag = request.form.get("tag", "Other")  # Default to "Other" if not provided
        
        # Handle image upload
        image_url = None
        if 'service_image' in request.files:
            file = request.files['service_image']
            if file and file.filename:
                # Create uploads directory if it doesn't exist
                upload_folder = 'static/uploads'
                os.makedirs(upload_folder, exist_ok=True)
                
                # Generate unique filename
                filename = secure_filename(file.filename)
                timestamp = str(int(__import__('time').time()))
                unique_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(upload_folder, unique_filename)
                
                # Save file
                file.save(filepath)
                image_url = f"/{filepath}"
        
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("INSERT INTO services (title, description, price, user_id, tag, image_url) VALUES (?, ?, ?, ?, ?, ?)", 
                      (title, description, price, session["user_id"], tag, image_url))
        db.commit()
        cursor.close()
        db.close()

        return redirect("/seller")
        db.close()

        return render_template("mainpage_seller.html", services=user_posts, profile=user_profile, tags=SERVICE_TAGS)

@seller_bp.route("/edit_service", methods=["GET", "POST"])
def edit_service():
    service_id = request.form.get("service_id")
    title = request.form.get("title")
    description = request.form.get("description")
    price = request.form.get("price")
    
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("UPDATE services SET title = ?, description = ?, price = ? WHERE user_id = ? AND id = ?", 
                  (title, description, price, session["user_id"], service_id))
    db.commit()

    user_tasks = cursor.execute("""SELECT services.id, services.title, services.description, services.price, 
                                  services.image_url, users.resume, users.username FROM services
                                  JOIN users ON services.user_id = users.id
                                  WHERE services.user_id = ?""", (session["user_id"],)).fetchall()
    user_posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], 
                                row["resume"], row["username"], row["image_url"]) for row in user_tasks]

    user_profile = Profile(session["username"], session["profile_type"], None, 
                          session["user_id"], resume=session.get("resume", ""))
    cursor.close()
    db.close()

    return render_template("mainpage_seller.html", services=user_posts, profile=user_profile, tags=SERVICE_TAGS)

@seller_bp.route("/delete_service", methods=["GET", "POST"])
def delete_service():
    service_id = request.form.get("service_id")
    
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM services WHERE id = ? AND user_id = ?", (service_id, session["user_id"]))
    db.commit()

    user_tasks = cursor.execute("""SELECT services.id, services.title, services.description, services.price, 
                                  services.image_url, users.resume, users.username FROM services
                                  JOIN users ON services.user_id = users.id
                                  WHERE services.user_id = ?""", (session["user_id"],)).fetchall()
    user_posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], 
                                row["resume"], row["username"], row["image_url"]) for row in user_tasks]

    user_profile = Profile(session["username"], session["profile_type"], None, 
                          session["user_id"], resume=session.get("resume", ""))
    cursor.close()
    db.close()
    
    return render_template("mainpage_seller.html", services=user_posts, profile=user_profile, tags=SERVICE_TAGS)

@seller_bp.route("/seller/inbox")
def seller_inbox():
    db = get_db_connection()
    cursor = db.cursor()

    seller_id = session.get("user_id")
    if not seller_id:
        return redirect("/login")

    conversations = cursor.execute("""
        SELECT 
            c.id AS conversation_id,
            u.username AS buyer_username,
            s.title AS service_title,
            m.message AS last_message,
            m.timestamp AS last_timestamp,
            (
                SELECT COUNT(*) 
                FROM chat_messages 
                WHERE conversation_id = c.id
                AND sender_id != ?
                AND is_read = 0
            ) AS unread_count
        FROM conversations c
        JOIN users u ON c.buyer_id = u.id
        JOIN services s ON c.service_id = s.id
        LEFT JOIN chat_messages m ON m.id = (
            SELECT id FROM chat_messages
            WHERE conversation_id = c.id
            ORDER BY timestamp DESC
            LIMIT 1
        )
        WHERE c.seller_id = ?
        ORDER BY last_timestamp DESC
    """, (seller_id, seller_id)).fetchall()

    total_unread = sum(c["unread_count"] for c in conversations)

    user_profile = Profile(
        session["username"],
        session["profile_type"],
        None,
        session["user_id"],
        resume=session.get("resume", "")
    )
    
    cursor.close()
    db.close()

    return render_template(
        "seller_inbox.html",
        conversations=conversations,
        total_unread=total_unread,
        profile=user_profile
    )
