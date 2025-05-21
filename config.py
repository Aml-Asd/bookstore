import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env')) # Load .env file from project root

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-hard-to-guess-secret-string-for-dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'bookstore.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # For file uploads (example, adjust path as needed)
    # UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'images', 'uploads')
    # Or to instance folder (more secure if instance is not served directly)
    UPLOAD_FOLDER = os.path.join(basedir, 'instance', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # For image uploads