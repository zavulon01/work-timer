import sys
import os
import tkinter as tk
from PIL import Image, ImageDraw

from src.ui_app import PomodoroApp
from src.tray_icon import setup_tray_icon

def generate_default_icon() -> Image.Image:
    """Generates a beautiful modern tomato icon dynamically using Pillow."""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Red tomato round body
    draw.ellipse((8, 14, 56, 58), fill=(255, 107, 107), outline=(230, 80, 80), width=2)
    # Green stem/leaves
    draw.polygon([(32, 4), (25, 16), (39, 16)], fill=(46, 196, 182))
    draw.rectangle((30, 10, 34, 16), fill=(46, 196, 182))
    
    return image

def main():
    # Instantiate the main CTk application
    app = PomodoroApp()
    
    # Generate and save the icon image for tray and PyInstaller resource bundling
    icon_img = generate_default_icon()
    icon_path = os.path.abspath("icon.png")
    if not os.path.exists(icon_path):
        icon_img.save(icon_path)
    
    # Use the generated icon for the CTk app window title bar icon
    try:
        app.iconphoto(False, tk.PhotoImage(file=icon_path))
    except Exception:
        # Fallback if tk photo image fails
        pass

    # Thread-safe callbacks scheduled to run on the Tkinter main thread
    def on_show():
        app.after(0, app.restore_window)
        
    def on_toggle_pause():
        app.after(0, app.toggle_timer)
        
    def on_exit():
        app.after(0, shutdown)

    # Initialize pystray tray icon
    tray = setup_tray_icon(on_show, on_toggle_pause, on_exit, icon_img)
    
    def shutdown():
        # Stop pystray icon thread
        tray.stop()
        # Destroy CTk app window and exit
        app.destroy()
        sys.exit(0)

    # Handle OS close event via tray exit if needed
    # We override standard window close to minimize to tray instead
    
    # Start pystray event loop in a background thread
    tray.run_detached()
    
    # Run the Tkinter mainloop on the main thread (blocking)
    app.mainloop()

if __name__ == "__main__":
    main()
