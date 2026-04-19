"""
services/services.py
Business logic layer — không phụ thuộc vào Flask request/response.
"""
import math
from datetime import datetime
from flask import abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from repositories.core_repositories import (
    AuthRepository, UserRepository, RoleRepository,
    CategoryRepository,
)
from repositories.domain_repositories import (
    ProductRepository, InventoryRepository,
    TransferRepository, ShipmentRepository,
    ReceiptRepository, ReportRepository, WarehouseRepository,
)
from helpers.validate_helper import Validator


# ─── Auth ────────────────────────────────────────────────────────────────────

class AuthService:
    def __init__(self):
        self._repo = AuthRepository()

    def login(self, username: str, password: str):
        if Validator.is_empty(username) or Validator.is_empty(password):
            abort(400, description="Tên đăng nhập và mật khẩu không được để trống")

        user = self._repo.find_user_by_username(username)
        if not user or not check_password_hash(user['password_hash'], password):
            abort(401, description="Tên đăng nhập hoặc mật khẩu không đúng")

        token = create_access_token(
            identity=str(user['id']),
            additional_claims={"role": user['role_name'], "username": user['username']}
        )
        return token, user


# ─── Users ───────────────────────────────────────────────────────────────────

class UserService:
    def __init__(self):
        self._repo = UserRepository()

    def register(self, username: str, password: str):
        if Validator.is_empty(username) or Validator.is_empty(password):
            abort(400, description="Tên đăng nhập và mật khẩu không được để trống")

        username = username.strip()
        if len(username) < 3 or len(username) > 50 or ' ' in username:
            abort(400, description="Tên đăng nhập phải có độ dài từ 3 đến 50 ký tự và không được chứa khoảng trắng")

        if self._repo.find_by_username(username):
            abort(400, description="Tên đăng nhập đã tồn tại")

        password = password.strip()
        if not Validator.validate_password_strength(password):
            abort(400, description="Mật khẩu yếu. Mật khẩu nên có ít nhất 8 ký tự, gồm kí tự đặc biệt, chữ hoa, chữ thường và số.")

        role = self._repo.get_staff_role_id()
        success = self._repo.create(username, generate_password_hash(password), role['id'])
        if not success:
            abort(500, description="Đã xảy ra lỗi khi tạo tài khoản")

    def get_list(self, user_id=None, username=None):
        if not user_id and not username:
            users = self._repo.get_all()
        else:
            users = self._repo.search(user_id, username)
        if not users:
            abort(404, description="Không tìm thấy người dùng nào phù hợp với tiêu chí tìm kiếm")
        return users

    def change_password(self, user_id, new_password: str):
        if Validator.is_empty(new_password):
            abort(400, description="Mật khẩu không được để trống")
        new_password = new_password.strip()
        if not Validator.validate_password_strength(new_password):
            abort(400, description="Mật khẩu yếu. Mật khẩu nên có ít nhất 8 ký tự, gồm kí tự đặc biệt, chữ hoa, chữ thường và số.")
        if not self._repo.find_by_id(user_id):
            abort(404, description="Không tìm thấy người dùng với ID đã cho")
        if not self._repo.update_password(user_id, generate_password_hash(new_password)):
            abort(500, description="Đã xảy ra lỗi khi cập nhật mật khẩu")

    def update_role(self, user_id, role_id):
        if not user_id or not role_id:
            abort(400, description="ID của người dùng và vai trò không được để trống")
        if not self._repo.find_by_id(user_id):
            abort(404, description="Không tìm thấy người dùng với ID đã cho")
        role_repo = RoleRepository()
        if not role_repo.find_by_id(role_id):
            abort(404, description="Không tìm thấy vai trò với ID đã cho")
        if not self._repo.update_role(user_id, role_id):
            abort(500, description="Đã xảy ra lỗi khi cập nhật vai trò của người dùng")

    def delete(self, user_id):
        if not self._repo.find_by_id(user_id):
            abort(404, description="Không tìm thấy người dùng với ID đã cho")
        self._repo.delete(user_id)


# ─── Roles ───────────────────────────────────────────────────────────────────

