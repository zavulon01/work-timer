import customtkinter
import tkinter as tk
from src.config_manager import load_config, save_config
from src.notification_helper import send_notification
from src.strict_window import StrictBreakWindow

# Define Color Scheme
BG_COLOR = "#12131C"          # Very deep dark purple/grey
CARD_COLOR = "#1E2030"        # Card background
TEXT_MAIN = "#FFFFFF"         # Main white text
TEXT_MUTED = "#8F94A5"        # Muted gray text
COLOR_FOCUS = "#FF6B6B"       # Vibrant pastel coral red
COLOR_BREAK = "#2EC4B6"       # Refreshing teal green
COLOR_TRACK = "#2A2D44"       # Circular progress background track

import customtkinter
import tkinter as tk
from PIL import Image, ImageDraw
from src.config_manager import load_config, save_config
from src.notification_helper import send_notification
from src.strict_window import StrictBreakWindow

# Define Color Scheme
BG_COLOR = "#12131C"          # Very deep dark purple/grey
CARD_COLOR = "#1E2030"        # Card background
TEXT_MAIN = "#FFFFFF"         # Main white text
TEXT_MUTED = "#8F94A5"        # Muted gray text
COLOR_FOCUS = "#FF6B6B"       # Vibrant pastel coral red
COLOR_BREAK = "#2EC4B6"       # Refreshing teal green
COLOR_TRACK = "#2A2D44"       # Circular progress background track

class CircularProgress(customtkinter.CTkLabel):
    def __init__(self, parent, size=220, thickness=12, **kwargs):
        super().__init__(
            parent,
            text="",
            width=size,
            height=size,
            **kwargs
        )
        self.size = size
        self.thickness = thickness
        self.image = None
        
    def set_progress(self, ratio, color_hex):
        # Generate the circle image using Pillow with anti-aliasing (supersampling)
        img = self.generate_circle_image(ratio, color_hex)
        
        # Create CTkImage for high DPI support
        ctk_img = customtkinter.CTkImage(
            light_image=img,
            dark_image=img,
            size=(self.size, self.size)
        )
        self.configure(image=ctk_img)
        self.image = ctk_img  # Keep reference

    def generate_circle_image(self, ratio, color_hex) -> Image.Image:
        scale = 4  # Draw 4x larger for high-quality antialiasing
        img_size = self.size * scale
        thick = self.thickness * scale
        
        def hex_to_rgba(hex_str):
            hex_str = hex_str.lstrip('#')
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4)) + (255,)
            
        color = hex_to_rgba(color_hex)
        bg = hex_to_rgba(BG_COLOR)
        track = hex_to_rgba(COLOR_TRACK)
        
        img = Image.new("RGBA", (img_size, img_size), bg)
        draw = ImageDraw.Draw(img)
        
        # Bounding box
        pad = thick / 2
        bbox = [pad, pad, img_size - pad, img_size - pad]
        
        # Draw background track
        draw.ellipse(bbox, outline=track, width=thick)
        
        # Draw active progress arc (Pillow: start=-90 deg is top, goes clockwise)
        angle = ratio * 360
        if angle > 0:
            draw.arc(
                bbox,
                start=-90,
                end=-90 + angle,
                fill=color,
                width=thick
            )
            
        # Resize to target size using high-quality Lanczos resampling
        return img.resize((self.size, self.size), resample=Image.Resampling.LANCZOS)


class PomodoroApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = load_config()
        self.focus_duration = self.config["focus_duration_minutes"] * 60
        self.break_duration = self.config["break_duration_minutes"] * 60
        self.strict_break_enabled = self.config["strict_break_enabled"]
        
        # State variables
        self.current_mode = "focus"  # "focus" or "break"
        self.timer_state = "idle"    # "idle", "running", "paused"
        self.remaining_seconds = self.focus_duration
        self.is_hidden = False
        self.strict_window = None
        self.tick_job = None         # Holds the scheduled tk after job
        
        # Configure Main Window
        self.title("Work Timer")
        self.geometry("380x560")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)
        
        # System Tray support
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Create Layout
        self.setup_ui()
        self.update_timer_display()

    def setup_ui(self):
        # 1. Header / Mode Switcher Frame
        self.mode_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.mode_frame.pack(pady=(25, 10))
        
        self.btn_focus = customtkinter.CTkButton(
            self.mode_frame,
            text="Работа",
            width=110,
            height=32,
            corner_radius=20,
            fg_color=COLOR_FOCUS,
            hover_color="#E05B5B",
            font=("Outfit", 14, "bold"),
            command=lambda: self.switch_mode("focus")
        )
        self.btn_focus.pack(side="left", padx=5)
        
        self.btn_break = customtkinter.CTkButton(
            self.mode_frame,
            text="Перерыв",
            width=110,
            height=32,
            corner_radius=20,
            fg_color=CARD_COLOR,
            text_color=TEXT_MUTED,
            hover_color="#2A2D44",
            font=("Outfit", 14, "bold"),
            command=lambda: self.switch_mode("break")
        )
        self.btn_break.pack(side="left", padx=5)
        
        # 2. Main Timer Area
        self.timer_container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.timer_container.pack(pady=20)
        self.timer_container.grid_rowconfigure(0, weight=1)
        self.timer_container.grid_columnconfigure(0, weight=1)
        
        # Circular Progress ring as background layer in grid cell (0,0)
        self.progress_ring = CircularProgress(self.timer_container)
        self.progress_ring.grid(row=0, column=0, sticky="nsew")
        
        # Text overlay container in the same grid cell (0,0)
        self.text_overlay = customtkinter.CTkFrame(self.timer_container, fg_color="transparent")
        self.text_overlay.grid(row=0, column=0)
        
        self.timer_label = customtkinter.CTkLabel(
            self.text_overlay,
            text="25:00",
            font=("Outfit", 40, "bold"),
            text_color=TEXT_MAIN
        )
        self.timer_label.pack()
        
        self.sub_label = customtkinter.CTkLabel(
            self.text_overlay,
            text="FOCUS",
            font=("Outfit", 11, "bold"),
            text_color=TEXT_MUTED
        )
        self.sub_label.pack()

        # 3. Control Buttons
        self.control_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=10)
        
        self.btn_start = customtkinter.CTkButton(
            self.control_frame,
            text="Старт",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#3A3F58",
            hover_color="#4E5474",
            font=("Outfit", 14, "bold"),
            command=self.toggle_timer
        )
        self.btn_start.pack(side="left", padx=10)
        
        self.btn_reset = customtkinter.CTkButton(
            self.control_frame,
            text="Сброс",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="transparent",
            border_width=2,
            border_color="#3A3F58",
            hover_color="#1E2030",
            font=("Outfit", 14, "bold"),
            command=self.reset_timer
        )
        self.btn_reset.pack(side="left", padx=10)
        
        # Divider
        divider = customtkinter.CTkFrame(self, height=2, fg_color=CARD_COLOR)
        divider.pack(fill="x", padx=40, pady=15)
        
        # 4. Settings Panel
        self.settings_frame = customtkinter.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=12)
        self.settings_frame.pack(fill="x", padx=25, pady=(5, 20))
        
        # Focus Duration Row
        lbl_focus = customtkinter.CTkLabel(self.settings_frame, text="Время работы (мин):", font=("Outfit", 12), text_color=TEXT_MUTED)
        lbl_focus.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        self.entry_focus = customtkinter.CTkEntry(self.settings_frame, width=60, height=25, border_width=1, fg_color=BG_COLOR)
        self.entry_focus.insert(0, str(int(self.focus_duration / 60)))
        self.entry_focus.grid(row=0, column=1, padx=15, pady=8, sticky="e")
        
        # Break Duration Row
        lbl_break = customtkinter.CTkLabel(self.settings_frame, text="Время перерыва (мин):", font=("Outfit", 12), text_color=TEXT_MUTED)
        lbl_break.grid(row=1, column=0, padx=15, pady=8, sticky="w")
        
        self.entry_break = customtkinter.CTkEntry(self.settings_frame, width=60, height=25, border_width=1, fg_color=BG_COLOR)
        self.entry_break.insert(0, str(int(self.break_duration / 60)))
        self.entry_break.grid(row=1, column=1, padx=15, pady=8, sticky="e")
        
        # Strict Break Option Row
        lbl_strict = customtkinter.CTkLabel(self.settings_frame, text="Строгий перерыв:", font=("Outfit", 12), text_color=TEXT_MUTED)
        lbl_strict.grid(row=2, column=0, padx=15, pady=8, sticky="w")
        
        self.switch_strict = customtkinter.CTkSwitch(
            self.settings_frame,
            text="",
            progress_color=COLOR_BREAK,
            width=40
        )
        if self.strict_break_enabled:
            self.switch_strict.select()
        self.switch_strict.grid(row=2, column=1, padx=15, pady=8, sticky="e")
        
        # Save Button
        self.btn_save = customtkinter.CTkButton(
            self.settings_frame,
            text="Сохранить настройки",
            height=30,
            fg_color=CARD_COLOR,
            border_width=1,
            border_color="#3A3F58",
            hover_color="#2A2D44",
            font=("Outfit", 12, "bold"),
            command=self.save_settings
        )
        self.btn_save.grid(row=3, column=0, columnspan=2, padx=15, pady=(5, 12), sticky="ew")
        
        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_columnconfigure(1, weight=0)

    def update_timer_display(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        color = COLOR_FOCUS if self.current_mode == "focus" else COLOR_BREAK
        subtext = "FOCUS" if self.current_mode == "focus" else "BREAK"
        
        total_seconds = self.focus_duration if self.current_mode == "focus" else self.break_duration
        ratio = (total_seconds - self.remaining_seconds) / total_seconds if total_seconds > 0 else 0
        
        # Update progress and text labels
        self.progress_ring.set_progress(ratio, color)
        self.timer_label.configure(text=time_str)
        self.sub_label.configure(text=subtext, text_color=color)

    def switch_mode(self, target_mode):
        # Cancel any scheduled tick
        if self.tick_job is not None:
            self.after_cancel(self.tick_job)
            self.tick_job = None
            
        self.current_mode = target_mode
        if target_mode == "focus":
            self.btn_focus.configure(fg_color=COLOR_FOCUS, text_color=TEXT_MAIN)
            self.btn_break.configure(fg_color=CARD_COLOR, text_color=TEXT_MUTED)
            self.remaining_seconds = self.focus_duration
        else:
            self.btn_break.configure(fg_color=COLOR_BREAK, text_color=TEXT_MAIN)
            self.btn_focus.configure(fg_color=CARD_COLOR, text_color=TEXT_MUTED)
            self.remaining_seconds = self.break_duration
            
        self.timer_state = "idle"
        self.btn_start.configure(text="Старт", fg_color="#3A3F58", hover_color="#4E5474")
        self.update_timer_display()

    def toggle_timer(self):
        if self.timer_state == "running":
            self.pause_timer()
        else:
            self.start_timer()

    def start_timer(self):
        # Prevent spawning multiple tick loops
        if self.tick_job is not None:
            self.after_cancel(self.tick_job)
            self.tick_job = None
            
        self.timer_state = "running"
        self.btn_start.configure(text="Пауза", fg_color="#FF9F1C", hover_color="#E08A12")
        self.tick()

    def pause_timer(self):
        self.timer_state = "paused"
        self.btn_start.configure(text="Старт", fg_color="#3A3F58", hover_color="#4E5474")
        if self.tick_job is not None:
            self.after_cancel(self.tick_job)
            self.tick_job = None

    def reset_timer(self):
        self.timer_state = "idle"
        self.btn_start.configure(text="Старт", fg_color="#3A3F58", hover_color="#4E5474")
        if self.tick_job is not None:
            self.after_cancel(self.tick_job)
            self.tick_job = None
            
        self.remaining_seconds = self.focus_duration if self.current_mode == "focus" else self.break_duration
        self.update_timer_display()

    def tick(self):
        if self.timer_state != "running":
            return
        
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_timer_display()
            self.tick_job = self.after(1000, self.tick)
        else:
            self.handle_timer_completed()

    def handle_timer_completed(self):
        self.timer_state = "idle"
        self.btn_start.configure(text="Старт", fg_color="#3A3F58", hover_color="#4E5474")
        if self.tick_job is not None:
            self.after_cancel(self.tick_job)
            self.tick_job = None
            
        if self.current_mode == "focus":
            send_notification("Время отдохнуть!", "Рабочий интервал окончен. Пора сделать перерыв.")
            self.switch_mode("break")
            
            if self.strict_break_enabled:
                self.show_strict_break()
                
            if self.is_hidden and not self.strict_break_enabled:
                self.restore_window()
                
            self.start_timer()
        else:
            send_notification("Пора за работу!", "Перерыв завершен. Время сфокусироваться!")
            self.switch_mode("focus")
            if self.is_hidden:
                self.restore_window()

    def show_strict_break(self):
        if self.strict_window is not None:
            try:
                self.strict_window.destroy()
            except Exception:
                pass
        
        self.strict_window = StrictBreakWindow(self, lambda: self.remaining_seconds)

    def save_settings(self):
        try:
            focus_mins = int(self.entry_focus.get())
            break_mins = int(self.entry_break.get())
            
            if focus_mins <= 0 or break_mins <= 0:
                raise ValueError()
                
            self.focus_duration = focus_mins * 60
            self.break_duration = break_mins * 60
            self.strict_break_enabled = self.switch_strict.get()
            
            # Save configuration
            config_data = {
                "focus_duration_minutes": focus_mins,
                "break_duration_minutes": break_mins,
                "strict_break_enabled": self.strict_break_enabled
            }
            save_config(config_data)
            
            # Always reset the timer to apply duration settings immediately
            self.reset_timer()
            
            self.btn_save.configure(text="Сохранено!", fg_color="#2EC4B6")
            self.after(2000, lambda: self.btn_save.configure(text="Сохранить настройки", fg_color=CARD_COLOR))
        except ValueError:
            self.btn_save.configure(text="Ошибка (введите числа)!", fg_color="#FF6B6B")
            self.after(2000, lambda: self.btn_save.configure(text="Сохранить настройки", fg_color=CARD_COLOR))

    def minimize_to_tray(self):
        self.withdraw()
        self.is_hidden = True

    def restore_window(self):
        self.deiconify()
        self.focus_force()
        self.is_hidden = False
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
