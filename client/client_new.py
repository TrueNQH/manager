import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
import io
import requests as reqs
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

API_URL = 'http://127.0.0.1:5000'

class LoginFrame(tk.Frame):
    def __init__(self, parent, on_login):
        super().__init__(parent, bg='white')
        self.on_login = on_login
        self.create_widgets()

    def create_widgets(self):
        # Main container
        container = tk.Frame(self, bg='white', padx=40, pady=40)
        container.pack(expand=True)

        # Title
        title = tk.Label(container,
                        text="ĐĂNG NHẬP HỆ THỐNG",
                        font=('Arial', 24, 'bold'),
                        fg='#2c3e50',
                        bg='white')
        title.pack(pady=(0, 20))

        # Username
        username_label = tk.Label(container,
                                text="Tên đăng nhập:",
                                font=('Arial', 10, 'bold'),
                                fg='#2c3e50',
                                bg='white')
        username_label.pack(anchor='w', pady=(0, 5))

        self.username_entry = tk.Entry(container,
                                     font=('Arial', 11),
                                     width=30,
                                     relief='solid',
                                     bd=1)
        self.username_entry.pack(fill='x', pady=(0, 15))

        # Password
        password_label = tk.Label(container,
                                text="Mật khẩu:",
                                font=('Arial', 10, 'bold'),
                                fg='#2c3e50',
                                bg='white')
        password_label.pack(anchor='w', pady=(0, 5))

        self.password_entry = tk.Entry(container,
                                     font=('Arial', 11),
                                     show='•',
                                     width=30,
                                     relief='solid',
                                     bd=1)
        self.password_entry.pack(fill='x', pady=(0, 20))

        # Login button
        self.login_button = tk.Button(container,
                                    text="ĐĂNG NHẬP",
                                    font=('Arial', 12, 'bold'),
                                    bg='#3498db',
                                    fg='white',
                                    relief='flat',
                                    padx=20,
                                    pady=10,
                                    cursor='hand2',
                                    command=self.login)
        self.login_button.pack(fill='x', pady=(10, 0))

        # Add hover effect
        self.login_button.bind("<Enter>", self.on_enter)
        self.login_button.bind("<Leave>", self.on_leave)

        # Add Enter key bindings
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.login())

        # Focus username field
        self.username_entry.focus()

    def on_enter(self, e):
        self.login_button['bg'] = '#2980b9'

    def on_leave(self, e):
        self.login_button['bg'] = '#3498db'

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.on_login(username, password)

# Copy the rest of your existing classes (Sidebar, StudentFrame, ManagerFrame) here
# ... (copy all the other classes from your original file)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quản lý Thu Chi Học Phí")
        self.geometry("700x500")

        self.token = None
        self.role = None
        self.student_frame = None
        self.manager_frame = None
        
        # Create login frame
        self.login_frame = LoginFrame(self, self.handle_login)
        self.login_frame.pack(fill='both', expand=True)

    def handle_login(self, username, password):
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
        self.login_frame = LoginFrame(self, self.handle_login)
        self.login_frame.pack(fill='both', expand=True)

if __name__ == '__main__':
    app = App()
    app.mainloop() 