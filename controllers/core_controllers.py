"""
controllers/core_controllers.py
Users / Roles / Categories / Warehouses blueprints.
"""
import flask
from flask import Blueprint, jsonify, abort
from flask_jwt_extended import get_jwt, jwt_required
from services.services import UserService, RoleService, CategoryService, WarehouseService

# ─── Users ───────────────────────────────────────────────────────────────────
users_bp = Blueprint('users', __name__)
_user_svc = UserService()


@users_bp.route('/', methods=['POST'])
def register():
    """
    API Đăng ký tài khoản người dùng mới
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_name:
              type: string
              example: "nhanvien01"
            password:
              type: string
              example: "B$ecure2026"
    responses:
      200:
        description: Đăng ký thành công
      400:
        description: Dữ liệu không hợp lệ
      500:
        description: Lỗi server
    """
    payload = flask.request.get_json(silent=True) or {}
    _user_svc.register(payload.get("user_name"), payload.get("password"))
    return jsonify({"success": True, "message": "Tài khoản mới đã được tạo"}), 200


@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """
    API Lấy danh sách người dùng
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Danh sách người dùng
      404:
        description: Không tìm thấy người dùng
    """
    users = _user_svc.get_list(
        flask.request.args.get("id"),
        flask.request.args.get("username")
    )
    return jsonify({"success": True, "data": users}), 200


@users_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def change_password(id):
    """
    API Đổi mật khẩu
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            password:
              type: string
              example: "B$ecure2026"
    responses:
      200:
        description: Cập nhật thành công
      400:
        description: Mật khẩu yếu
      404:
        description: Không tìm thấy người dùng
    """
    payload = flask.request.get_json(silent=True) or {}
    _user_svc.change_password(id, payload.get("password"))
    return jsonify({"success": True, "message": "Mật khẩu đã được cập nhật"}), 200


@users_bp.route('/', methods=['PUT'])
@jwt_required()
def update_user_role():
    """
    API Cập nhật vai trò người dùng
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 1
            role_id:
              type: integer
              example: 2
    responses:
      200:
        description: Cập nhật thành công
      403:
        description: Không có quyền
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    payload = flask.request.get_json(silent=True) or {}
    _user_svc.update_role(payload.get("user_id"), payload.get("role_id"))
    return jsonify({"success": True, "message": "Vai trò của người dùng đã được cập nhật"}), 200


@users_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    """
    API Xóa người dùng
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Đã xóa
      403:
        description: Không có quyền
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    _user_svc.delete(id)
    return jsonify({"success": True, "message": "Người dùng đã được xóa"}), 200


# ─── Roles ───────────────────────────────────────────────────────────────────
roles_bp = Blueprint('roles', __name__)
_role_svc = RoleService()


def _require_admin():
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")


@roles_bp.route('/', methods=['GET'])
@jwt_required()
def get_roles():
    """
    API Lấy danh sách vai trò
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    responses:
      200:
        description: Danh sách vai trò
    """
    _require_admin()
    roles = _role_svc.get_list(
        flask.request.args.get("id"),
        flask.request.args.get("role_name")
    )
    return jsonify({"success": True, "data": roles}), 200


@roles_bp.route('/', methods=['POST'])
@jwt_required()
def create_role():
    """
    API Tạo vai trò mới
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            role_name:
              type: string
              example: "Manager"
    responses:
      200:
        description: Tạo thành công
    """
    _require_admin()
    payload = flask.request.get_json(silent=True) or {}
    _role_svc.create(payload.get("role_name"))
    return jsonify({"success": True, "message": "Vai trò mới đã được tạo"}), 200


@roles_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def update_role(id):
    """
    API Cập nhật vai trò
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Cập nhật thành công
    """
    _require_admin()
    payload = flask.request.get_json(silent=True) or {}
    _role_svc.update(id, payload.get("role_name"))
    return jsonify({"success": True, "message": "Vai trò đã được cập nhật"}), 200


@roles_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_role(id):
    """
    API Xóa vai trò
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Đã xóa
    """
    _require_admin()
    _role_svc.delete(id)
    return jsonify({"success": True, "message": "Vai trò đã được xóa"}), 200


# ─── Categories ──────────────────────────────────────────────────────────────
categories_bp = Blueprint('categories', __name__)
_cat_svc = CategoryService()


@categories_bp.route('/', methods=['GET'])
@jwt_required()
def get_categories():
    """
    API Lấy danh sách danh mục
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    responses:
      200:
        description: Danh sách danh mục
    """
    cats = _cat_svc.get_list(
        flask.request.args.get("id"),
        flask.request.args.get("name")
    )
    return jsonify({"success": True, "data": cats}), 200


@categories_bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    """
    API Tạo danh mục mới
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "Điện tử"
    responses:
      200:
        description: Tạo thành công
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    payload = flask.request.get_json(silent=True) or {}
    _cat_svc.create(payload.get("name"))
    return jsonify({"success": True, "message": "Danh mục đã được tạo thành công"}), 200


@categories_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def update_category(id):
    """
    API Cập nhật danh mục
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Cập nhật thành công
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    payload = flask.request.get_json(silent=True) or {}
    _cat_svc.update(id, payload.get("name"))
    return jsonify({"success": True, "message": "Danh mục đã được cập nhật"}), 200


@categories_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_category(id):
    """
    API Xóa danh mục
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Đã xóa
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    _cat_svc.delete(id)
    return jsonify({"success": True, "message": "Danh mục đã được xóa"}), 200


# ─── Warehouses ──────────────────────────────────────────────────────────────
warehouses_bp = Blueprint('warehouses', __name__)
_wh_svc = WarehouseService()


@warehouses_bp.route('/', methods=['GET'])
@jwt_required()
def get_warehouses():
    """
    API Lấy danh sách kho hàng
    ---
    tags:
      - Warehouses
    security:
      - Bearer: []
    responses:
      200:
        description: Danh sách kho
    """
    result = _wh_svc.get_list(
        flask.request.args.get("id"),
        flask.request.args.get("name")
    )
    return jsonify({"success": True, "data": result}), 200


@warehouses_bp.route('/', methods=['POST'])
@jwt_required()
def create_warehouse():
    """
    API Tạo kho hàng mới
    ---
    tags:
      - Warehouses
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "Kho A"
            address:
              type: string
              example: "Hà Nội"
            capacity:
              type: integer
              example: 1000
            latitude:
              type: number
              example: 21.028511
            longitude:
              type: number
              example: 105.804817
    responses:
      200:
        description: Tạo thành công
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    payload = flask.request.get_json(silent=True) or {}
    _wh_svc.create(
        payload.get("name"), payload.get("address"),
        payload.get("capacity"), payload.get("longitude"), payload.get("latitude")
    )
    return jsonify({"success": True, "message": "Kho hàng mới đã được tạo"}), 200


@warehouses_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def update_warehouse(id):
    """
    API Cập nhật kho hàng
    ---
    tags:
      - Warehouses
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Cập nhật thành công
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    payload = flask.request.get_json(silent=True) or {}
    _wh_svc.update(id, payload)
    return jsonify({"success": True, "message": "Kho hàng đã được cập nhật"}), 200


@warehouses_bp.route('/<id>', methods=['DELETE'])
@jwt_required()
def delete_warehouse(id):
    """
    API Xóa kho hàng
    ---
    tags:
      - Warehouses
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Đã xóa
    """
    if get_jwt().get("role") != "ADMIN":
        abort(403, description="Bạn không có quyền thực hiện hành động này")
    _wh_svc.delete(id)
    return jsonify({"success": True, "message": "Kho đã được xóa"}), 200
