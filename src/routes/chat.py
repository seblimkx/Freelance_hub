"""Chat and messaging routes"""
from flask import Blueprint, render_template, request, session, redirect, jsonify
from src.models import Profile
from src.utils.database import get_db_connection

chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/api/conversations")
def api_conversations():
    """API endpoint for floating chat window"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"conversations": []}), 401

    db = get_db_connection()
    cursor = db.cursor()

    # Get conversations where user is either buyer or seller
    conversations = cursor.execute("""
        SELECT 
            c.id AS conversation_id,
            c.buyer_id,
            c.seller_id,
            buyer.username AS buyer_username,
            seller.username AS seller_username,
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
        JOIN users buyer ON c.buyer_id = buyer.id
        JOIN users seller ON c.seller_id = seller.id
        JOIN services s ON c.service_id = s.id
        LEFT JOIN chat_messages m ON m.id = (
            SELECT id FROM chat_messages
            WHERE conversation_id = c.id
            ORDER BY timestamp DESC
            LIMIT 1
        )
        WHERE c.buyer_id = ? OR c.seller_id = ?
        ORDER BY last_timestamp DESC
        LIMIT 10
    """, (user_id, user_id, user_id)).fetchall()

    # Format conversations with proper other party name
    formatted_conversations = []
    for conv in conversations:
        formatted_conversations.append({
            "conversation_id": conv["conversation_id"],
            "other_party": conv["seller_username"] if conv["buyer_id"] == user_id else conv["buyer_username"],
            "service_title": conv["service_title"],
            "last_message": conv["last_message"],
            "last_timestamp": conv["last_timestamp"],
            "unread_count": conv["unread_count"]
        })

    cursor.close()
    db.close()

    return jsonify({"conversations": formatted_conversations})

@chat_bp.route("/api/conversation/<int:conversation_id>/messages")
def api_conversation_messages(conversation_id):
    """API endpoint to get messages for a conversation"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cursor = db.cursor()

    # Verify user is part of this conversation
    conversation = cursor.execute("""
        SELECT * FROM conversations 
        WHERE id = ? AND (buyer_id = ? OR seller_id = ?)
    """, (conversation_id, user_id, user_id)).fetchone()

    if not conversation:
        cursor.close()
        db.close()
        return jsonify({"error": "Conversation not found"}), 404

    # Mark messages as read
    cursor.execute("""
        UPDATE chat_messages
        SET is_read = 1
        WHERE conversation_id = ? AND sender_id != ?
    """, (conversation_id, user_id))
    db.commit()

    # Fetch messages
    messages = cursor.execute("""
        SELECT chat_messages.*, users.username
        FROM chat_messages
        JOIN users ON chat_messages.sender_id = users.id
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (conversation_id,)).fetchall()

    formatted_messages = [{
        "id": msg["id"],
        "message": msg["message"],
        "sender_id": msg["sender_id"],
        "username": msg["username"],
        "timestamp": msg["timestamp"]
    } for msg in messages]

    cursor.close()
    db.close()

    return jsonify({"messages": formatted_messages, "user_id": user_id})

@chat_bp.route("/api/conversation/<int:conversation_id>/send", methods=["POST"])
def api_send_message(conversation_id):
    """API endpoint to send a message"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    message = request.form.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    # Verify user is part of this conversation
    conversation = cursor.execute("""
        SELECT * FROM conversations 
        WHERE id = ? AND (buyer_id = ? OR seller_id = ?)
    """, (conversation_id, user_id, user_id)).fetchone()

    if not conversation:
        cursor.close()
        db.close()
        return jsonify({"error": "Conversation not found"}), 404

    # Insert message
    cursor.execute("""
        INSERT INTO chat_messages (conversation_id, sender_id, message)
        VALUES (?, ?, ?)
    """, (conversation_id, user_id, message))

    # Determine recipient for notification
    recipient_id = conversation["seller_id"] if user_id == conversation["buyer_id"] else conversation["buyer_id"]

    # Insert notification
    cursor.execute("""
        INSERT INTO notifications (user_id, message)
        VALUES (?, ?)
    """, (recipient_id, f"New message from {session['username']}"))

    db.commit()
    cursor.close()
    db.close()

    return jsonify({"success": True})

@chat_bp.route("/inbox")
def inbox():
    """General inbox for both buyers and sellers"""
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor()

    # Get conversations where user is either buyer or seller
    conversations = cursor.execute("""
        SELECT 
            c.id AS conversation_id,
            c.buyer_id,
            c.seller_id,
            buyer.username AS buyer_username,
            seller.username AS seller_username,
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
        JOIN users buyer ON c.buyer_id = buyer.id
        JOIN users seller ON c.seller_id = seller.id
        JOIN services s ON c.service_id = s.id
        LEFT JOIN chat_messages m ON m.id = (
            SELECT id FROM chat_messages
            WHERE conversation_id = c.id
            ORDER BY timestamp DESC
            LIMIT 1
        )
        WHERE c.buyer_id = ? OR c.seller_id = ?
        ORDER BY last_timestamp DESC
    """, (user_id, user_id, user_id)).fetchall()

    # Format conversations with proper other party name
    formatted_conversations = []
    for conv in conversations:
        formatted_conversations.append({
            "conversation_id": conv["conversation_id"],
            "other_party": conv["seller_username"] if conv["buyer_id"] == user_id else conv["buyer_username"],
            "service_title": conv["service_title"],
            "last_message": conv["last_message"],
            "last_timestamp": conv["last_timestamp"],
            "unread_count": conv["unread_count"]
        })

    total_unread = sum(c["unread_count"] for c in formatted_conversations)

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
        "inbox.html",
        conversations=formatted_conversations,
        total_unread=total_unread,
        profile=user_profile
    )