class RoleService:
    def __init__(self):
        self._repo = RoleRepository()

    def get_list(self, role_id=None, role_name=None):
        if not role_id and not role_name:
            roles = self._repo.get_all()
        else:
            roles = self._repo.search(role_id, role_name)
        if not roles:
            abort(404, description="Không tìm thấy vai trò nào phù hợp với tiêu chí tìm kiếm")
        return roles

    def create(self, role_name: str):
        if Validator.is_empty(role_name):
            abort(400, description="Tên vai trò không được để trống")
        role_name = role_name.strip().upper()
        if self._repo.find_by_name(role_name):
            abort(400, description="Vai trò này đã tồn tại")
        if not self._repo.create(role_name):
            abort(500, description="Đã xảy ra lỗi khi tạo vai trò mới")

    def update(self, role_id, role_name: str):
        if role_name is None:
            abort(400, description="Tên vai trò không được để trống")
        role_name = role_name.strip().upper()
        if not self._repo.update(role_id, role_name):
            abort(500, description="Đã xảy ra lỗi khi cập nhật vai trò")

    def delete(self, role_id):
        if not self._repo.find_by_id(role_id):
            abort(404, description="Vai trò không tồn tại")
        self._repo.delete(role_id)


# ─── Categories ──────────────────────────────────────────────────────────────

class CategoryService:
    def __init__(self):
        self._repo = CategoryRepository()

    def get_list(self, cat_id=None, name=None):
        if not cat_id and not name:
            cats = self._repo.get_all()
        else:
            cats = self._repo.search(cat_id, name)
        if not cats:
            abort(404, description="Không tìm thấy danh mục nào phù hợp với tiêu chí tìm kiếm")
        return cats

    def create(self, name: str):
        if Validator.is_empty(name):
            abort(400, description="Tên của danh mục không được để trống")
        name = name.strip().upper()
        if self._repo.find_by_name(name):
            abort(400, description="Danh mục này đã tồn tại")
        if not self._repo.create(name):
            abort(500, description="Đã xảy ra lỗi khi tạo danh mục mới")

    def update(self, cat_id, name: str):
        if Validator.is_empty(name):
            abort(400, description="Tên của danh mục không được để trống")
        name = name.strip().upper()
        if self._repo.find_by_name(name):
            abort(400, description="Danh mục này đã tồn tại")
        if not self._repo.find_by_id(cat_id):
            abort(404, description="Không tìm thấy danh mục với ID đã cho")
        if not self._repo.update(cat_id, name):
            abort(500, description="Đã xảy ra lỗi khi cập nhật danh mục")

    def delete(self, cat_id):
        if not self._repo.find_by_id(cat_id):
            abort(404, description="Không tìm thấy danh mục với ID đã cho")
        self._repo.delete(cat_id)


# ─── Warehouses ──────────────────────────────────────────────────────────────

class WarehouseService:
    def __init__(self):
        self._repo = WarehouseRepository()

    def get_list(self, wh_id=None, name=None):
        if not wh_id and not name:
            result = self._repo.get_all()
        else:
            result = self._repo.search(wh_id, name)
        if not result:
            abort(404, description="Không tìm thấy kho hàng nào phù hợp với tiêu chí tìm kiếm")
        return result

    def create(self, name, address, capacity, longitude, latitude):
        if Validator.is_empty(name):
            abort(400, description="Tên của kho hàng không được để trống")
        name = name.strip().upper()
        if not self._repo.create(name, address, capacity, longitude, latitude):
            abort(500, description="Đã xảy ra lỗi khi tạo kho hàng mới")

    def update(self, wh_id, payload: dict):
        if not self._repo.find_by_id(wh_id):
            abort(404, description="Không tìm thấy kho hàng với ID đã cho")
        fields = {}
        if payload.get("name") and payload["name"].strip():
            fields["name"] = payload["name"].strip()
        if payload.get("address") and payload["address"].strip():
            fields["address"] = payload["address"].strip()
        if payload.get("capacity") not in (None, ""):
            fields["capacity"] = int(payload["capacity"])
        if payload.get("longitude") not in (None, ""):
            fields["longitude"] = payload["longitude"]
        if payload.get("latitude") not in (None, ""):
            fields["latitude"] = payload["latitude"]
        if not fields:
            abort(400, description="Không có dữ liệu nào để cập nhật")
        self._repo.update(wh_id, fields)

    def delete(self, wh_id):
        if not self._repo.find_by_id(wh_id):
            abort(404, description="Không tìm thấy kho hàng với ID đã cho")
        self._repo.delete(wh_id)


