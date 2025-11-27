from flask import Flask, redirect, render_template, request, session, flash, url_for
from flask_session import Session
from search_algo import SearchQuery, freelance_post
from user_profile import Profile
import sqlite3
import os
from werkzeug.utils import secure_filename
import PyPDF2
import json
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
from dotenv import load_dotenv

UPLOAD_FOLDER = "static/uploads"

load_dotenv()
app = Flask(__name__)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Generate a secure secret key if not in environment
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

app.config["SESSION_PERMANENT"] = True
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(app.root_path, "flask_session")
Session(app) 

#ensuring flask updates every time after reload
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

def get_db_connection():
    conn = sqlite3.connect("project.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

SERVICE_TAGS = [
    "Web Development",
    "Graphic Design",
    "Tutoring",
    "Electrical",
    "Translation",
    "Writing",
    "Photography",
    "Video Editing",
    "Marketing",
    "AI & Data",
]

@app.route("/", methods=["GET"])
def home():
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")
        password_confirm = request.form.get("confirmation")

        db = get_db_connection()
        cursor = db.cursor()

        if not name:
            return render_template("error.html", error = "Please enter name")
        
        if not password:
            return render_template("error.html", error = "Please enter password")
        
        if not password_confirm:
            return render_template("error.html", error = "Please confirm password")
        
        if password != password_confirm:
            return render_template("error.html", error="Passwords do not match")
        
        rows = cursor.execute("SELECT username FROM users").fetchall()
        name_list = [row[0] for row in rows]

        if name in name_list:
            return render_template("error.html", error = "Name is taken")
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha512')
        
        cursor.execute("INSERT INTO users (username, password, is_buyer, is_seller) VALUES (?, ?, ?, ?)", (name, hashed_password, 1, 0))
        db.commit()

        # Create user session
        rows = cursor.execute("SELECT * FROM users WHERE username = ?", (name,)).fetchall()
        user_profile = Profile(name, "buyer", rows[0]["password"], rows[0]["id"], resume=rows[0]["resume"])
        session["user_id"] = rows[0]["id"]
        session["username"] = name
        session["profile_type"] = user_profile.profile_type
        session["password"] = user_profile.password
        session["resume"] = user_profile.resume

        services = cursor.execute("""SELECT services.id, services.title, services.description, services.price, services.image_url,
                                users.resume, users.username FROM services
                                JOIN users ON services.user_id = users.id""").fetchall()
        posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], row["resume"], row["username"], row["image_url"]) for row in services]
        cursor.close()
        db.close()

        return render_template("/mainpage_buyer.html", items = posts, profile = user_profile, tags = SERVICE_TAGS)
    else:
        return render_template("register.html")

@app.route("/set_preferences", methods=["GET", "POST"])
def set_preferences():
    selected_tags = request.form.get("selected_tags", "[]")
    
    try:
        preferences = json.loads(selected_tags)
    except Exception:
        preferences = []

    preferences_str = json.dumps(preferences)
    # print(preferences_str)

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET preferences = ? WHERE id = ?", (preferences_str, session["user_id"]))
    db.commit()

    return redirect(("/buyer"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")

        if not name:
            return render_template("error.html", error = "Please enter name")
        
        if not password:
            return render_template("error.html", error = "Please enter password")
        
        db = get_db_connection()
        cursor = db.cursor()

        user = cursor.execute("SELECT * FROM users WHERE username = ?", (name,)).fetchone()

        if not user or not check_password_hash(user["password"], password):
            cursor.close()
            db.close()
            return render_template("error.html", error="Invalid username or password")

        services = cursor.execute("""SELECT services.id, services.title, services.description, services.price, services.image_url,
                                users.resume, users.username FROM services
                                JOIN users ON services.user_id = users.id""").fetchall()
        posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], row["resume"], row["username"], row["image_url"]) for row in services]

        session["user_id"] = user["id"]
        session["username"] = name

        if user["is_buyer"] == 1:
            user_profile = Profile(name, "buyer", user["password"], user["id"], resume=user["resume"])
            session["profile_type"] = user_profile.profile_type
            session["password"] = user_profile.password
            session["resume"] = user_profile.resume

        if user["is_seller"] == 1:
            user_profile = Profile(name, "seller", user["password"], user["id"], resume=user["resume"])
            session["profile_type"] = user_profile.profile_type
            session["password"] = user_profile.password
            session["resume"] = user_profile.resume

        cursor.close()
        db.close()
        if user_profile.is_buyer():
            return redirect(("/buyer"))
        
        if user_profile.is_seller():
            return render_template("/mainpage_buyer.html", items = posts, profile = user_profile, tags = SERVICE_TAGS)   
    else:
        return render_template("login.html")

def recommend(posts):
    db = get_db_connection()
    cursor = db.cursor()
    row = cursor.execute("SELECT preferences FROM users WHERE id = ?", (session["user_id"], )).fetchone()
    preferences = json.loads(row["preferences"]) if row and row["preferences"] else []
    cursor.close()
    db.close()
    
    engine = SearchQuery(posts)

    if preferences:
        query = " ".join(preferences)
        results = engine.search(query)
        items_ranked = [item for item, score in results]
    else:
        items_ranked = posts

    return items_ranked

