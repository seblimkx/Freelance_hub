"""Application configuration settings"""
import os
from dotenv import load_dotenv

load_dotenv()

# Upload folder configuration
UPLOAD_FOLDER = "static/uploads"

# Service category tags
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

# Flask configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    SESSION_PERMANENT = True
    UPLOAD_FOLDER = UPLOAD_FOLDER
    SESSION_TYPE = "filesystem"
    TEMPLATES_AUTO_RELOAD = True
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Select config based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
