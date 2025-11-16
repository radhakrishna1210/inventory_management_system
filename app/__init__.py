import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-default-secret-key-for-dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    UPLOAD_FOLDER = os.path.join(app.root_path, 'static/uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from . import models

        from .main.routes import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from .admin.routes import admin as admin_blueprint
        app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    @app.context_processor
    def inject_is_customer():
        from flask_login import current_user
        is_customer = False
        if current_user.is_authenticated:
            # Check if user has email attribute (Customer) vs username (Admin User)
            # Customers have email, Admins have username
            is_customer = hasattr(current_user, 'email') and getattr(current_user, 'email', None) is not None
        return dict(is_customer=is_customer)

    return app