# ─── Products ────────────────────────────────────────────────────────────────

class ProductService:
    def __init__(self):
        self._repo = ProductRepository()
        self._cat_repo = CategoryRepository()

    def get_all(self):
        return self._repo.get_all()

    def get_by_id(self, product_id):
        return self._repo.find_by_id(product_id)

    def get_by_name(self, name: str):
        return self._repo.find_by_name(name.strip().upper())

    def create(self, data: dict):
        sku = data.get('sku')
        name = data.get('product_name')
        category = data.get('category_name')
        min_stock = data.get('min_stock', 0)
        description = data.get('description')

        if not all([sku, name, category, min_stock, description]):
            abort(400, description='Thông tin sản phẩm không được để trống')

        sku = str(sku).strip().upper()
        name = str(name).strip()
        category = str(category).strip().upper()
        min_stock = int(min_stock)
        description = str(description).strip()

        cat = self._cat_repo.find_by_name(category)
        if not cat:
            abort(400, description="Loại sản phẩm không tồn tại")
        if self._repo.find_by_sku(sku):
            abort(400, description="Số định danh sản phẩm đã tồn tại")
        if self._repo.find_by_exact_name(name):
            abort(400, description="Sản phẩm đã tồn tại")
        if not self._repo.create(sku, name, cat['id'], min_stock, description):
            abort(500, description="Đã xảy ra lỗi khi thêm sản phẩm mới vào")

    def update(self, product_id, data: dict):
        sku = data.get('sku')
        name = data.get('product_name')
        category = data.get('category_name')
        min_stock = data.get('min_stock')
        description = data.get('description')

        if not all([sku, name, category, min_stock, description]):
            abort(400, description='Thông tin sản phẩm không được để trống')

        sku = str(sku).strip().upper()
        name = str(name).strip()
        category = str(category).strip().upper()
        min_stock = int(min_stock)
        description = str(description).strip()

        if not self._repo.find_id_by_id(product_id):
            abort(404, description="Sản phẩm không tồn tại")
        cat = self._cat_repo.find_by_name(category)
        if not cat:
            abort(400, description="Loại sản phẩm không tồn tại")
        if not self._repo.update(product_id, sku, name, cat['id'], min_stock, description):
            abort(500, description="Đã xảy ra lỗi khi cập nhật thông tin sản phẩm")

    def delete(self, product_id):
        if not self._repo.find_id_by_id(product_id):
            abort(404, description="Sản phẩm không tồn tại")
        if not self._repo.delete(product_id):
            abort(500, description="Đã xảy ra lỗi khi xóa thông tin sản phẩm")


# ─── Inventory ───────────────────────────────────────────────────────────────

