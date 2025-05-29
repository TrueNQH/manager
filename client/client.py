import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
import io
import requests as reqs  # Để tránh trùng với requests của API
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

API_URL = 'http://127.0.0.1:5000'

class Sidebar(ttk.Frame):
    def __init__(self, parent, menu_items, on_select, on_logout=None):
        super().__init__(parent, width=200)
        self.pack_propagate(False)
        self.on_select = on_select
        self.on_logout = on_logout
        self.buttons = []
        for i, (name, key) in enumerate(menu_items):
            btn = ttk.Button(self, text=name, command=lambda k=key: self.on_select(k))
            btn.pack(fill='x', pady=2, padx=5)
            self.buttons.append(btn)
        if self.on_logout:
            ttk.Separator(self).pack(fill='x', pady=10)
            btn_logout = ttk.Button(self, text="Thoát", command=self.on_logout)
            btn_logout.pack(fill='x', pady=2, padx=5)

class StudentFrame(ttk.Frame):
    def __init__(self, parent, token, logout_callback):
        super().__init__(parent)
        self.token = token
        self.logout_callback = logout_callback
        self.sidebar = Sidebar(self,
                               [
                                   ('Thông tin cá nhân', 'profile'),
                                   ('Xem học phí', 'fee_status'),
                                   ('Đăng ký môn học', 'register_course'),
                                   
                               ],
                               self.change_view,
                               on_logout=self.logout_callback)
        self.sidebar.pack(side='left', fill='y')

        self.container = ttk.Frame(self)
        self.container.pack(side='left', fill='both', expand=True)

        self.frames = {}
        self.create_fee_status_frame()
        self.create_register_course_frame()
        self.create_profile_frame()

        self.change_view('fee_status')

    def create_fee_status_frame(self):
        frame = ttk.Frame(self.container)
        ttk.Label(frame, text="Thông tin học phí", font=('Arial', 16)).pack(pady=10)
        self.lbl_fee = ttk.Label(frame, text="Tổng học phí: ")
        self.lbl_fee.pack(pady=5)
        self.lbl_status = ttk.Label(frame, text="Trạng thái thanh toán: ")
        self.lbl_status.pack(pady=5)
        self.qr_label = ttk.Label(frame)
        self.qr_label.pack(pady=10)
        self.frames['fee_status'] = frame

        btn_refresh = ttk.Button(frame, text="Làm mới", command=self.load_fee_status)
        btn_refresh.pack(pady=5)
    


    def create_register_course_frame(self):
        frame = ttk.Frame(self.container)
        ttk.Label(frame, text="Đăng ký môn học", font=('Arial', 16)).pack(pady=10)

        ttk.Label(frame, text="Chọn môn học:").pack()

        self.course_cb = ttk.Combobox(frame, state='readonly')
        self.course_cb.pack()

        btn_load_courses = ttk.Button(frame, text="Tải danh sách môn học", command=self.load_courses)
        btn_load_courses.pack(pady=5)

        btn_register = ttk.Button(frame, text="Đăng ký", command=self.register_course)
        btn_register.pack(pady=5)

        self.lbl_register_msg = ttk.Label(frame, text="")
        self.lbl_register_msg.pack()

        # Hiển thị tổng học phí các môn đã đăng ký
        self.lbl_total_fee = ttk.Label(frame, text="Tổng học phí hiện tại: 0 VND")
        self.lbl_total_fee.pack(pady=10)

        self.frames['register_course'] = frame

    def create_profile_frame(self):
        frame = ttk.Frame(self.container)
        ttk.Label(frame, text="Thông tin cá nhân", font=('Arial', 16)).pack(pady=10)
        self.lbl_name = ttk.Label(frame, text="Tên: ")
        self.lbl_name.pack(pady=5)
        self.lbl_phone = ttk.Label(frame, text="Số điện thoại: ")
        self.lbl_phone.pack(pady=5)
        self.frames['profile'] = frame

    def load_courses(self):
        def format_fee(fee):
            try:
                # Loại bỏ khoảng trắng 2 đầu, chuyển sang float rồi format
                f = float(str(fee).strip())
                # Format với dấu phẩy nhóm hàng nghìn, giữ 0 chữ số thập phân
                return f"{f:,.0f}"
            except:
                return str(fee)
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.get(f"{API_URL}/courses", headers=headers)
            if res.status_code == 200:
                courses = res.json()
                self.courses = {f"{c['name']} - {format_fee(c['fee'])} VND": c['id'] for c in courses}



                self.course_cb['values'] = list(self.courses.keys())
                if courses:
                    self.course_cb.current(0)
            else:
                messagebox.showerror("Lỗi", "Không tải được danh sách môn học")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def register_course(self):
        course_text = self.course_cb.get()
        if not course_text:
            self.lbl_register_msg.config(text="Vui lòng chọn môn học", foreground='red')
            return
        course_id = self.courses.get(course_text)
        if not course_id:
            self.lbl_register_msg.config(text="Môn học không hợp lệ", foreground='red')
            return

        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.post(f"{API_URL}/student/register-course", json={'course_id': course_id}, headers=headers)
            if res.status_code == 200:
                self.lbl_register_msg.config(text="Đăng ký thành công", foreground='green')
                self.load_total_fee()  # Cập nhật tổng học phí
            else:
                self.lbl_register_msg.config(text=res.json().get('msg', 'Lỗi đăng ký'), foreground='red')
        except Exception as e:
            self.lbl_register_msg.config(text=str(e), foreground='red')

    def load_total_fee(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.get(f"{API_URL}/student/total-fee", headers=headers)
            if res.status_code == 200:
                total_fee = res.json().get('total_fee', 0)
                self.lbl_total_fee.config(text=f"Tổng học phí hiện tại: {total_fee:,.0f} VND")
            else:
                self.lbl_total_fee.config(text="Không tải được tổng học phí")
        except Exception as e:
            self.lbl_total_fee.config(text=f"Lỗi: {e}")

    def change_view(self, key):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[key].pack(fill='both', expand=True)
        if key == 'profile':
            self.load_profile()
        elif key == 'fee_status':
            self.load_fee_status()
        elif key == 'register_course':
            self.load_courses()
            self.load_total_fee()

    def load_fee_status(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.get(f"{API_URL}/student/payment-status", headers=headers)
            if res.status_code == 200:
                data = res.json()
                self.lbl_fee.config(text=f"Tổng học phí: {data['total_fee']:.2f} VND")
                status_text = "Chưa nộp học phí" if data['last_payment_status'] == 'pending' else "Đã nộp học phí"
                self.lbl_status.config(text=f"Trạng thái: {status_text}")
                amount = data.get('total_fee')
                code = data.get('payment_id')
                if amount and code:
                    qr_url = f"https://img.vietqr.io/image/OCB-0386306595-compact.png?amount={amount}&addInfo={code}"
                    # Tải QR code bằng thread
                    threading.Thread(target=self.load_qr_image, args=(qr_url,), daemon=True).start()
                else:
                    self.qr_label.configure(text="Không có thông tin QR", image='')
            else:
                messagebox.showerror("Lỗi", res.json().get('msg', 'Lỗi API'))
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def load_qr_image(self, qr_url):
        try:
            response = reqs.get(qr_url, timeout=5)
            if response.status_code == 200:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                img = ImageTk.PhotoImage(image)
                # Cập nhật giao diện phải dùng .after để đảm bảo thread-safe
                self.qr_label.after(0, self.update_qr_label, img)
            else:
                self.qr_label.after(0, self.qr_label.configure, {'text': "Không tải được mã QR", 'image': ''})
        except Exception as e:
            self.qr_label.after(0, self.qr_label.configure, {'text': f"Lỗi tải QR: {e}", 'image': ''})

    def update_qr_label(self, img):
        self.qr_label.configure(image=img, text='')
        self.qr_label.image = img  # giữ tham chiếu

    def load_profile(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.get(f"{API_URL}/student/profile", headers=headers)
            if res.status_code == 200:
                data = res.json()
                self.lbl_name.config(text=f"Tên: {data.get('name', '')}")
                self.lbl_phone.config(text=f"Số điện thoại: {data.get('phone', '')}")
            else:
                messagebox.showerror("Lỗi", res.json().get('msg', 'Lỗi API'))
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))


class ManagerFrame(ttk.Frame):
    def __init__(self, parent, token, logout_callback):
        super().__init__(parent)
        self.token = token
        self.logout_callback = logout_callback
        self.sidebar = Sidebar(self,
                               [('Danh sách học viên', 'students'),
                                ('Cập nhật trạng thái thanh toán', 'update_payment'),
                                ('Thống kê', 'stats')],
                               self.change_view,
                               on_logout=self.logout_callback)
        self.sidebar.pack(side='left', fill='y')
        self.container = ttk.Frame(self)
        self.container.pack(side='left', fill='both', expand=True)

        self.frames = {}
        self.create_students_frame()
        self.create_update_payment_frame()
        self.create_stats_frame()

        self.change_view('students')

    def create_students_frame(self):
        frame = ttk.Frame(self.container)
        ttk.Label(frame, text="Danh sách học viên", font=('Arial', 16)).pack(pady=10)

        cols = ('id', 'name', 'phone')
        self.tree = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=120)
        self.tree.pack(fill='both', expand=True)

        btn_refresh = ttk.Button(frame, text="Làm mới", command=self.load_students)
        btn_refresh.pack(pady=5)

        self.frames['students'] = frame
        self.load_students()

    def create_update_payment_frame(self):
        frame = ttk.Frame(self.container)
        ttk.Label(frame, text="Cập nhật trạng thái thanh toán", font=('Arial', 16)).pack(pady=10)

        frm = ttk.Frame(frame)
        frm.pack(pady=5)

        ttk.Label(frm, text="Payment ID:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_payment_id = ttk.Entry(frm)
        self.entry_payment_id.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frm, text="Trạng thái:").grid(row=1, column=0, padx=5, pady=5)
        self.status_cb = ttk.Combobox(frm, values=['pending', 'paid'], state='readonly')
        self.status_cb.grid(row=1, column=1, padx=5, pady=5)
        self.status_cb.current(0)

        btn_update = ttk.Button(frame, text="Cập nhật", command=self.update_payment_status)
        btn_update.pack(pady=5)

        self.lbl_update_msg = ttk.Label(frame, text="")
        self.lbl_update_msg.pack()

        self.frames['update_payment'] = frame

    def create_stats_frame(self):
        frame = ttk.Frame(self.container)
        ttk.Label(frame, text="Thống kê thanh toán", font=('Arial', 16)).pack(pady=10)
        self.stats_canvas = None
        btn_refresh = ttk.Button(frame, text="Làm mới", command=self.load_stats)
        btn_refresh.pack(pady=5)
        self.frames['stats'] = frame

    def change_view(self, key):
        for f in self.frames.values():
            f.pack_forget()
        self.frames[key].pack(fill='both', expand=True)

    def load_students(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.get(f"{API_URL}/manager/students", headers=headers)
            if res.status_code == 200:
                students = res.json()
                self.tree.delete(*self.tree.get_children())
                for s in students:
                    self.tree.insert('', 'end', values=(s['id'], s['name'], s['phone']))
            else:
                messagebox.showerror("Lỗi", res.json().get('msg', 'Lỗi API'))
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def update_payment_status(self):
        payment_id = self.entry_payment_id.get()
        status = self.status_cb.get()
        if not payment_id:
            self.lbl_update_msg.config(text="Vui lòng nhập Payment ID", foreground='red')
            return

        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.post(
                f"{API_URL}/manager/update-payment-status",
                json={'payment_id': int(payment_id), 'status': status},
                headers=headers
            )
            if res.status_code == 200:
                self.lbl_update_msg.config(text="Cập nhật thành công", foreground='green')
            else:
                # Hiển thị thông báo lỗi trả về từ API
                try:
                    msg = res.json().get('msg', 'Lỗi cập nhật')
                except Exception:
                    msg = 'Lỗi cập nhật'
                self.lbl_update_msg.config(text=msg, foreground='red')
        except Exception as e:
            self.lbl_update_msg.config(text=str(e), foreground='red')

    def load_stats(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            res = requests.get(f"{API_URL}/manager/payment-stats", headers=headers)
            if res.status_code == 200:
                stats = res.json()
                labels = [s['status'] for s in stats]
                sizes = [s['count'] for s in stats]
                fig, ax = plt.subplots(figsize=(4, 4))
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                if self.stats_canvas:
                    self.stats_canvas.get_tk_widget().destroy()
                self.stats_canvas = FigureCanvasTkAgg(fig, master=self.frames['stats'])
                self.stats_canvas.draw()
                self.stats_canvas.get_tk_widget().pack()
            else:
                messagebox.showerror("Lỗi", res.json().get('msg', 'Lỗi API'))
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quản lý Thu Chi Học Phí")
        self.geometry("700x500")

        self.token = None
        self.role = None
        self.student_frame = None
        self.manager_frame = None
        self.login_frame = ttk.Frame(self)
        self.login_frame.pack(fill='both', expand=True)

        self.create_login_ui()
    def logout(self):
        # Xoá token, role
        self.token = None
        self.role = None
        
        # Ẩn frame role hiện tại nếu có
        if self.student_frame:
            self.student_frame.destroy()
            self.student_frame = None
        if self.manager_frame:
            self.manager_frame.destroy()
            self.manager_frame = None

        # Hiện lại màn hình đăng nhập
        self.login_frame.pack(fill='both', expand=True)
    def create_login_ui(self):
        for w in self.login_frame.winfo_children():
            w.destroy()

        ttk.Label(self.login_frame, text="Tên đăng nhập:").pack(pady=5)
        self.entry_username = ttk.Entry(self.login_frame)
        self.entry_username.pack(pady=5)

        ttk.Label(self.login_frame, text="Mật khẩu:").pack(pady=5)
        self.entry_password = ttk.Entry(self.login_frame, show='*')
        self.entry_password.pack(pady=5)

        btn_login = ttk.Button(self.login_frame, text="Đăng nhập", command=self.login)
        btn_login.pack(pady=20)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        if not username or not password:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu")
            return

        try:
            res = requests.post(f"{API_URL}/login", json={'username': username, 'password': password})
            if res.status_code == 200:
                data = res.json()
                self.token = data['access_token']
                self.role = data['role']
                self.login_frame.pack_forget()
                if self.role == 'student':
                    self.student_frame = StudentFrame(self, self.token, logout_callback=self.logout)
                    self.student_frame.pack(fill='both', expand=True)
                elif self.role == 'manager':
                    self.manager_frame = ManagerFrame(self, self.token, logout_callback=self.logout)
                    self.manager_frame.pack(fill='both', expand=True)
            else:
                messagebox.showerror("Lỗi đăng nhập", res.json().get('msg', 'Lỗi không xác định'))
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", str(e))


if __name__ == '__main__':
    app = App()
    app.mainloop()
