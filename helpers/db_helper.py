import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnection:
    """Quản lý kết nối tới SQL Server."""

    def __init__(self):
        self._driver = os.getenv("DB_DRIVER")
        self._server = os.getenv("DB_SERVER")
        self._database = os.getenv("DB_NAME")
        self._trusted = os.getenv("DB_TRUSTED_CONNECTION", "no")
        self._user = os.getenv("DB_USER")
        self._password = os.getenv("DB_PASSWORD")

    def get_connection(self):
        conn_str = f"DRIVER={self._driver};SERVER={self._server};DATABASE={self._database};"
        if self._trusted.lower() == "yes":
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={self._user};PWD={self._password};TrustServerCertificate=yes;"
        try:
            return pyodbc.connect(conn_str)
        except Exception as e:
            print(f"[DB] Connection error: {e}")
            return None


class BaseRepository:
    """
    Lớp cơ sở cho tất cả Repository.
    Cung cấp query_db và execute_db dùng chung.
    """

    def __init__(self):
        self._db = DatabaseConnection()

    def query_db(self, query: str, args=(), one=False):
        conn = self._db.get_connection()
        if conn is None:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return (rows[0] if rows else None) if one else rows
        finally:
            conn.close()

    def execute_db(self, query: str, args=()):
        conn = self._db.get_connection()
        if conn is None:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def insert_returning_id(self, query: str, args=()):
        """
        Dùng cho INSERT ... OUTPUT INSERTED.id (SQL Server).
        query_db thông thường không commit nên OUTPUT không lưu được.
        Method này execute + commit + trả về id.
        """
        conn = self._db.get_connection()
        if conn is None:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, args)
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_raw_connection(self):
        """Trả về raw connection để dùng transaction thủ công."""
        return self._db.get_connection()


# Singleton dùng cho các module cũ (backward-compat)
_repo = BaseRepository()


def get_db_connection():
    return DatabaseConnection().get_connection()


def query_db(query, args=(), one=False):
    return _repo.query_db(query, args, one)


def execute_db(query, args=()):
    return _repo.execute_db(query, args)