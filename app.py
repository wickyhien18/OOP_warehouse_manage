import os
import re

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
import pyodbc

# ─── Import blueprints từ controllers ────────────────────────────────────────
from controllers.auth_controller import auth_bp
from controllers.core_controllers import (
    users_bp, roles_bp, categories_bp, warehouses_bp
)
from controllers.domain_controllers import (
    products_bp, inventory_bp, transfer_bp, logistics_bp, reports_bp
)
from controllers.receipt_controller import receipt_bp

# ─── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)

CORS(app, supports_credentials=True,
     origins=["http://localhost:5500", "http://127.0.0.1:5500"])

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.url_map.strict_slashes = False

jwt = JWTManager(app)

app.config['SWAGGER'] = {
    'title': 'WMS API - Nhóm 4',
    'uiversion': 3,
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': "Nhập Token theo định dạng: Bearer <your_token_here>"
        }
    }
}
swagger = Swagger(app)

# ─── Register blueprints ─────────────────────────────────────────────────────
app.register_blueprint(auth_bp,       url_prefix='/api/auth')
app.register_blueprint(users_bp,      url_prefix='/api/users')
app.register_blueprint(roles_bp,      url_prefix='/api/roles')
app.register_blueprint(categories_bp, url_prefix='/api/categories')
app.register_blueprint(warehouses_bp, url_prefix='/api/warehouses')
app.register_blueprint(products_bp,   url_prefix='/api/products')
app.register_blueprint(inventory_bp,  url_prefix='/api/inventory')
app.register_blueprint(transfer_bp,   url_prefix='/api/transfers')
app.register_blueprint(logistics_bp,  url_prefix='/api/logistics')
app.register_blueprint(reports_bp,    url_prefix='/api/reports')
app.register_blueprint(receipt_bp,    url_prefix='/api/receipts')


# ─── Global error handlers ───────────────────────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify({
            "success": False,
            "error_code": f"HTTP_{e.code}",
            "message": e.description,
        }), e.code

    if isinstance(e, pyodbc.Error):
        error_msg = str(e)
        if "547" in error_msg:
            match = re.search(r'constraint "FK_([^_]+)_([^"]+)"', error_msg)
            friendly = (
                f"Không thể xóa bản ghi này vì đang có dữ liệu liên kết tại bảng '{match.group(1)}'."
                if match else
                "Không thể xóa do vi phạm ràng buộc dữ liệu liên quan."
            )
        else:
            friendly = "Lỗi cơ sở dữ liệu không xác định."
        return jsonify({
            "success": False,
            "error_code": "DB_FOREIGN_KEY_CONFLICT",
            "message": friendly
        }), 409

    response = {
        "success": False,
        "error_code": "INTERNAL_SERVER_ERROR",
        "message": "System encountered an unexpected error. Please try again later."
    }
    if app.config.get("DEBUG"):
        response["details"] = str(e)
    return jsonify(response), 500


@jwt.unauthorized_loader
def unauthorized_callback(err_str):
    return jsonify({
        "success": False,
        "error_code": "MISSING_TOKEN",
        "message": "Vui lòng cung cấp Access Token trong Header hoặc Cookie"
    }), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "success": False,
        "error_code": "TOKEN_EXPIRED",
        "message": "Phiên đăng nhập đã hết hạn, vui lòng login lại"
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(err_str):
    return jsonify({
        "success": False,
        "error_code": "INVALID_TOKEN",
        "message": "Token không hợp lệ hoặc đã bị chỉnh sửa"
    }), 401


if __name__ == '__main__':
    app.run(debug=True)