@chat_bp.route("/chat/<int:service_id>")
def chat(service_id):
    user_id = session.get("user_id")
    if user_id is None:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor()

    # Get the service and seller
    service = cursor.execute("""
        SELECT services.*, users.username AS seller_name, users.id AS seller_id
        FROM services
        JOIN users ON services.user_id = users.id
        WHERE services.id = ?
    """, (service_id,)).fetchone()

    if not service:
        return "Service not found", 404

    seller_id = service["seller_id"]
    buyer_id = user_id

    # Try to find existing conversation
    conversation = cursor.execute("""
        SELECT * FROM conversations
        WHERE service_id = ? AND buyer_id = ?
    """, (service_id, buyer_id)).fetchone()

    # If no conversation exists, create one
    if conversation is None:
        cursor.execute("""
            INSERT INTO conversations (service_id, buyer_id, seller_id)
            VALUES (?, ?, ?)
        """, (service_id, buyer_id, seller_id))
        db.commit()

        conversation = cursor.execute("""
            SELECT * FROM conversations
            WHERE service_id = ? AND buyer_id = ?
        """, (service_id, buyer_id)).fetchone()

    conversation_id = conversation["id"]

    # Fetch messages
    messages = cursor.execute("""
        SELECT chat_messages.*, users.username
        FROM chat_messages
        JOIN users ON chat_messages.sender_id = users.id
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (conversation_id,)).fetchall()
    cursor.close()
    db.close()

    service_data = {
        "id": service["id"], 
        "title": service["title"], 
        "description": service["description"], 
        "price": service["price"], 
        "seller": service["seller_name"], 
        "image_url": service["image_url"] or "/static/default_image.png"
    }
    user_profile = Profile(session["username"], session["profile_type"], None, 
                          session["user_id"], resume=session.get("resume", ""))
    
    return render_template("chat.html", 
                           service=service_data, 
                           profile=user_profile,
                           conversation_id=conversation_id, 
                           messages=messages)

@chat_bp.route("/chat/convo/<int:conversation_id>")
def chat_conversation(conversation_id):
    user_id = session.get("user_id")
    if user_id is None:
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor()

    # Check conversation exists
    conversation = cursor.execute("""
        SELECT * FROM conversations WHERE id = ?
    """, (conversation_id,)).fetchone()

    if not conversation:
        return "Conversation not found", 404

    # Mark messages as read for this user
    cursor.execute("""
        UPDATE chat_messages
        SET is_read = 1
        WHERE conversation_id = ?
        AND sender_id != ?
    """, (conversation_id, user_id))
    db.commit()

    # Load service
    service = cursor.execute("""
        SELECT services.*, users.username AS seller_name
        FROM services
        JOIN users ON services.user_id = users.id
        WHERE services.id = ?
    """, (conversation["service_id"],)).fetchone()

    # Load messages
    messages = cursor.execute("""
        SELECT chat_messages.*, users.username
        FROM chat_messages
        JOIN users ON chat_messages.sender_id = users.id
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (conversation_id,)).fetchall()

    service_data = {
        "id": service["id"],
        "title": service["title"],
        "description": service["description"],
        "price": service["price"],
        "seller": service["seller_name"],
        "image_url": service["image_url"] or "/static/default_image.png"
    }
    profile_type = session["profile_type"]
    user_profile = Profile(
        session["username"],
        session["profile_type"],
        None,
        session["user_id"],
        resume=session.get("resume", "")
    )
    cursor.close()
    db.close()

    return render_template("chat.html",
                           service=service_data,
                           profile=user_profile,
                           conversation_id=conversation_id,
                           messages=messages,
                           profile_type=profile_type)

@chat_bp.route("/send_message/<int:conversation_id>", methods=["POST"])
def send_msg(conversation_id):
    user_id = session.get("user_id")
    if user_id is None:
        return "Unauthorized", 403

    msg = request.form.get("message", "").strip()
    if msg == "":
        return redirect(f"/chat/{conversation_id}")

    db = get_db_connection()
    cursor = db.cursor()

    conv = cursor.execute("""
        SELECT * FROM conversations 
        WHERE id=? AND (buyer_id=? OR seller_id=?)
    """, (conversation_id, user_id, user_id)).fetchone()

    if conv is None:
        return "Unauthorized", 403

    cursor.execute("""
        INSERT INTO chat_messages (conversation_id, sender_id, message)
        VALUES (?, ?, ?)
    """, (conversation_id, user_id, msg))

    # Determine who to notify
    recipient_id = conv["seller_id"] if user_id == conv["buyer_id"] else conv["buyer_id"]

    # Insert notification
    cursor.execute("""
        INSERT INTO notifications (user_id, message)
        VALUES (?, ?)
    """, (recipient_id, f"New message from {session['username']}"))

    db.commit()

    service_id = conv["service_id"]
    cursor.close()
    db.close()

    return redirect(f"/chat/{service_id}")