@app.route("/buyer", methods=["GET"])
def buyer():
    db = get_db_connection()
    cursor = db.cursor()
    user_id = session["user_id"]

    user_profile = Profile(session["username"], session["profile_type"], None, session["user_id"], resume=session.get("resume", ""))
    services = cursor.execute("""
        SELECT services.id, services.title, services.description, services.price, services.image_url,
               users.resume, users.username
        FROM services
        JOIN users ON services.user_id = users.id
        WHERE services.user_id != ?
    """, (user_id,)).fetchall()
    posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], row["resume"], row["username"], row["image_url"]) for row in services]
    ranked_items = recommend(posts)

    cursor.close()
    db.close()

    session["profile_type"] = "buyer"
    return render_template("mainpage_buyer.html", items = ranked_items, profile = user_profile, tags = SERVICE_TAGS)

@app.route("/seller", methods=["GET", "POST"])
def seller():
    db = get_db_connection()
    cursor = db.cursor()

    # Fetch current user's resume
    user_row = cursor.execute(
        "SELECT * FROM users WHERE id = ?", 
        (session["user_id"],)
    ).fetchone()

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
        resume=user_row["resume"]   # <- explicitly as keyword
    )

    return render_template(
        "mainpage_seller.html",
        services=user_posts,
        profile=user_profile,
        tags=SERVICE_TAGS,
        total_unread=total_unread,     
    )

    
@app.route("/search", methods=["GET", "POST"])
def search():
    db = get_db_connection()
    cursor = db.cursor()
    services = cursor.execute("""SELECT services.id, services.title, services.description, services.price, services.image_url,
                            users.resume, users.username FROM services
                            JOIN users ON services.user_id = users.id""").fetchall()
    posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], row["resume"], row["username"], row["image_url"]) for row in services]
    engine = SearchQuery(posts)
    query = request.args.get("query")

    if query:
        results = engine.search(query)
        items_ranked = [item for item, score in results]
    else:
        items_ranked = posts

    user_profile = Profile(session["username"],session["profile_type"], None, session["user_id"], resume=session.get("resume", ""))
    cursor.close()
    db.close()

    return render_template("mainpage_buyer.html", items = items_ranked, profile = user_profile, tags = SERVICE_TAGS)

@app.route("/add_service", methods=["GET", "POST"])
def add_service():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        price = request.form.get("price")
        tag = request.form["tag"]
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("INSERT INTO services (title, description, price, user_id, tag) VALUES (?, ?, ?, ?, ?)", (title, description, price, session["user_id"], tag))
        db.commit()

        user_tasks = cursor.execute("""SELECT services.id, services.title, services.description, services.price, services.image_url,
                                    users.resume, users.username FROM services
                                    JOIN users ON services.user_id = users.id
                                    WHERE services.user_id = ?""", (session["user_id"],)).fetchall()
        user_posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], row["resume"], row["username"], row["image_url"]) for row in user_tasks]

        user_profile = Profile(session["username"],session["profile_type"], None, session["user_id"], resume=session.get("resume", ""))
        cursor.close()
        db.close()

        return render_template("mainpage_seller.html", services = user_posts, profile = user_profile, tags = SERVICE_TAGS)  

@app.route("/edit_service", methods=["GET", "POST"])
def edit_service():
    service_id = request.form.get("service_id")
    title = request.form.get("title")
    description = request.form.get("description")
    price = request.form.get("price")
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("UPDATE services SET title = ?, description = ?, price = ? WHERE user_id = ? AND id = ?", (title, description, price, session["user_id"], service_id))
    db.commit()

    user_tasks = cursor.execute("""SELECT services.id, services.title, services.description, services.price, services.image_url,
                                users.resume, users.username FROM services
                                JOIN users ON services.user_id = users.id
                                WHERE services.user_id = ?""", (session["user_id"],)).fetchall()
    user_posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], row["resume"], row["username"], row["image_url"]) for row in user_tasks]

    user_profile = Profile(session["username"],session["profile_type"], None, session["user_id"], resume=session.get("resume", ""))
    cursor.close()
    db.close()

    return render_template("mainpage_seller.html", services = user_posts, profile = user_profile, tags = SERVICE_TAGS)  

@app.route("/delete_service", methods=["GET", "POST"])
def delete_service():
        service_id = request.form.get("service_id")
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("DELETE FROM services WHERE id = ? AND user_id = ?", (service_id, session["user_id"]))
        db.commit()

        user_tasks = cursor.execute("""SELECT services.id, services.title, services.description, services.price, services.image_url,
                                    users.resume, users.username FROM services
                                    JOIN users ON services.user_id = users.id
                                    WHERE services.user_id = ?""", (session["user_id"],)).fetchall()
        user_posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], row["resume"], row["username"], row["image_url"]) for row in user_tasks]

        user_profile = Profile(session["username"],session["profile_type"], None, session["user_id"], resume=session.get("resume", ""))
        cursor.close()
        db.close()
        return render_template("mainpage_seller.html", services = user_posts, profile = user_profile, tags = SERVICE_TAGS)  
 