class InventoryService:
    def __init__(self):
        self._repo = InventoryRepository()
        self._wh_repo = WarehouseRepository()
        self._prod_repo = ProductRepository()

    def _resolve_warehouse_product(self, warehouse_name, product_name):
        wh = self._wh_repo.find_by_id(warehouse_name) or \
             self._repo.query_db("SELECT id FROM Warehouses WHERE name=?", (warehouse_name,), one=True)
        prod = self._repo.query_db("SELECT id FROM Products WHERE name=?", (product_name,), one=True)
        if not wh or not prod:
            abort(400, "Warehouse or Product not found")
        return wh["id"], prod["id"]

    def get_all(self):
        return self._repo.get_all()

    def add(self, warehouse_name, product_name, quantity):
        if not all([warehouse_name, product_name, quantity]):
            abort(400, "Missing fields")
        wh = self._repo.query_db("SELECT id FROM Warehouses WHERE name=?", (warehouse_name,), one=True)
        prod = self._repo.query_db("SELECT id FROM Products WHERE name=?", (product_name,), one=True)
        if not wh or not prod:
            abort(400, "Warehouse or Product not found")
        exist = self._repo.find_by_warehouse_product(wh["id"], prod["id"])
        if exist:
            if not self._repo.add_quantity(exist["id"], quantity):
                abort(500, "Add failed")
        else:
            if not self._repo.create(wh["id"], prod["id"], quantity):
                abort(500, "Add failed")

    def remove(self, warehouse_name, product_name, quantity):
        if not all([warehouse_name, product_name, quantity]):
            abort(400, "Missing fields")
        wh = self._repo.query_db("SELECT id FROM Warehouses WHERE name=?", (warehouse_name,), one=True)
        prod = self._repo.query_db("SELECT id FROM Products WHERE name=?", (product_name,), one=True)
        if not wh or not prod:
            abort(400, "Warehouse or Product not found")
        inv = self._repo.find_by_warehouse_product(wh["id"], prod["id"])
        if not inv:
            abort(400, "Product not in warehouse")
        if inv["quantity"] < quantity:
            abort(400, "Not enough stock")
        if not self._repo.subtract_quantity(inv["id"], quantity):
            abort(500, "Remove failed")

    def update(self, inv_id, quantity):
        if not self._repo.set_quantity(inv_id, quantity):
            abort(500, "Update failed")

    def delete(self, inv_id):
        if not self._repo.find_by_id(inv_id):
            abort(404, "Inventory not found")
        if not self._repo.delete(inv_id):
            abort(500, "Delete failed")

    def search_by_product(self, name):
        return self._repo.search_by_product(name) if name else []

    def search_by_warehouse(self, name):
        return self._repo.search_by_warehouse(name) if name else []


# ─── Transfer ────────────────────────────────────────────────────────────────

class TransferService:
    def __init__(self):
        self._repo = TransferRepository()
        self._inv_repo = InventoryRepository()
        self._wh_repo = WarehouseRepository()

    def get_all(self):
        return self._repo.get_all()

    def create(self, from_wh_id, to_wh_id, staff_id, products: list):
        if not self._wh_repo.find_by_id(from_wh_id) or not self._wh_repo.find_by_id(to_wh_id):
            abort(404, "Warehouse not found")

        self._repo.create(from_wh_id, to_wh_id, staff_id)
        transfer = self._repo.find_latest()
        transfer_id = transfer['id']

        for item in products:
            product_id = item['product_id']
            qty = item['quantity']
            stock = self._inv_repo.get_stock(from_wh_id, product_id)
            if not stock or stock['quantity'] < qty:
                abort(400, f"Not enough stock for product {product_id}")
            self._inv_repo.subtract_quantity(
                self._inv_repo.find_by_warehouse_product(from_wh_id, product_id)['id'], qty
            )
            self._repo.add_detail(transfer_id, product_id, qty)

        return transfer_id

    def update_status(self, transfer_id, new_status: str):
        VALID = ["PENDING", "APPROVED"]
        if new_status not in VALID:
            abort(400, "Invalid status")
        transfer = self._repo.find_by_id(transfer_id)
        if not transfer:
            abort(404, "Transfer not found")
        if transfer['status'] == new_status:
            return
        self._repo.update_status(transfer_id, new_status)

    def suggest_warehouse(self, product_id: int, to_warehouse_id: int):
        target = self._wh_repo.find_by_id(to_warehouse_id)
        if not target:
            abort(404, "Target warehouse not found")
        inventories = self._inv_repo.find_with_stock(product_id)
        best, best_score = None, None
        for inv in inventories:
            dist = math.sqrt(
                (inv['Latitude'] - target['Latitude'])**2 +
                (inv['Longitude'] - target['Longitude'])**2
            )
            score = dist - inv['quantity'] * 0.01
            if best_score is None or score < best_score:
                best_score = score
                best = inv
        return best


# ─── Shipments ───────────────────────────────────────────────────────────────

