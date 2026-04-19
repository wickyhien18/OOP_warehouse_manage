"""
repositories/user_repository.py
Chứa tất cả truy vấn DB liên quan đến Users, Roles, Categories, Warehouses, Auth.
"""
from helpers.db_helper import BaseRepository


class AuthRepository(BaseRepository):
    def find_user_by_username(self, username: str):
        return self.query_db(
            "SELECT Users.id, username, role_name, password_hash "
            "FROM Users JOIN Roles ON Users.role_id = Roles.id "
            "WHERE username like ?",
            ('%' + username + '%',), one=True
        )


class UserRepository(BaseRepository):
    def find_by_username(self, username: str):
        return self.query_db(
            "SELECT id FROM Users WHERE username = ?", (username,), one=True
        )

    def find_by_id(self, user_id):
        return self.query_db(
            "SELECT id FROM Users WHERE id = ?", (user_id,), one=True
        )

    def get_all(self):
        return self.query_db(
            "SELECT Users.id, Users.username, Roles.role_name, Users.created_at "
            "FROM Users JOIN Roles ON Users.role_id = Roles.id"
        )

    def search(self, user_id=None, username=None):
        query = (
            "SELECT Users.id, Users.username, Roles.role_name, Users.created_at "
            "FROM Users JOIN Roles ON Users.role_id = Roles.id WHERE"
        )
        data = ()
        parts = []
        if user_id:
            parts.append(" Users.id = ?")
            data += (user_id,)
        if username:
            parts.append(" Users.username like ?")
            data += ('%' + username + '%',)
        return self.query_db(query + " AND".join(parts), data)

    def create(self, username: str, password_hash: str, role_id: int):
        return self.execute_db(
            "INSERT INTO Users (username, password_hash, role_id) VALUES (?, ?, ?)",
            (username, password_hash, role_id)
        )

    def update_password(self, user_id, password_hash: str):
        return self.execute_db(
            "UPDATE Users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id)
        )

    def update_role(self, user_id, role_id):
        return self.execute_db(
            "UPDATE Users SET role_id = ? WHERE id = ?",
            (role_id, user_id)
        )

    def delete(self, user_id):
        return self.execute_db("DELETE FROM Users WHERE id = ?", (user_id,))

    def get_staff_role_id(self):
        return self.query_db(
            "SELECT id FROM Roles WHERE role_name = 'STAFF'", one=True
        )


class RoleRepository(BaseRepository):
    def get_all(self):
        return self.query_db("SELECT * FROM Roles")

    def find_by_id(self, role_id):
        return self.query_db(
            "SELECT id FROM Roles WHERE id = ?", (role_id,), one=True
        )

    def find_by_name(self, role_name: str):
        return self.query_db(
            "SELECT id FROM Roles WHERE role_name = ?", (role_name,), one=True
        )

    def search(self, role_id=None, role_name=None):
        parts, data = [], ()
        if role_id:
            parts.append(" id = ?")
            data += (role_id,)
        if role_name:
            parts.append(" role_name = ?")
            data += (role_name,)
        query = "SELECT * FROM Roles WHERE" + " AND".join(parts)
        return self.query_db(query, data)

    def create(self, role_name: str):
        return self.execute_db(
            "INSERT INTO Roles (role_name) VALUES (?)", (role_name,)
        )

    def update(self, role_id, role_name: str):
        return self.execute_db(
            "UPDATE Roles SET role_name = ? WHERE id = ?", (role_name, role_id)
        )

    def delete(self, role_id):
        return self.execute_db("DELETE FROM Roles WHERE id = ?", (role_id,))

    def has_users(self, role_id):
        return self.query_db(
            "SELECT id FROM Users WHERE role_id = ?", (role_id,), one=True
        )


class CategoryRepository(BaseRepository):
    def get_all(self):
        return self.query_db("SELECT * FROM Categories")

    def find_by_id(self, cat_id):
        return self.query_db(
            "SELECT id FROM Categories WHERE id = ?", (cat_id,), one=True
        )

    def find_by_name(self, name: str):
        return self.query_db(
            "SELECT id FROM Categories WHERE name = ?", (name,), one=True
        )

    def search(self, cat_id=None, name=None):
        parts, data = [], ()
        if cat_id:
            parts.append(" id = ?")
            data += (cat_id,)
        if name:
            parts.append(" name = ?")
            data += (name,)
        query = "SELECT * FROM Categories WHERE" + " AND".join(parts)
        return self.query_db(query, data)

    def create(self, name: str):
        return self.execute_db(
            "INSERT INTO Categories (name) VALUES (?)", (name,)
        )

    def update(self, cat_id, name: str):
        return self.execute_db(
            "UPDATE Categories SET name = ? WHERE id = ?", (name, cat_id)
        )

    def delete(self, cat_id):
        return self.execute_db(
            "DELETE FROM Categories WHERE id = ?", (cat_id,)
        )



