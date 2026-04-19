"""
repositories/domain_repositories.py
Truy vấn DB cho Product, Inventory, Transfer, Logistics, Receipt, Reports.
"""
from helpers.db_helper import BaseRepository


class ProductRepository(BaseRepository):
    _BASE = (
        "SELECT products.id, sku, products.name AS product_name, "
        "min_stock, description, created_at, categories.name AS category_name "
        "FROM products JOIN Categories ON Categories.id = products.category_id"
    )

    def get_all(self):
        return self.query_db(self._BASE)

    def find_by_id(self, product_id):
        return self.query_db(self._BASE + " WHERE products.id = ?", (product_id,), one=True)

    def find_by_name(self, name: str):
        return self.query_db(self._BASE + " WHERE products.name like ?", (name,))

    def find_id_by_id(self, product_id):
        return self.query_db(
            "SELECT id FROM Products WHERE id = ?", (product_id,), one=True
        )

    def find_by_sku(self, sku: str):
        return self.query_db(
            "SELECT id FROM Products WHERE sku = ?", (sku,), one=True
        )

    def find_by_exact_name(self, name: str):
        return self.query_db(
            "SELECT id FROM Products WHERE name = ?", (name,), one=True
        )

    def create(self, sku, name, category_id, min_stock, description):
        return self.execute_db(
            "INSERT INTO Products(sku, name, category_id, min_stock, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (sku, name, category_id, min_stock, description)
        )

    def update(self, product_id, sku, name, category_id, min_stock, description):
        return self.execute_db(
            "UPDATE Products SET sku=?, name=?, category_id=?, min_stock=?, description=? "
            "WHERE id=?",
            (sku, name, category_id, min_stock, description, product_id)
        )

    def delete(self, product_id):
        return self.execute_db(
            "DELETE FROM Products WHERE id=?", (product_id,)
        )


class InventoryRepository(BaseRepository):
    _BASE = """
        SELECT i.id, i.warehouse_id, i.product_id,
               w.name AS warehouse_name, p.name AS product_name, i.quantity
        FROM Inventory i
        JOIN Warehouses w ON i.warehouse_id = w.id
        JOIN Products p ON i.product_id = p.id
    """

    def get_all(self):
        return self.query_db(self._BASE + " ORDER BY i.id DESC")

    def find_by_id(self, inv_id):
        return self.query_db(
            "SELECT id FROM Inventory WHERE id=?", (inv_id,), one=True
        )

    def find_by_warehouse_product(self, warehouse_id, product_id):
        return self.query_db(
            "SELECT id, quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
            (warehouse_id, product_id), one=True
        )

    def find_with_stock(self, product_id):
        return self.query_db(
            "SELECT i.*, w.Latitude, w.Longitude FROM Inventory i "
            "JOIN Warehouses w ON i.warehouse_id = w.id "
            "WHERE product_id=? AND quantity > 0",
            (product_id,)
        )

    def search_by_product(self, name: str):
        return self.query_db(
            self._BASE + " WHERE p.name LIKE ?", (f"%{name}%",)
        )

    def search_by_warehouse(self, name: str):
        return self.query_db(
            self._BASE + " WHERE w.name LIKE ?", (f"%{name}%",)
        )

    def add_quantity(self, inv_id, quantity):
        return self.execute_db(
            "UPDATE Inventory SET quantity = quantity + ? WHERE id=?",
            (quantity, inv_id)
        )

    def subtract_quantity(self, inv_id, quantity):
        return self.execute_db(
            "UPDATE Inventory SET quantity = quantity - ? WHERE id=?",
            (quantity, inv_id)
        )

    def create(self, warehouse_id, product_id, quantity):
        return self.execute_db(
            "INSERT INTO Inventory (warehouse_id, product_id, quantity) VALUES (?,?,?)",
            (warehouse_id, product_id, quantity)
        )

    def set_quantity(self, inv_id, quantity):
        return self.execute_db(
            "UPDATE Inventory SET quantity=? WHERE id=?", (quantity, inv_id)
        )

    def delete(self, inv_id):
        return self.execute_db(
            "DELETE FROM Inventory WHERE id=?", (inv_id,)
        )

    def update_by_warehouse_product(self, warehouse_id, product_id, delta: int):
        return self.execute_db(
            "UPDATE Inventory SET quantity = quantity + ? "
            "WHERE warehouse_id=? AND product_id=?",
            (delta, warehouse_id, product_id)
        )

    def get_stock(self, warehouse_id, product_id):
        return self.query_db(
            "SELECT quantity FROM Inventory WHERE warehouse_id=? AND product_id=?",
            (warehouse_id, product_id), one=True
        )


