from flask import Flask
from config import Config
from database.models import db, User
from flask_login import LoginManager
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize SQLAlchemy database
    db.init_app(app)
    
    # Initialize Flask-Login session manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register Route Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Database initialization & seeding
    with app.app_context():
        db.create_all()
        
        # Check and seed default admin account
        admin_email = 'admin@stockvision.ai'
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            print("Seeding administrative account: admin@stockvision.ai")
            admin = User(
                full_name='System Administrator',
                email=admin_email,
                is_admin=True
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("Admin account seeded successfully!")
            
    return app

app = create_app()

if __name__ == '__main__':
    # Listen on all interfaces, port 5000 for standard local run
    app.run(host='0.0.0.0', port=5000, debug=True)
