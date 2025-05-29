from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
)
import mysql.connector
from mysql.connector import Error
from passlib.hash import bcrypt

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "cho1nguoi"  # Đổi key này cho bảo mật
jwt = JWTManager(app)

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='edufinance_manager',
            user='root',
            password=''
        )
        return conn
    except Error as e:
        print("Error connecting to MySQL", e)
        return None

# Helper kiểm tra role
def role_required(required_roles):
    def decorator(func):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            if user_role not in required_roles:
                return jsonify(msg="Không có quyền truy cập"), 403
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator




# Đăng nhập user, trả về JWT token
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not bcrypt.verify(password, user['password_hash']):
        return jsonify(msg="Sai tên đăng nhập hoặc mật khẩu"), 401

    access_token = create_access_token(identity=str(user['id']), additional_claims={"role": user['role']})
    return jsonify(access_token=access_token, role=user['role'])

# Ví dụ route dành cho học viên xem thông tin cá nhân
@app.route('/student/profile', methods=['GET'])
@role_required(['student'])
def student_profile():
    user_id = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT s.id, s.name, s.phone FROM students s JOIN users u ON s.user_id = u.id WHERE u.id = %s", (user_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    if not student:
        return jsonify(msg="Không tìm thấy thông tin học viên"), 404
    return jsonify(student)
@app.route('/student/total-fee', methods=['GET'])
@role_required(['student'])
def get_total_fee():
    user_id = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM students WHERE user_id = %s", (user_id,))
    student = cursor.fetchone()
    if not student:
        cursor.close()
        conn.close()
        return jsonify(msg="Học viên không tồn tại"), 404
    student_id = student[0]

    cursor.execute("""
        SELECT SUM(c.fee) FROM registrations r
        JOIN courses c ON r.course_id = c.id
        WHERE r.student_id = %s
    """, (student_id,))
    total_fee = cursor.fetchone()[0] or 0

    cursor.close()
    conn.close()
    return jsonify(total_fee=float(total_fee))
# Ví dụ route cho học viên đăng ký môn học
@app.route('/student/register-course', methods=['POST'])
@role_required(['student'])
def register_course():
    user_id = get_jwt_identity()
    data = request.json
    course_id = data.get('course_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    # Lấy student_id từ user_id
    cursor.execute("SELECT id FROM students WHERE user_id=%s", (user_id,))
    student_id = cursor.fetchone()
    if not student_id:
        cursor.close()
        conn.close()
        return jsonify(msg="Học viên không tồn tại"), 404
    student_id = student_id[0]

    # Kiểm tra đã đăng ký chưa
    cursor.execute("SELECT * FROM registrations WHERE student_id=%s AND course_id=%s", (student_id, course_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify(msg="Đã đăng ký môn học này"), 400

    # Thêm đăng ký
    cursor.execute("INSERT INTO registrations (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
    conn.commit()

    # Tính lại tổng học phí các môn đã đăng ký
    cursor.execute("""
        SELECT SUM(c.fee) FROM registrations r
        JOIN courses c ON r.course_id = c.id
        WHERE r.student_id = %s
    """, (student_id,))
    total_fee = cursor.fetchone()[0] or 0

    # Kiểm tra đã có payment chưa
    cursor.execute("SELECT id FROM payments WHERE student_id=%s", (student_id,))
    payment = cursor.fetchone()
    if payment:
        # Nếu đã có, cập nhật lại amount và đặt trạng thái về pending
        cursor.execute("UPDATE payments SET amount=%s, status='pending' WHERE student_id=%s", (total_fee, student_id))
    else:
        # Nếu chưa có, tạo mới
        cursor.execute("INSERT INTO payments (student_id, amount, status) VALUES (%s, %s, 'pending')", (student_id, total_fee))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify(msg="Đăng ký môn học thành công")
# Route học viên xem học phí, trạng thái thanh toán
@app.route('/student/payment-status', methods=['GET'])
@role_required(['student'])
def student_payment_status():
    user_id = get_jwt_identity()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Lấy student_id từ user_id
    cursor.execute("SELECT id FROM students WHERE user_id=%s", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.close()
        conn.close()
        return jsonify(msg="Không tìm thấy học viên"), 404
    student_id = res['id']

    # Tính tổng học phí các môn đã đăng ký
    cursor.execute("""
        SELECT SUM(c.fee) as total_fee
        FROM registrations r
        JOIN courses c ON r.course_id = c.id
        WHERE r.student_id = %s
    """, (student_id,))
    total_fee = cursor.fetchone()['total_fee'] or 0

    # Đóng cursor này trước khi mở cursor mới
    cursor.close()

    # Tạo cursor mới cho truy vấn tiếp theo
    cursor2 = conn.cursor(dictionary=True)
    cursor2.execute("""
        SELECT id, status, amount, payment_date
        FROM payments
        WHERE student_id = %s
        ORDER BY payment_date DESC
        LIMIT 1
    """, (student_id,))
    payment = cursor2.fetchone()
    cursor2.close()
    conn.close()

    return jsonify({
        'total_fee': float(total_fee),
        'last_payment_status': payment['status'] if payment else 'chưa thanh toán',
        'last_payment_amount': float(payment['amount']) if payment else 0,
        'last_payment_date': payment['payment_date'].isoformat() if payment else None,
        'payment_id': payment['id'] if payment else None
    })

@app.route('/courses', methods=['GET'])
# @role_required(['student', 'manager'])
def get_courses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, fee FROM courses")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(courses)

# Ví dụ route dành cho quản lý xem danh sách học viên
@app.route('/manager/students', methods=['GET'])
@role_required(['manager'])
def manager_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT s.id, s.name, s.phone FROM students s")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(students)


# Route quản lý cập nhật trạng thái học phí
@app.route('/manager/update-payment-status', methods=['POST'])
@role_required(['manager'])
def update_payment_status():
    data = request.json
    payment_id = data.get('payment_id')
    new_status = data.get('status')  # 'pending' hoặc 'paid'

    if new_status not in ['pending', 'paid']:
        return jsonify(msg="Trạng thái không hợp lệ"), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM payments WHERE id=%s", (payment_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify(msg="Thanh toán không tồn tại"), 404

    cursor.execute("UPDATE payments SET status=%s WHERE id=%s", (new_status, payment_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(msg="Cập nhật trạng thái thanh toán thành công")



@app.route('/manager/payment-stats', methods=['GET'])
@role_required(['manager'])
def payment_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM payments
        GROUP BY status
    """)
    stats = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)
