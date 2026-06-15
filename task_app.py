import customtkinter as ctk
import json
import os
import threading
import time
from datetime import datetime
import pystray
from PIL import Image, ImageDraw
from plyer import notification
from tkinter import messagebox

DATA_FILE = "tasks.json"

class TaskTracker:
    def __init__(self, data_file):
        self.data_file = data_file
        self.tasks = self.load_tasks()
        self.running = True
        self.lock = threading.Lock()
        
    def load_tasks(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_tasks(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def add_task(self, name, date_str, time_str, progress, reporter):
        task = {
            "id": int(time.time() * 1000),
            "name": name,
            "date": date_str,
            "time": time_str,
            "progress": progress,
            "reporter": reporter,
            "status": "pending",
            "notified_2h": False,
            "notified_1h": False
        }
        with self.lock:
            self.tasks.append(task)
            self.save_tasks()
        return task

    def update_task_progress(self, task_id, progress):
        with self.lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    task["progress"] = progress
                    if progress >= 100:
                        task["status"] = "completed"
                        task["progress"] = 100
                    break
            self.save_tasks()

    def mark_completed(self, task_id):
        with self.lock:
            for task in self.tasks:
                if task["id"] == task_id:
                    task["status"] = "completed"
                    task["progress"] = 100
                    break
            self.save_tasks()

    def check_deadlines(self):
        """Luồng chạy ngầm kiểm tra deadline mà không block giao diện"""
        while self.running:
            now = datetime.now()
            changed = False
            
            with self.lock:
                for task in self.tasks:
                    if task.get("status") == "completed":
                        continue
                        
                    try:
                        deadline_str = f"{task['date']} {task['time']}"
                        deadline = datetime.strptime(deadline_str, "%d/%m/%Y %H:%M")
                    except ValueError:
                        continue 
                        
                    time_diff = deadline - now
                    total_seconds = time_diff.total_seconds()
                    
                    # Mốc 1: Sắp đến hạn ( <= 2 giờ và > 1 giờ )
                    if 3600 < total_seconds <= 7200 and not task.get("notified_2h"):
                        self.show_notification(
                            "Sắp đến hạn",
                            f"Sắp đến hạn: {task['name']} - Còn 2 giờ nữa"
                        )
                        task["notified_2h"] = True
                        changed = True
                    # Mốc 2: Gấp ( <= 1 giờ )
                    elif 0 < total_seconds <= 3600 and not task.get("notified_1h"):
                        self.show_notification(
                            "Gấp",
                            f"Gấp: {task['name']} - Do {task['reporter']} phụ trách chỉ còn 1 giờ để hoàn thành!"
                        )
                        task["notified_1h"] = True
                        changed = True
                
                if changed:
                    self.save_tasks()
                    
            # Check mỗi 60s (ngủ từng giây để thoát thread nhanh khi tắt app)
            for _ in range(60):
                if not self.running:
                    break
                time.sleep(1)

    def show_notification(self, title, message):
        """Hiển thị popup notification"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="TaskApp",
                timeout=10
            )
        except Exception as e:
            print(f"Notification error: {e}")

    def stop(self):
        self.running = False


class TaskApp(ctk.CTk):
    def __init__(self, tracker):
        super().__init__()
        
        self.tracker = tracker
        self.tray_icon = None
        
        # Cấu hình cửa sổ chính
        self.title("Quản lý Công việc & Nhắc nhở")
        self.geometry("800x600")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Bắt sự kiện tắt cửa sổ -> thu xuống system tray
        self.protocol('WM_DELETE_WINDOW', self.hide_window)
        
        self.setup_ui()
        self.refresh_task_list()
        
        # Khởi chạy luồng kiểm tra deadline
        self.check_thread = threading.Thread(target=self.tracker.check_deadlines, daemon=True)
        self.check_thread.start()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- Form nhập liệu ---
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.entry_name = ctk.CTkEntry(input_frame, placeholder_text="Tên công việc")
        self.entry_name.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.entry_date = ctk.CTkEntry(input_frame, placeholder_text="Ngày (DD/MM/YYYY)")
        self.entry_date.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.entry_time = ctk.CTkEntry(input_frame, placeholder_text="Giờ (HH:MM)")
        self.entry_time.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.entry_progress = ctk.CTkEntry(input_frame, placeholder_text="Tiến độ (%)")
        self.entry_progress.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.entry_reporter = ctk.CTkEntry(input_frame, placeholder_text="Người báo cáo")
        self.entry_reporter.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        btn_add = ctk.CTkButton(input_frame, text="Thêm/Lưu công việc", command=self.add_task)
        btn_add.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        # --- Danh sách hiển thị ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Danh sách công việc chưa hoàn thành")
        self.scroll_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
    def add_task(self):
        name = self.entry_name.get().strip()
        date_str = self.entry_date.get().strip()
        time_str = self.entry_time.get().strip()
        progress_str = self.entry_progress.get().strip()
        reporter = self.entry_reporter.get().strip()
        
        if not name or not date_str or not time_str or not reporter:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return
            
        # Kiểm tra try-except theo đúng format ngày giờ
        try:
            datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
        except ValueError:
            messagebox.showerror("Lỗi", "Sai định dạng ngày hoặc giờ!\nNgày: DD/MM/YYYY\nGiờ: HH:MM")
            return
            
        try:
            progress = int(progress_str) if progress_str else 0
            if not (0 <= progress <= 100):
                raise ValueError
        except ValueError:
            messagebox.showerror("Lỗi", "Tiến độ phải là số từ 0 - 100!")
            return
            
        self.tracker.add_task(name, date_str, time_str, progress, reporter)
        
        # Clear form
        self.entry_name.delete(0, 'end')
        self.entry_date.delete(0, 'end')
        self.entry_time.delete(0, 'end')
        self.entry_progress.delete(0, 'end')
        self.entry_reporter.delete(0, 'end')
        
        self.refresh_task_list()
        
    def refresh_task_list(self):
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        with self.tracker.lock:
            tasks = [t for t in self.tracker.tasks if t.get("status") != "completed"]
            
        for task in tasks:
            frame = ctk.CTkFrame(self.scroll_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            info = f"📌 {task['name']} | 🕒 {task['date']} {task['time']} | 👤 {task['reporter']} | 📊 {task['progress']}%"
            lbl = ctk.CTkLabel(frame, text=info, anchor="w", font=("Arial", 13))
            lbl.pack(side="left", padx=10, pady=5, fill="x", expand=True)
            
            btn_update = ctk.CTkButton(frame, text="Cập nhật tiến độ", width=120,
                                       command=lambda t=task: self.prompt_update_progress(t["id"]))
            btn_update.pack(side="left", padx=5, pady=5)
            
            btn_complete = ctk.CTkButton(frame, text="Hoàn thành", width=100, fg_color="#27ae60", hover_color="#2ecc71",
                                         command=lambda t=task: self.mark_completed(t["id"]))
            btn_complete.pack(side="left", padx=5, pady=5)
            
    def prompt_update_progress(self, task_id):
        dialog = ctk.CTkInputDialog(text="Nhập tiến độ mới (0-100):", title="Cập nhật tiến độ")
        result = dialog.get_input()
        if result is not None:
            try:
                prog = int(result)
                if 0 <= prog <= 100:
                    self.tracker.update_task_progress(task_id, prog)
                    self.refresh_task_list()
                else:
                    messagebox.showerror("Lỗi", "Tiến độ phải từ 0 đến 100")
            except ValueError:
                messagebox.showerror("Lỗi", "Tiến độ không hợp lệ")

    def mark_completed(self, task_id):
        self.tracker.mark_completed(task_id)
        self.refresh_task_list()

    def hide_window(self):
        """Thu nhỏ xuống System Tray thay vì tắt hẳn"""
        self.withdraw()
        image = self.create_image()
        menu = pystray.Menu(
            pystray.MenuItem('Mở lên', self.show_window),
            pystray.MenuItem('Thoát hoàn toàn', self.quit_window)
        )
        self.tray_icon = pystray.Icon("TaskApp", image, "Quản lý công việc", menu)
        
        # Chạy tray trong luồng riêng để không block mainloop của tkinter
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        
    def show_window(self, icon, item):
        """Mở lại cửa sổ từ Tray"""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.after(0, self.deiconify)
        
    def quit_window(self, icon, item):
        """Thoát hoàn toàn ứng dụng"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.tracker.stop()
        self.after(0, self.destroy)
        # Bắt buộc thoát chương trình vì có daemon thread và pystray icon
        os._exit(0)
        
    def create_image(self):
        """Tạo icon cho System Tray"""
        width = 64
        height = 64
        color1 = '#2c3e50'
        color2 = '#ecf0f1'
        
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        # Vẽ một biểu tượng checkmark đơn giản
        dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
        dc.rectangle((0, height // 2, width // 2, height), fill=color2)
        return image

if __name__ == "__main__":
    tracker = TaskTracker(DATA_FILE)
    app = TaskApp(tracker)
    app.mainloop()
