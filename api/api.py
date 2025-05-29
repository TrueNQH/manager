from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

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

# Thêm học viên
@app.route('/students', methods=['POST'])
def add_student():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name, phone) VALUES (%s, %s)", (name, phone))
    conn.commit()
    student_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({'id': student_id, 'name': name, 'phone': phone}), 201

# Lấy danh sách học viên
@app.route('/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(students)

# Thêm giao dịch thu/chi
@app.route('/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    student_id = data.get('student_id')
    t_type = data.get('type')  # 'income' hoặc 'expense'
    amount = data.get('amount')
    description = data.get('description')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (student_id, type, amount, description) VALUES (%s, %s, %s, %s)",
        (student_id, t_type, amount, description)
    )
    conn.commit()
    trans_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({'id': trans_id, 'student_id': student_id, 'type': t_type, 'amount': amount, 'description': description}), 201

# Lấy danh sách giao dịch
@app.route('/transactions', methods=['GET'])
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.id, s.name as student_name, t.type, t.amount, t.description, t.transaction_date
        FROM transactions t
        JOIN students s ON t.student_id = s.id
        ORDER BY t.transaction_date DESC
    """)
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(transactions)

# Tổng thu, tổng chi
@app.route('/summary', methods=['GET'])
def get_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
    total_income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
    total_expense = cursor.fetchone()[0] or 0
    cursor.close()
    conn.close()
    return jsonify({'total_income': float(total_income), 'total_expense': float(total_expense)})

if __name__ == '__main__':
    app.run(debug=True)
