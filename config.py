import os

class Config:
    # Key for secure sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_stockvision_secure_key_987654321'
    
    # Detect Vercel or other serverless environment
    IS_SERVERLESS = os.environ.get('VERCEL') is not None or os.environ.get('SERVERLESS') is not None
    
    # Database configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    if IS_SERVERLESS:
        # Vercel only allows writing to the /tmp folder
        DB_DIR = '/tmp'
        MODELS_DIR = '/tmp/models'
    else:
        DB_DIR = os.path.join(BASE_DIR, 'database')
        MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    # Ensure directories exist
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Database URL configuration (Supports external Postgres/MySQL, defaults to SQLite)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(DB_DIR, 'stockvision.db')}"
    # Workaround for postgresql:// vs postgres:// URL schema on Heroku/Vercel
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False

