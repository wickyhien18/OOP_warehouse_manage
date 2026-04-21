"""
services/receipt_service.py
Business logic cho Receipt: inbound, outbound, get, delete.
"""
from flask import abort
from repositories.receipt_repository import ReceiptRepository


class ReceiptService:

    def __init__(self):
        self._repo = ReceiptRepository()

    # ── Shared validation ─────────────────────────────────────────────────────

    def _resolve_warehouse(self, name: str):
        name = str(name).strip().upper()
        wh = self._repo.find_warehouse_by_name(name)
        if not wh:
            abort(400, description="Tên nhà kho không tồn tại")
        return wh['id']

    def _resolve_staff(self, name: str):
        name = str(name).strip().upper()
        staff = self._repo.find_staff_by_username(name)
        if not staff:
            abort(400, description="Nhân viên không tồn tại")
        return staff['id']

    def _validate_products_exist(self, items: list):
        names = [item['product_name'] for item in items]
        exist_rows = self._repo.find_products_by_names(names)
        exist_names = {row['name'] for row in exist_rows}
        for name in names:
            if name not in exist_names:
                abort(400, description=f"Sản phẩm '{name}' không tồn tại. Hãy tạo mới")

    def _validate_outbound_stock(self, warehouse_id, items: list):
        for item in items:
            name = item['product_name']
            quantity = int(item['quantity'])
            product_id = self._repo.find_product_id_by_name(name)
            inv = self._repo.find_inventory(warehouse_id, product_id)
            if not inv:
                abort(400, description=f"Sản phẩm '{name}' không có trong kho")
            if inv['quantity'] < quantity:
                abort(400, description=(
                    f"Sản phẩm '{name}' không đủ số lượng. "
                    f"Tồn kho: {inv['quantity']}, yêu cầu: {quantity}"
                ))

    # ── Create inbound ────────────────────────────────────────────────────────

    def create_inbound(self, warehouse_name, staff_name, partner_name, items):
        if not all([warehouse_name, staff_name, partner_name, items]):
            abort(400, description="Thông tin phiếu nhập không được để trống")

        warehouse_id = self._resolve_warehouse(warehouse_name)
        staff_id = self._resolve_staff(staff_name)
        partner_name = str(partner_name).strip()

        self._validate_products_exist(items)

        receipt_id = self._repo.create_receipt('INBOUND', warehouse_id, staff_id, partner_name)
        if not receipt_id:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin phiếu")

        for item in items:
            name = item['product_name']
            quantity = int(item['quantity'])
            price = item['price']
            product_id = self._repo.find_product_id_by_name(name)

            if not self._repo.add_detail(receipt_id, product_id, quantity, price):
                abort(500, description="Đã xảy ra lỗi khi thêm thông tin chi tiết phiếu")

            inv = self._repo.find_inventory(warehouse_id, product_id)
            if inv is None:
                if not self._repo.create_inventory(warehouse_id, product_id, quantity):
                    abort(500, description="Đã xảy ra lỗi khi thêm sản phẩm vào kho")
            else:
                if not self._repo.add_inventory(inv['id'], quantity):
                    abort(500, description="Đã xảy ra lỗi khi cập nhật số lượng sản phẩm trong kho")

            if not self._repo.add_inventory_log(product_id, warehouse_id, quantity, 'INBOUND', receipt_id):
                abort(500, description="Đã xảy ra lỗi khi thêm thông tin nhật ký kho")

    # ── Create outbound ───────────────────────────────────────────────────────

    def create_outbound(self, warehouse_name, staff_name, partner_name, items):
        if not all([warehouse_name, staff_name, partner_name, items]):
            abort(400, description="Thông tin phiếu xuất không được để trống")

        warehouse_id = self._resolve_warehouse(warehouse_name)
        staff_id = self._resolve_staff(staff_name)
        partner_name = str(partner_name).strip()

        self._validate_products_exist(items)
        self._validate_outbound_stock(warehouse_id, items)

        receipt_id = self._repo.create_receipt('OUTBOUND', warehouse_id, staff_id, partner_name)
        if not receipt_id:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin phiếu")

        for item in items:
            name = item['product_name']
            quantity = int(item['quantity'])
            price = item['price']
            product_id = self._repo.find_product_id_by_name(name)

            if not self._repo.add_detail(receipt_id, product_id, quantity, price):
                abort(500, description="Đã xảy ra lỗi khi thêm thông tin chi tiết phiếu")

            inv = self._repo.find_inventory(warehouse_id, product_id)
            if not self._repo.subtract_inventory(inv['id'], quantity):
                abort(500, description="Đã xảy ra lỗi khi cập nhật số lượng sản phẩm trong kho")

            if not self._repo.add_inventory_log(product_id, warehouse_id, quantity, 'OUTBOUND', receipt_id):
                abort(500, description="Đã xảy ra lỗi khi thêm thông tin nhật ký kho")

        # ── Create audit (Kiểm kê) ────────────────────────────────────────────────

    def create_audit(self, warehouse_name, staff_name, partner_name, items):
        """
        Xử lý nghiệp vụ kiểm kê: Tính chênh lệch và cập nhật lại tồn kho thực tế.
        """
        if not all([warehouse_name, staff_name, partner_name, items]):
            abort(400, description="Thông tin phiếu kiểm kê không được để trống")

        warehouse_id = self._resolve_warehouse(warehouse_name)
        staff_id = self._resolve_staff(staff_name)
        partner_name = str(partner_name).strip()

        self._validate_products_exist(items)

        # 1. Tạo phiếu với type 'AUDIT'
        receipt_id = self._repo.create_receipt('AUDIT', warehouse_id, staff_id, partner_name)
        if not receipt_id:
            abort(500, description="Đã xảy ra lỗi khi thêm thông tin phiếu kiểm kê")

        for item in items:
            name = item['product_name']
            actual_qty = int(item['quantity'])
            product_id = self._repo.find_product_id_by_name(name)

            # Lấy thông tin tồn kho hiện tại trong hệ thống
            inv = self._repo.find_inventory(warehouse_id, product_id)
            system_qty = inv['quantity'] if inv else 0

            # Tính toán chênh lệch để ghi Log (Thực tế - Hệ thống)
            diff_qty = actual_qty - system_qty

            if inv is None:
                # Nếu chưa có bản ghi trong Inventory, phải tạo mới
                if not self._repo.create_inventory(warehouse_id, product_id, actual_qty):
                    abort(500, description="Lỗi tạo tồn kho mới")
            else:
                # Nếu đã có, dùng hàm set_inventory_absolute vừa thêm ở bước 1
                if not self._repo.set_inventory_absolute(inv['id'], actual_qty):
                    abort(500, description="Lỗi cập nhật tồn kho tuyệt đối")

            # 2. Thêm chi tiết phiếu (Giá kiểm kê mặc định là 0)
            if not self._repo.add_detail(receipt_id, product_id, actual_qty, 0):
                abort(500, description="Đã xảy ra lỗi khi thêm chi tiết phiếu kiểm kê")

            # 3. Cập nhật số dư kho khớp với số lượng thực tế
            if inv is None:
                if not self._repo.create_inventory(warehouse_id, product_id, actual_qty):
                    abort(500, description="Đã xảy ra lỗi khi tạo tồn kho mới từ kiểm kê")
            else:
                # Dùng hàm set_inventory_absolute đã thêm vào Repository
                if not self._repo.set_inventory_absolute(inv['id'], actual_qty):
                    abort(500, description="Đã xảy ra lỗi khi điều chỉnh tồn kho")

            # 4. Ghi nhật ký biến động với số lượng chênh lệch (AUDIT)
            if not self._repo.add_inventory_log(product_id, warehouse_id, diff_qty, 'AUDIT', receipt_id):
                abort(500, description="Đã xảy ra lỗi khi ghi nhật ký kiểm kê")

    # ── Read ──────────────────────────────────────────────────────────────────

    def _group_rows(self, rows: list, type_key='type') -> list:
        """Gom các row có cùng receipt_id thành 1 object với mảng items."""
        result = {}
        for row in rows:
            rid = row.get('receipt_id') or row.get('id')
            if rid not in result:
                result[rid] = {
                    "id": rid,
                    "type": row.get('type'),
                    "warehouse_name": row['warehouse_name'],
                    "staff_name": row['staff_name'],
                    "partner_name": row['partner_name'],
                    "created_at": str(row['created_at']),
                    "items": []
                }
            result[rid]['items'].append({
                "product_name": row['product_name'],
                "sku": row['sku'],
                "quantity": row['quantity'],
                "price": row['price'],
                "total_price": row['quantity'] * row['price']
            })
        return list(result.values())

    def get_all(self) -> list:
        return self._group_rows(self._repo.get_all_raw())

    def get_by_type(self, receipt_type: str) -> list:
        return self._group_rows(self._repo.get_by_type_raw(receipt_type))

    def get_by_id(self, receipt_id) -> dict:
        rows = self._repo.get_by_id_raw(receipt_id)
        if not rows:
            abort(404, description="Không tìm thấy phiếu")
        grouped = self._group_rows(rows)
        return grouped[0]

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, receipt_id):
        if not self._repo.find_receipt_by_id(receipt_id):
            abort(404, description="Thông tin phiếu không tồn tại")
        self._repo.delete(receipt_id)