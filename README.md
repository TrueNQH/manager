# Student Management System / Hệ Thống Quản Lý Học Viên

A desktop application for managing student registrations and payments, built with Python and Tkinter.

Ứng dụng desktop quản lý đăng ký và thanh toán học phí, được xây dựng bằng Python và Tkinter.

## Features / Tính năng

- User authentication with role-based access (Student/Manager)
- Student features:
  - View personal information
  - Register for courses
  - View payment status
  - Generate QR code for payment
- Manager features:
  - View student list
  - Update payment status
  - View payment statistics

- Xác thực người dùng với phân quyền (Học viên/Quản lý)
- Tính năng cho học viên:
  - Xem thông tin cá nhân
  - Đăng ký khóa học
  - Xem trạng thái thanh toán
  - Tạo mã QR thanh toán
- Tính năng cho quản lý:
  - Xem danh sách học viên
  - Cập nhật trạng thái thanh toán
  - Xem thống kê thanh toán

## Requirements / Yêu cầu

- Python 3.7 or higher
- MySQL Server
- Required Python packages (listed in requirements.txt)

- Python 3.7 trở lên
- MySQL Server
- Các gói Python cần thiết (được liệt kê trong requirements.txt)

## Installation / Cài đặt

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up the database:
- Create a MySQL database named `edufinance_manager`
- Import the database schema from `database/schema.sql`

5. Configure the application:
- Update database connection settings in `api/app.py` if needed:
```python
conn = mysql.connector.connect(
    host='localhost',
    database='edufinance_manager',
    user='root',
    password=''
)
```

## Running the Application / Chạy ứng dụng

1. Start the API server:
```bash
cd api
python app.py
```

2. In a new terminal, start the client application:
```bash
cd client
python client.py
```

## Default Accounts / Tài khoản mặc định

### Student Account / Tài khoản học viên
- Username: student1
- Password: password123

### Manager Account / Tài khoản quản lý
- Username: manager1
- Password: password123

## Project Structure / Cấu trúc dự án

```
├── api/
│   ├── app.py              # API server
│   └── requirements.txt    # API dependencies
├── client/
│   ├── client.py          # Main client application
│   └── client_new.py      # Updated client with new UI
├── database/
│   └── schema.sql         # Database schema
└── README.md              # This file
```

## Contributing / Đóng góp

Feel free to submit issues and enhancement requests!

Mọi đóng góp đều được hoan nghênh!

## License / Giấy phép

This project is licensed under the MIT License.

Dự án này được cấp phép theo MIT License. 