class ShipmentService:
    def __init__(self):
        self._repo = ShipmentRepository()
        self._transfer_repo = TransferRepository()
        self._inv_repo = InventoryRepository()

    def get_all(self):
        return self._repo.get_all()

    def get_by_id(self, shipment_id):
        shipment = self._repo.find_by_transfer_id(shipment_id)
        if not shipment:
            abort(404, "Shipment not found")
        return dict(shipment)

    def create(self, transfer_id, driver_name, license_plate, expected_at_str):
        transfer = self._transfer_repo.find_by_id(transfer_id)
        if not transfer or transfer['status'] != 'APPROVED':
            abort(404, "Transfer not found")
        try:
            expected_at = datetime.fromisoformat(expected_at_str)
        except Exception:
            abort(400, "Invalid datetime format")
        if self._repo.find_by_transfer_id(transfer_id):
            abort(400, "Shipment for this Transfer ID already exists")
        self._repo.create(transfer_id, driver_name, license_plate, expected_at)

    def update(self, shipment_id, data: dict):
        VALID = ["PICKING", "SHIPPING", "DELIVERED"]
        shipment = self._repo.find_by_id(shipment_id)
        if not shipment:
            abort(404, "Shipment not found")

        old_status = shipment['status']
        status = data.get("status")
        if status and status not in VALID:
            abort(400, "Invalid status")

        fields = {}
        if status:
            fields["status"] = status
        if data.get("driver_name"):
            fields["driver_name"] = data["driver_name"]
        if data.get("license_plate"):
            fields["license_plate"] = data["license_plate"]
        if not fields:
            abort(400, "No data to update")
        if status == "DELIVERED":
            fields["actual_delivery_at"] = datetime.now()

        self._repo.update(shipment_id, fields)

        if status == "SHIPPING":
            self._transfer_repo.update_status(shipment['transfer_id'], 'SHIPPING')

        if old_status != "DELIVERED" and status == "DELIVERED":
            transfer = self._transfer_repo.find_by_id(shipment['transfer_id'])
            details = self._transfer_repo.get_details(shipment['transfer_id'])
            conn = self._repo.get_raw_connection()
            try:
                cursor = conn.cursor()
                for item in details:
                    cursor.execute(
                        "SELECT * FROM Inventory WHERE warehouse_id=? AND product_id=?",
                        (transfer['to_warehouse_id'], item['product_id'])
                    )
                    if not cursor.fetchone():
                        abort(404, "Inventory not found")
                    cursor.execute(
                        "UPDATE Inventory SET quantity = quantity + ? "
                        "WHERE warehouse_id=? AND product_id=?",
                        (item['quantity'], transfer['to_warehouse_id'], item['product_id'])
                    )
                cursor.execute(
                    "UPDATE Transfer_Orders SET status='COMPLETED' WHERE id=?",
                    (shipment['transfer_id'],)
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def delete(self, shipment_id):
        shipment = self._repo.find_by_id(shipment_id)
        if not shipment:
            abort(404, "Shipment not found")
        if shipment['status'] == "DELIVERED":
            abort(400, "Cannot delete delivered shipment")
        self._repo.delete(shipment_id)


# ─── Reports ─────────────────────────────────────────────────────────────────

class ReportService:
    def __init__(self):
        self._repo = ReportRepository()

    def get_ton_kho(self):
        result = self._repo.get_ton_kho()
        if not result:
            abort(404, description="Không có sản phẩm nào trong kho")
        return result

    def get_low_stock(self):
        result = self._repo.get_low_stock()
        if not result:
            abort(404, description="Không có sản phẩm nào sắp hết hàng")
        return result

    def get_inventory_history(self, sku: str):
        result = self._repo.get_inventory_history(sku)
        if not result:
            abort(404, description="Không tìm thấy lịch sử nhập/xuất nào cho sản phẩm này")
        return result

    def get_transfer_history(self, sku=None):
        result = self._repo.get_transfer_history(sku)
        if not result:
            abort(404, description="Không tìm thấy lịch sử điều chuyển nào cho sản phẩm này")
        return result

    def get_receipt_history(self):
        result = self._repo.get_receipt_history()
        if not result:
            abort(404, description="Không tìm thấy lịch sử phiếu nhập/xuất nào")
        return result

    def get_excel_data(self):
        return {
            "inventory": self._repo.get_excel_inventory(),
            "stock_summary": self._repo.get_excel_stock_summary(),
            "history": self._repo.get_excel_history(),
            "transfers": self._repo.get_excel_transfers(),
            "receipts": self._repo.get_receipt_history(),
        }
