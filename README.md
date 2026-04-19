# Warehouse Management System (WMS)

## Requirements

- Flask
- Flask-Cors
- Flasgger
- pyodbc
- python-dotenv
- Flask-JWT-Extended
- openpyxl
- pandas
- Werkzeug

Cài đặt toàn bộ dependencies:

```bash
pip install -r requirements.txt
```

## Database Setup

1. Đọc file `database.txt` để xem thông tin cơ sở dữ liệu.
2. Tham khảo `.env.example` và tạo file `.env` của bạn:

```env
DB_DRIVER={ODBC Driver 17 for SQL Server}
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=warehouse_db
DB_TRUSTED_CONNECTION=yes
DB_USER=
DB_PASSWORD=
JWT_SECRET_KEY=your_secret_key_here
```

3. Kiểm tra kết nối database:

```bash
python test_db.py
```

4. Kiểm tra danh sách ODBC driver có sẵn trên máy (nếu gặp lỗi kết nối):

```python
import pyodbc
print(pyodbc.drivers())
```

## Khởi chạy

```bash
python app.py
```

Swagger UI: [http://localhost:5000/apidocs](http://localhost:5000/apidocs)

## Project Structure

```text
wms/
│
├── app.py                          # Entry point — khởi tạo Flask app, đăng ký blueprints
├── test_db.py                      # Script kiểm tra kết nối database
│
├── helpers/
│   ├── db_helper.py                # DatabaseConnection + BaseRepository (query_db, execute_db)
│   └── validate_helper.py          # Validator class (is_empty, validate_email, validate_password_strength)
│
├── repositories/                   # Tầng truy vấn DB — chỉ chứa SQL, không có business logic
│   ├── core_repositories.py        # AuthRepository, UserRepository, RoleRepository, CategoryRepository
│   ├── domain_repositories.py      # WarehouseRepository, ProductRepository, InventoryRepository,
│   │                               # TransferRepository, ShipmentRepository, ReportRepository
│   └── receipt_repository.py       # ReceiptRepository (inbound/outbound/logs)
│
├── services/                       # Tầng business logic — validate, xử lý nghiệp vụ, gọi repository
│   ├── services.py                 # AuthService, UserService, RoleService, CategoryService,
│   │                               # WarehouseService, ProductService, InventoryService,
│   │                               # TransferService, ShipmentService, ReportService
│   └── receipt_service.py          # ReceiptService (inbound, outbound, get, delete)
│
└── controllers/                    # Tầng controller — parse request, gọi service, trả response
    ├── auth_controller.py          # POST /api/auth/ (login), POST /api/auth/logout
    ├── core_controllers.py         # /api/users, /api/roles, /api/categories, /api/warehouses
    ├── domain_controllers.py       # /api/products, /api/inventory, /api/transfers,
    │                               # /api/logistics, /api/reports
    └── receipt_controller.py       # /api/receipts (inbound, outbound, CRUD)
```

## API Endpoints

### Auth — `/api/auth`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/` | Đăng nhập, nhận JWT cookie |
| POST | `/logout` | Đăng xuất, xóa cookie |

### Users — `/api/users`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/` | Đăng ký tài khoản mới (mặc định role STAFF) |
| GET | `/` | Lấy danh sách người dùng |
| PUT | `/` | Cập nhật vai trò người dùng (ADMIN) |
| PUT | `/<id>` | Đổi mật khẩu |
| DELETE | `/<id>` | Xóa người dùng (ADMIN) |

### Roles — `/api/roles`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy danh sách vai trò (ADMIN) |
| POST | `/` | Tạo vai trò mới (ADMIN) |
| PUT | `/<id>` | Cập nhật vai trò (ADMIN) |
| DELETE | `/<id>` | Xóa vai trò (ADMIN) |

### Categories — `/api/categories`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy danh sách danh mục |
| POST | `/` | Tạo danh mục mới (ADMIN) |
| PUT | `/<id>` | Cập nhật danh mục (ADMIN) |
| DELETE | `/<id>` | Xóa danh mục (ADMIN) |

### Warehouses — `/api/warehouses`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy danh sách kho hàng |
| POST | `/` | Tạo kho mới (ADMIN) |
| PUT | `/<id>` | Cập nhật kho (ADMIN) |
| DELETE | `/<id>` | Xóa kho (ADMIN) |

### Products — `/api/products`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy danh sách sản phẩm |
| GET | `/<id>` | Lấy sản phẩm theo ID |
| GET | `/name=<name>` | Tìm sản phẩm theo tên |
| POST | `/` | Thêm sản phẩm mới |
| PUT | `/<id>` | Cập nhật sản phẩm (MANAGER) |
| DELETE | `/<id>` | Xóa sản phẩm (MANAGER) |

### Inventory — `/api/inventory`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy toàn bộ tồn kho |
| POST | `/add` | Cộng số lượng vào kho |
| POST | `/remove` | Trừ số lượng khỏi kho |
| PUT | `/update/<id>` | Cập nhật số lượng trực tiếp |
| DELETE | `/delete/<id>` | Xóa bản ghi tồn kho |
| GET | `/search/product` | Tìm theo tên sản phẩm |
| GET | `/search/warehouse` | Tìm theo tên kho |

### Receipts — `/api/receipts`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy toàn bộ phiếu nhập/xuất |
| GET | `/inbound` | Lấy danh sách phiếu nhập |
| GET | `/outbound` | Lấy danh sách phiếu xuất |
| GET | `/<id>` | Lấy chi tiết một phiếu |
| POST | `/inbound` | Tạo phiếu nhập, cập nhật tồn kho |
| POST | `/outbound` | Tạo phiếu xuất, cập nhật tồn kho |
| DELETE | `/<id>` | Xóa phiếu (ADMIN) |

### Transfers — `/api/transfers`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy danh sách lệnh điều chuyển |
| POST | `/transfers` | Tạo lệnh điều chuyển mới |
| PUT | `/transfers/<id>` | Cập nhật trạng thái lệnh |
| GET | `/transfers/suggest` | Gợi ý kho nguồn tốt nhất |

### Logistics (Shipments) — `/api/logistics`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/shipments` | Lấy danh sách vận đơn |
| GET | `/shipments/<id>` | Lấy vận đơn theo ID |
| POST | `/shipments` | Tạo vận đơn mới |
| PUT | `/shipments/<id>` | Cập nhật trạng thái vận đơn |
| DELETE | `/shipments/<id>` | Xóa vận đơn |

### Reports — `/api/reports`
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `` | Tồn kho hiện tại |
| GET | `/low-stock` | Sản phẩm sắp hết hàng |
| GET | `/history/<sku>` | Lịch sử nhập/xuất theo SKU |
| GET | `/transfer-history` | Lịch sử điều chuyển |
| GET | `/receipt` | Lịch sử phiếu nhập/xuất |
| GET | `/export/excel` | Xuất báo cáo tổng hợp ra file Excel |

## Architecture

Dự án áp dụng pattern **3 tầng (3-Layer Architecture)**:

```
Request → Controller → Service → Repository → Database
```

- **Controller**: Chỉ parse request và trả response. Không chứa business logic.
- **Service**: Toàn bộ business logic, validation, kiểm tra quyền nghiệp vụ.
- **Repository**: Chỉ chứa câu SQL. Mọi class kế thừa `BaseRepository`.