class TransferRepository(BaseRepository):
    def get_all(self):
        return self.query_db("SELECT * FROM Transfer_Orders")

    def find_by_id(self, transfer_id):
        return self.query_db(
            "SELECT * FROM Transfer_Orders WHERE id=?", (transfer_id,), one=True
        )

    def find_latest(self):
        return self.query_db(
            "SELECT TOP 1 * FROM Transfer_Orders ORDER BY id DESC", one=True
        )

    def create(self, from_wh_id, to_wh_id, staff_id):
        return self.execute_db(
            "INSERT INTO Transfer_Orders (from_warehouse_id, to_warehouse_id, staff_id, status) "
            "VALUES (?, ?, ?, 'PENDING')",
            (from_wh_id, to_wh_id, staff_id)
        )

    def update_status(self, transfer_id, status: str):
        return self.execute_db(
            "UPDATE Transfer_Orders SET status=? WHERE id=?", (status, transfer_id)
        )

    def get_details(self, transfer_id):
        return self.query_db(
            "SELECT * FROM Transfer_Details WHERE transfer_id=?", (transfer_id,)
        )

    def add_detail(self, transfer_id, product_id, quantity):
        return self.execute_db(
            "INSERT INTO Transfer_Details (transfer_id, product_id, quantity) VALUES (?, ?, ?)",
            (transfer_id, product_id, quantity)
        )


class ShipmentRepository(BaseRepository):
    def get_all(self):
        return self.query_db("SELECT * FROM Shipments")

    def find_by_id(self, shipment_id):
        return self.query_db(
            "SELECT * FROM Shipments WHERE id=?", (shipment_id,), one=True
        )

    def find_by_transfer_id(self, transfer_id):
        return self.query_db(
            "SELECT * FROM Shipments WHERE transfer_id=?", (transfer_id,), one=True
        )

    def create(self, transfer_id, driver_name, license_plate, expected_at):
        return self.execute_db(
            "INSERT INTO Shipments (transfer_id, driver_name, license_plate, status, expected_delivery_at) "
            "VALUES (?, ?, ?, 'PICKING', ?)",
            (transfer_id, driver_name, license_plate, expected_at)
        )

    def update(self, shipment_id, fields: dict):
        set_clauses = [f"{k}=?" for k in fields]
        values = list(fields.values()) + [shipment_id]
        return self.execute_db(
            f"UPDATE Shipments SET {', '.join(set_clauses)} WHERE id=?",
            tuple(values)
        )

    def delete(self, shipment_id):
        return self.execute_db(
            "DELETE FROM Shipments WHERE id=?", (shipment_id,)
        )


class ReceiptRepository(BaseRepository):
    def find_by_id(self, receipt_id):
        return self.query_db(
            "SELECT * FROM Receipts WHERE id=?", (receipt_id,), one=True
        )

    def find_latest(self):
        return self.query_db(
            "SELECT TOP 1 id FROM Receipts ORDER BY id DESC", one=True
        )

    def get_details(self, receipt_id):
        return self.query_db(
            "SELECT * FROM Receipt_Details WHERE receipt_id=?", (receipt_id,)
        )

    def create_receipt(self, warehouse_id, receipt_type, staff_id, partner_name, note):
        return self.execute_db(
            "INSERT INTO Receipts (warehouse_id, type, staff_id, partner_name, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (warehouse_id, receipt_type, staff_id, partner_name, note)
        )

    def add_detail(self, receipt_id, product_id, quantity, price):
        return self.execute_db(
            "INSERT INTO Receipt_Details (receipt_id, product_id, quantity, price) "
            "VALUES (?, ?, ?, ?)",
            (receipt_id, product_id, quantity, price)
        )

class WarehouseRepository(BaseRepository):
    def get_all(self):
        return self.query_db("SELECT * FROM Warehouses")

    def find_by_id(self, wh_id):
        return self.query_db(
            "SELECT * FROM Warehouses WHERE id = ?", (wh_id,), one=True
        )

    def search(self, wh_id=None, name=None):
        parts, data = [], ()
        if wh_id:
            parts.append(" id = ?")
            data += (wh_id,)
        if name:
            parts.append(" name like ?")
            data += ('%' + name + '%',)
        query = "SELECT * FROM Warehouses WHERE" + " AND".join(parts)
        return self.query_db(query, data)

    def create(self, name, address, capacity, longitude, latitude):
        return self.execute_db(
            "INSERT INTO Warehouses (name, address, capacity, longitude, latitude) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, address, capacity, longitude, latitude)
        )

    def update(self, wh_id, fields: dict):
        set_clauses = [f"{k} = ?" for k in fields]
        values = list(fields.values()) + [wh_id]
        return self.execute_db(
            f"UPDATE Warehouses SET {', '.join(set_clauses)} WHERE id = ?",
            tuple(values)
        )

    def delete(self, wh_id):
        return self.execute_db(
            "DELETE FROM Warehouses WHERE id = ?", (wh_id,)
        )

