"""
controllers/receipt_controller.py
7 endpoints - thứ tự route: string cụ thể trước, parameter sau.
"""
from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import get_jwt, jwt_required
from services.receipt_service import ReceiptService

receipt_bp = Blueprint('receipts', __name__)
_svc = ReceiptService()


# ── GET / ─────────────────────────────────────────────────────────────────────
@receipt_bp.route("/", methods=["GET"])
@jwt_required()
def get_all_receipts():
    """
    API Lấy danh sách toàn bộ phiếu kèm chi tiết
    ---
    tags:
      - Receipt
    security:
      - Bearer: []
    responses:
      200:
        description: Danh sách tất cả phiếu nhập/xuất
    """
    return jsonify(_svc.get_all()), 200


# ── GET /inbound ──────────────────────────────────────────────────────────────
@receipt_bp.route('/inbound', methods=['GET'])
@jwt_required()
def get_inbound_receipts():
    """
    API Lấy danh sách Phiếu Nhập kèm chi tiết
    ---
    tags:
      - Receipt
    security:
      - Bearer: []
    responses:
      200:
        description: Danh sách phiếu nhập
    """
    return jsonify(_svc.get_by_type('INBOUND')), 200


# ── GET /outbound ─────────────────────────────────────────────────────────────
@receipt_bp.route('/outbound', methods=['GET'])
@jwt_required()
def get_outbound_receipts():
    """
    API Lấy danh sách Phiếu Xuất kèm chi tiết
    ---
    tags:
      - Receipt
    security:
      - Bearer: []
    responses:
      200:
        description: Danh sách phiếu xuất
    """
    return jsonify(_svc.get_by_type('OUTBOUND')), 200


# ── GET /<id> ─────────────────────────────────────────────────────────────────
@receipt_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_receipt_by_id(id):
    """
    API Lấy chi tiết một phiếu theo ID
    ---
    tags:
      - Receipt
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Chi tiết phiếu
      404:
        description: Không tìm thấy phiếu
    """
    return jsonify(_svc.get_by_id(id)), 200


# ── POST /inbound ─────────────────────────────────────────────────────────────
@receipt_bp.route('/inbound', methods=['POST'])
@jwt_required()
def create_inbound():
    """
    API Tạo phiếu nhập sản phẩm và cập nhật kho
    ---
    tags:
      - Receipt
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [warehouse_name, staff_name, partner_name, items]
          properties:
            warehouse_name: {type: string, example: "KHO QUẬN 1"}
            staff_name: {type: string, example: "NGUYEN VAN A"}
            partner_name: {type: string, example: "Công ty ABC"}
            items:
              type: array
              items:
                type: object
                properties:
                  product_name: {type: string}
                  quantity: {type: integer}
                  price: {type: number}
    responses:
      200:
        description: Đã thêm thông tin phiếu nhập thành công
      400:
        description: Dữ liệu không hợp lệ
      500:
        description: Lỗi hệ thống
    """
    data = request.get_json() or {}
    _svc.create_inbound(
        data.get('warehouse_name'), data.get('staff_name'),
        data.get('partner_name'), data.get('items')
    )
    return jsonify({"success": True, "message": "Đã thêm thông tin phiếu nhập thành công"}), 200


# ── POST /outbound ────────────────────────────────────────────────────────────
@receipt_bp.route('/outbound', methods=['POST'])
@jwt_required()
def create_outbound():
    """
    API Tạo phiếu xuất sản phẩm và cập nhật kho
    ---
    tags:
      - Receipt
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [warehouse_name, staff_name, partner_name, items]
          properties:
            warehouse_name: {type: string, example: "KHO QUẬN 1"}
            staff_name: {type: string, example: "NGUYEN VAN A"}
            partner_name: {type: string, example: "Công ty ABC"}
            items:
              type: array
              items:
                type: object
                properties:
                  product_name: {type: string}
                  quantity: {type: integer}
                  price: {type: number}
    responses:
      200:
        description: Đã thêm thông tin phiếu xuất thành công
      400:
        description: Dữ liệu không hợp lệ hoặc không đủ tồn kho
      500:
        description: Lỗi hệ thống
    """
    data = request.get_json() or {}
    _svc.create_outbound(
        data.get('warehouse_name'), data.get('staff_name'),
        data.get('partner_name'), data.get('items')
    )
    return jsonify({"success": True, "message": "Đã thêm thông tin phiếu xuất thành công"}), 200


# ── DELETE /<id> ──────────────────────────────────────────────────────────────
@receipt_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_receipt(id):
    """
    API Xóa phiếu nhập/xuất theo ID
    ---
    tags:
      - Receipt
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Xóa thành công
      403:
        description: Không có quyền
      404:
        description: Không tìm thấy phiếu
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    _svc.delete(id)
    return jsonify({"success": True, "message": "Xóa thông tin phiếu thành công"}), 200