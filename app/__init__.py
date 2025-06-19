from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .models import db, User

migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='app/templates')
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main
    app.register_blueprint(main)

    # ✅ Category creation happens AFTER app is fully ready
    with app.app_context():
        from .models import Category
        if not Category.query.filter_by(name="Other").first():
            db.session.add(Category(name="Other"))
            db.session.commit()

    return app

