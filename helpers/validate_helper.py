import re


class Validator:
    """Tập hợp các phương thức validate dùng chung."""

    @staticmethod
    def is_empty(value) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        return False

    @staticmethod
    def validate_email(email: str) -> bool:
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(regex, email))

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Mật khẩu hợp lệ khi:
        - Ít nhất 8 ký tự
        - Không chứa khoảng trắng
        - Có chữ hoa, chữ thường, số và ký tự đặc biệt
        """
        if len(password) < 8:
            return False
        if re.search(r"\s", password):
            return False
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        return all([has_upper, has_lower, has_digit, has_special])

    @staticmethod
    def is_numeric(value) -> bool:
        return str(value).isdigit()


# ─── Backward-compat functions ───────────────────────────────────────────────
def is_empty(value):
    return Validator.is_empty(value)

def validate_email(email):
    return Validator.validate_email(email)

def validate_password_strength(password):
    return Validator.validate_password_strength(password)

def is_numeric(value):
    return Validator.is_numeric(value)