@app.route("/service/<int:service_id>") 
def service_detail(service_id): 
    db = get_db_connection() 
    cursor = db.cursor() 
    service = cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    cursor.close()
    db.close()
    
    if not service:
        return "Service not found", 404

    service_data = {"id": service["id"], "title": service["title"], "description": service["description"], "price": service["price"]}
    user_profile = Profile(session["username"],session["profile_type"], None, session["user_id"], resume=session.get("resume", ""))
    
    return render_template("service_detail.html", service=service_data, profile = user_profile)


@app.route("/chat/<int:service_id>") 
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

    # 1. Try to find existing conversation
    conversation = cursor.execute("""
        SELECT * FROM conversations
        WHERE service_id = ? AND buyer_id = ?
    """, (service_id, buyer_id)).fetchone()

    # 2. If no conversation exists → create one
    if conversation is None:
        cursor.execute("""
            INSERT INTO conversations (service_id, buyer_id, seller_id)
            VALUES (?, ?, ?)
        """, (service_id, buyer_id, seller_id))
        db.commit()

        # Fetch the new conversation
        conversation = cursor.execute("""
            SELECT * FROM conversations
            WHERE service_id = ? AND buyer_id = ?
        """, (service_id, buyer_id)).fetchone()

    conversation_id = conversation["id"]

    # 3. Fetch messages
    messages = cursor.execute("""
        SELECT chat_messages.*, users.username
        FROM chat_messages
        JOIN users ON chat_messages.sender_id = users.id
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (conversation_id,)).fetchall()
    cursor.close()
    db.close()

    service_data = {"id": service["id"], "title": service["title"], "description": service["description"], "price": service["price"], "seller": service["seller_name"], "image_url": service["image_url"] or "/static/default_image.png"}
    user_profile = Profile(session["username"],session["profile_type"], None, session["user_id"], resume=session.get("resume", ""))
    return render_template("chat.html", 
                           service=service_data, 
                           profile = user_profile,
                           conversation_id = conversation_id, 
                           messages = messages)

@app.route("/chat/convo/<int:conversation_id>")
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

    # Load service (the convo contains service_id)
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
                           profile_type = profile_type,
                           )

@app.route("/send_message/<int:conversation_id>", methods=["POST"])
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

    # determine who to notify
    recipient_id = conv["seller_id"] if user_id == conv["buyer_id"] else conv["buyer_id"]

    # insert notification
    cursor.execute("""
        INSERT INTO notifications (user_id, message)
        VALUES (?, ?)
    """, (recipient_id, f"New message from {session['username']}"))

    db.commit()

    service_id = conv["service_id"]
    cursor.close()
    db.close()

    # correct redirect
    return redirect(f"/chat/{service_id}")

@app.route("/seller/inbox")
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

            -- Count unread messages (NOT sent by seller)
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

    # Total unread across all conversations
    total_unread = sum(c["unread_count"] for c in conversations)

    user_profile = Profile(
        session["username"],
        session["profile_type"],
        None,
        session["user_id"],
        session.get("resume", "")
    )

    # Pass total_unread into template
    return render_template(
        "seller_inbox.html",
        conversations=conversations,
        total_unread=total_unread,
        profile=user_profile
    )

ALLOWED_EXTENSIONS = {"pdf", "txt"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():
    if request.method == "POST":
        resume_text = request.form.get("resume_text", "").strip()
        resume_file = request.files.get("resume_file")

        extracted_text = ""

        if resume_file:
            filename = secure_filename(resume_file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
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
            return redirect(url_for("upload_resume"))
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET resume = ? WHERE id = ?", (extracted_text, session["user_id"]))
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

        return render_template("mainpage_seller.html", profile=user_profile, total_unread = total_unread)

    else:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT resume FROM users WHERE id = ?", (session["user_id"],))
        row = cursor.fetchone()
        resume_value = row["resume"] if row and row["resume"] else ""

        user_profile = Profile(
            session["username"],
            session["profile_type"],
            None,
            session["user_id"],
            resume_value
        )

        return render_template("upload_resume.html", profile=user_profile)



@app.route('/create-checkout-session/<int:service_id>', methods=['POST'])
def create_checkout_session(service_id):

    db = get_db_connection()
    cursor = db.cursor()
    service = cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    cursor.close()
    db.close()
    
    if not service:
        return "Service not found", 404
    YOUR_DOMAIN = 'http://127.0.0.1:5000'

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'myr',
                        'product_data': {
                            'name': service['title'],
                        },
                        'unit_amount': int(service['price'] * 100),
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)
    
@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/cancel')
def cancel():
    service_id = request.args.get('service_id', None)
    return render_template('cancel.html', service_id=service_id)


if __name__ == "__main__":
    app.run(debug=True)