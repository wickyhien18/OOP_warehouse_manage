"""
repositories/receipt_repository.py
Tất cả SQL query liên quan đến Receipts / Receipt_Details / Inventory_Logs.
"""
from helpers.db_helper import BaseRepository


class ReceiptRepository(BaseRepository):

    # ── Lookup helpers ────────────────────────────────────────────────────────

    def find_warehouse_by_name(self, name: str):
        return self.query_db(
            "SELECT id FROM Warehouses WHERE name = ?", (name,), one=True
        )

    def find_staff_by_username(self, username: str):
        return self.query_db(
            "SELECT id FROM Users WHERE username = ?", (username,), one=True
        )

    def find_products_by_names(self, names: list):
        """Trả về list dict {name} của những sản phẩm tồn tại."""
        placeholders = ','.join(['?'] * len(names))
        return self.query_db(
            f"SELECT name FROM Products WHERE name IN ({placeholders})",
            tuple(names)
        )

    def find_product_id_by_name(self, name: str):
        row = self.query_db(
            "SELECT id FROM Products WHERE name = ?", (name,), one=True
        )
        return row['id'] if row else None

    def find_inventory(self, warehouse_id, product_id):
        return self.query_db(
            "SELECT id, quantity FROM Inventory WHERE warehouse_id = ? AND product_id = ?",
            (warehouse_id, product_id), one=True
        )

    def find_receipt_by_id(self, receipt_id):
        return self.query_db(
            "SELECT id FROM Receipts WHERE id = ?", (receipt_id,), one=True
        )

    # ── Create receipt ────────────────────────────────────────────────────────

    def create_receipt(self, receipt_type: str, warehouse_id, staff_id, partner_name: str):
        """
        Dùng OUTPUT INSERTED.id để lấy ID vừa insert (SQL Server).
        Trả về integer ID, hoặc None nếu thất bại.
        """
        return self.insert_returning_id(
            "INSERT INTO Receipts (type, warehouse_id, staff_id, partner_name) "
            "OUTPUT INSERTED.id VALUES (?, ?, ?, ?)",
            (receipt_type, warehouse_id, staff_id, partner_name)
        )

    def add_detail(self, receipt_id, product_id, quantity, price):
        return self.execute_db(
            "INSERT INTO Receipt_Details (receipt_id, product_id, quantity, price) "
            "VALUES (?, ?, ?, ?)",
            (receipt_id, product_id, quantity, price)
        )

    # ── Inventory mutations ───────────────────────────────────────────────────

    def create_inventory(self, warehouse_id, product_id, quantity):
        return self.execute_db(
            "INSERT INTO Inventory (warehouse_id, product_id, quantity) VALUES (?, ?, ?)",
            (warehouse_id, product_id, quantity)
        )

    def add_inventory(self, inv_id, quantity):
        return self.execute_db(
            "UPDATE Inventory SET quantity = quantity + ? WHERE id = ?",
            (quantity, inv_id)
        )

    def subtract_inventory(self, inv_id, quantity):
        return self.execute_db(
            "UPDATE Inventory SET quantity = quantity - ? WHERE id = ?",
            (quantity, inv_id)
        )

    def add_inventory_log(self, product_id, warehouse_id, quantity, action_type, receipt_id):
        return self.execute_db(
            "INSERT INTO Inventory_Logs "
            "(product_id, warehouse_id, change_amount, action_type, reference_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (product_id, warehouse_id, quantity, action_type, receipt_id)
        )

    def set_inventory_absolute(self, inv_id, actual_quantity):
        """Đặt lại số lượng tồn kho theo số lượng thực tế đếm được (Dùng cho Kiểm kê)."""
        return self.execute_db(
            "UPDATE Inventory SET quantity = ? WHERE id = ?",
            (actual_quantity, inv_id)
        )
    # ── Queries ───────────────────────────────────────────────────────────────

    _DETAIL_SQL = """
        SELECT r.id       AS receipt_id,
               r.type,
               r.partner_name,
               r.created_at,
               w.name     AS warehouse_name,
               u.username AS staff_name,
               p.name     AS product_name,
               p.sku,
               rd.quantity,
               rd.price
        FROM Receipts r
        JOIN Warehouses w      ON r.warehouse_id = w.id
        JOIN Users u           ON r.staff_id = u.id
        JOIN Receipt_Details rd ON r.id = rd.receipt_id
        JOIN Products p        ON rd.product_id = p.id
    """

    def get_all_raw(self):
        return self.query_db(self._DETAIL_SQL + " ORDER BY r.created_at DESC")

    def get_by_type_raw(self, receipt_type: str):
        return self.query_db(
            self._DETAIL_SQL + " WHERE r.type = ? ORDER BY r.created_at DESC",
            (receipt_type,)
        )

    def get_by_id_raw(self, receipt_id):
        return self.query_db(
            self._DETAIL_SQL + " WHERE r.id = ?",
            (receipt_id,)
        )

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, receipt_id):
        return self.execute_db(
            "DELETE FROM Receipts WHERE id = ?", (receipt_id,)
        )