"""Lightweight DB helper using PyMySQL (no flask-sqlalchemy needed).
Works on both Windows and Linux/Mac.
"""
import os
import pymysql
from contextlib import contextmanager
from app.config import Config

def get_connection():
    # On Windows, unix_socket is not supported → use TCP (host + port)
    # On Linux/Mac, prefer socket if it exists
    connect_args = {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "user": Config.MYSQL_USER,
        "password": Config.MYSQL_PASSWORD,
        "database": Config.MYSQL_DB,
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }

    # Only use unix_socket on non-Windows systems and if the socket file exists
    if os.name != "nt":  # not Windows
        socket_path = Config.MYSQL_SOCKET
        if socket_path and os.path.exists(socket_path):
            connect_args["unix_socket"] = socket_path
            # When using socket, host/port are ignored by PyMySQL

    return pymysql.connect(**connect_args)

@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
