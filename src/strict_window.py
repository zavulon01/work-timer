import customtkinter

class StrictBreakWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, get_remaining_seconds_fn):
        super().__init__(parent)
        self.get_remaining_seconds = get_remaining_seconds_fn
        
        # Windows attributes
        self.title("Strict Break")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.94)  # Semi-transparent glassmorphism look
        self.configure(fg_color="#0a0b10")  # Custom deep space dark background
        
        # Intercept and disable standard Alt+F4 or manual close attempts
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Prevent clicks outside and maintain absolute focus
        self.lift()
        self.focus_force()
        self.grab_set()
        
        # Bind keyboard shortcuts to prevent bypassing
        self.bind("<Escape>", lambda e: None)
        
        # Center layout container
        self.container = customtkinter.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True)
        
        # Design Elements
        self.icon_label = customtkinter.CTkLabel(
            self.container,
            text="⏳",
            font=("Outfit", 72)
        )
        self.icon_label.pack(pady=10)
        
        self.header_label = customtkinter.CTkLabel(
            self.container,
            text="STRICT BREAK ACTIVE",
            font=("Outfit", 32, "bold"),
            text_color="#FF6B6B"  # Vibrant pastel red/coral
        )
        self.header_label.pack(pady=10)
        
        self.tip_label = customtkinter.CTkLabel(
            self.container,
            text="Stand up, stretch, hydrate, and look away from the screen.",
            font=("Outfit", 18),
            text_color="#8F94A5"
        )
        self.tip_label.pack(pady=5)
        
        self.timer_label = customtkinter.CTkLabel(
            self.container,
            text="00:00",
            font=("Outfit", 96, "bold"),
            text_color="#FFFFFF"
        )
        self.timer_label.pack(pady=30)
        
        # Run local loop to keep window in focus and update time
        self.update_window()

    def update_window(self):
        try:
            # Check remaining seconds from callback
            seconds_left = self.get_remaining_seconds()
            
            if seconds_left <= 0:
                self.grab_release()
                self.destroy()
                return
            
            minutes = seconds_left // 60
            seconds = seconds_left % 60
            self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
            
            # Constantly push window to top and maintain focus
            self.attributes("-topmost", True)
            self.focus_force()
            
            # Schedule next update
            self.after(500, self.update_window)
        except Exception:
            # Safe exit in case of exception to avoid locking the screen permanently
            self.grab_release()
            self.destroy()
