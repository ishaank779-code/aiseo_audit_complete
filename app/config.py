import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'aiseo-secret-key-change-in-prod')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'aiseo')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'aiseo123')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'aiseo_audit')
    MYSQL_SOCKET = os.environ.get('MYSQL_SOCKET', '/tmp/mysql.sock')

    # Prefer socket if available (sandbox style)
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@localhost/{MYSQL_DB}"
        f"?unix_socket={MYSQL_SOCKET}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
