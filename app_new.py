"""
FreelanceHub - Main Application Entry Point
Organized structure with blueprints for better maintainability
"""
from flask import Flask
from flask_session import Session
import os

from src.config.settings import config
from src.routes.auth import auth_bp
from src.routes.buyer import buyer_bp
from src.routes.seller import seller_bp
from src.routes.services import service_bp
from src.routes.chat import chat_bp
from src.routes.resume import resume_bp

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    app.config["SESSION_FILE_DIR"] = os.path.join(app.root_path, "flask_session")
    
    # Initialize extensions
    Session(app)
    
    # Configure Flask
    app.jinja_env.auto_reload = True
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(buyer_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(resume_bp)
    
    @app.after_request
    def after_request(response):
        """Ensure responses aren't cached"""
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
