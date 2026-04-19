"""
controllers/auth_controller.py
"""
from flask import Blueprint, jsonify, make_response
from flask_jwt_extended import jwt_required
from services.services import AuthService

auth_bp = Blueprint('auth', __name__)
_svc = AuthService()


@auth_bp.route('/', methods=['POST'])
def login():
    """
    API Đăng nhập để lấy Access Token
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: 123456
            remember_me:
              type: boolean
              example: false
    responses:
      200:
        description: Đăng nhập thành công
      400:
        description: Thiếu thông tin
      401:
        description: Sai tên đăng nhập hoặc mật khẩu
    """
    import flask
    payload = flask.request.get_json(silent=True) or {}
    token, user = _svc.login(payload.get("username"), payload.get("password"))
    remember_me = payload.get("remember_me", False)
    expires_delta = 2592000 if remember_me else 86400

    response = make_response(jsonify({
        "success": True,
        "message": "Đăng nhập thành công",
        "user_info": {"username": user['username'], "role": user['role_name']}
    }))
    response.set_cookie('access_token', token, httponly=True,
                        secure=True, samesite='None', max_age=expires_delta)
    return response, 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    API Đăng xuất
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: Đăng xuất thành công
    """
    response = make_response(jsonify({"success": True, "message": "Đăng xuất thành công"}))
    response.set_cookie('access_token', '', httponly=True,
                        secure=True, samesite='None', max_age=0)
    return response, 200
