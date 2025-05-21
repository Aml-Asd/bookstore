import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables from .env file (for SECRET_KEY, DATABASE_URL)
load_dotenv()

# Import Config after load_dotenv
from config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # The route function for login
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info" # Bootstrap class for flash message
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass # Already exists

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Import and register blueprints
    from bookstore_flask_project.app.routes.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from bookstore_flask_project.app.routes.customer_routes import bp as customer_bp
    app.register_blueprint(customer_bp) # No prefix for main site pages

    from bookstore_flask_project.app.routes.manager_routes import bp as manager_bp
    app.register_blueprint(manager_bp, url_prefix='/manager')

    # Import models here to ensure they are known to Flask-Migrate
    # but after db is initialized. This also avoids circular imports
    # if models need 'app' or 'db'.
    from bookstore_flask_project.app import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Context processor to make current_user available in all templates
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)

    return app