class ReportRepository(BaseRepository):
    def get_ton_kho(self):
        return self.query_db("""
            SELECT i.id, w.name AS warehouse_name, p.name AS product_name, i.quantity
            FROM Inventory i
            JOIN Products p ON i.product_id = p.id
            JOIN Warehouses w ON i.warehouse_id = w.id
            WHERE i.quantity > 0
        """)

    def get_low_stock(self):
        return self.query_db("""
            SELECT p.name AS product_name, p.min_stock,
                   ISNULL(SUM(i.quantity), 0) AS total_quantity,
                   (p.min_stock - ISNULL(SUM(i.quantity), 0)) AS need_to_import
            FROM Products p
            LEFT JOIN Inventory i ON p.id = i.product_id
            GROUP BY p.name, p.min_stock
            HAVING ISNULL(SUM(i.quantity), 0) <= p.min_stock
        """)

    def get_inventory_history(self, sku: str):
        return self.query_db("""
            SELECT p.sku, p.name AS product_name,
                   w.name AS warehouse_name,
                   l.change_amount, l.action_type, l.created_at
            FROM Inventory_Logs l
            JOIN Products p ON l.product_id = p.id
            LEFT JOIN Warehouses w ON l.warehouse_id = w.id
            WHERE p.sku = ?
            ORDER BY l.created_at DESC
        """, (sku,))

    def get_transfer_history(self, sku=None):
        query = """
            SELECT p.sku, p.name AS product_name,
                   w_from.name AS from_warehouse, w_to.name AS to_warehouse,
                   td.quantity, ISNULL(u.username, 'System') AS staff,
                   t.status, t.created_at
            FROM Transfer_Details td
            JOIN Transfer_Orders t ON td.transfer_id = t.id
            JOIN Products p ON td.product_id = p.id
            JOIN Warehouses w_from ON t.from_warehouse_id = w_from.id
            JOIN Warehouses w_to ON t.to_warehouse_id = w_to.id
            LEFT JOIN Users u ON t.staff_id = u.id
        """
        params = []
        if sku:
            query += " WHERE p.sku = ?"
            params.append(sku)
        query += " ORDER BY t.created_at DESC"
        return self.query_db(query, tuple(params))

    def get_receipt_history(self):
        return self.query_db("""
            SELECT r.id AS receipt_id, r.type,
                   w.name AS warehouse_name,
                   p.sku, p.name AS product_name,
                   rd.quantity, rd.price,
                   (rd.quantity * rd.price) AS total_value,
                   ISNULL(u.username, 'System') AS staff,
                   r.partner_name, r.created_at
            FROM Receipts r
            JOIN Receipt_Details rd ON r.id = rd.receipt_id
            JOIN Products p ON rd.product_id = p.id
            JOIN Warehouses w ON r.warehouse_id = w.id
            LEFT JOIN Users u ON r.staff_id = u.id
            ORDER BY r.created_at DESC
        """)

    def get_excel_inventory(self):
        return self.query_db("""
            SELECT w.name AS warehouse, p.sku, p.name AS product, i.quantity
            FROM Inventory i
            JOIN Products p ON i.product_id = p.id
            JOIN Warehouses w ON i.warehouse_id = w.id
        """)

    def get_excel_stock_summary(self):
        return self.query_db("""
            SELECT p.name, p.min_stock, ISNULL(SUM(i.quantity),0) AS total
            FROM Products p
            LEFT JOIN Inventory i ON p.id = i.product_id
            GROUP BY p.name, p.min_stock
        """)

    def get_excel_history(self):
        return self.query_db("""
            SELECT TOP 100 p.sku, p.name, l.change_amount, l.action_type, l.created_at
            FROM Inventory_Logs l
            JOIN Products p ON l.product_id = p.id
            ORDER BY l.created_at DESC
        """)

    def get_excel_transfers(self):
        return self.query_db("""
            SELECT p.sku, p.name, w_from.name AS from_wh, w_to.name AS to_wh,
                   td.quantity, t.status, t.created_at
            FROM Transfer_Details td
            JOIN Transfer_Orders t ON td.transfer_id = t.id
            JOIN Products p ON td.product_id = p.id
            JOIN Warehouses w_from ON t.from_warehouse_id = w_from.id
            JOIN Warehouses w_to ON t.to_warehouse_id = w_to.id
        """)
