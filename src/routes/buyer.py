"""Buyer-related routes"""
from flask import Blueprint, render_template, request, session, redirect
import json
from src.models import Profile, freelance_post
from src.utils.database import get_db_connection
from src.utils.search_engine import SearchQuery
from src.config import SERVICE_TAGS

buyer_bp = Blueprint('buyer', __name__)

def recommend(posts):
    """Recommend posts based on user preferences"""
    db = get_db_connection()
    cursor = db.cursor()
    row = cursor.execute("SELECT preferences FROM users WHERE id = ?", (session["user_id"],)).fetchone()
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

@buyer_bp.route("/buyer", methods=["GET"])
def buyer():
    db = get_db_connection()
    cursor = db.cursor()
    user_id = session["user_id"]

    user_profile = Profile(session["username"], session["profile_type"], None, 
                          session["user_id"], resume=session.get("resume", ""))
    services = cursor.execute("""
        SELECT services.id, services.title, services.description, services.price, services.image_url,
               users.resume, users.username
        FROM services
        JOIN users ON services.user_id = users.id
        WHERE services.user_id != ?
    """, (user_id,)).fetchall()
    posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], 
                           row["resume"], row["username"], row["image_url"]) for row in services]
    ranked_items = recommend(posts)

    # Get user preferences for highlighting (single category only)
    row = cursor.execute("SELECT preferences FROM users WHERE id = ?", (user_id,)).fetchone()
    user_preferences = json.loads(row["preferences"]) if row and row["preferences"] else []
    active_category = user_preferences[0] if user_preferences else None
    
    # Reorder tags to put active category first
    reordered_tags = list(SERVICE_TAGS)
    if active_category and active_category in reordered_tags:
        reordered_tags.remove(active_category)
        reordered_tags.insert(0, active_category)

    cursor.close()
    db.close()

    session["profile_type"] = "buyer"
    return render_template("mainpage_buyer.html", items=ranked_items, profile=user_profile, 
                          tags=reordered_tags, selected_category=active_category)

@buyer_bp.route("/set_preferences", methods=["GET", "POST"])
def set_preferences():
    selected_tags = request.form.get("selected_tags", "[]")
    
    try:
        preferences = json.loads(selected_tags)
    except Exception:
        preferences = []

    preferences_str = json.dumps(preferences)

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET preferences = ? WHERE id = ?", 
                  (preferences_str, session["user_id"]))
    db.commit()
    cursor.close()
    db.close()

    return redirect("/buyer")

@buyer_bp.route("/search", methods=["GET", "POST"])
def search():
    db = get_db_connection()
    cursor = db.cursor()
    
    services = cursor.execute("""SELECT services.id, services.title, services.description, services.price, 
                                services.image_url, users.resume, users.username FROM services
                                JOIN users ON services.user_id = users.id""").fetchall()
    posts = [freelance_post(row["title"], row["description"], row["price"], row["id"], 
                           row["resume"], row["username"], row["image_url"]) for row in services]
    engine = SearchQuery(posts)
    query = request.args.get("query")

    if query:
        results = engine.search(query)
        items_ranked = [item for item, score in results]
    else:
        items_ranked = posts

    user_profile = Profile(session["username"], session["profile_type"], None, 
                          session["user_id"], resume=session.get("resume", ""))
    
    # Get user preferences for consistency with buyer route
    user_id = session["user_id"]
    row = cursor.execute("SELECT preferences FROM users WHERE id = ?", (user_id,)).fetchone()
    user_preferences = json.loads(row["preferences"]) if row and row["preferences"] else []
    active_category = user_preferences[0] if user_preferences else None
    
    cursor.close()
    db.close()

    return render_template("mainpage_buyer.html", items=items_ranked, profile=user_profile, 
                          tags=SERVICE_TAGS, selected_category=active_category)
