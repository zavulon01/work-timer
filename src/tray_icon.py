import pystray
from PIL import Image

def setup_tray_icon(show_callback, toggle_pause_callback, exit_callback, icon_image) -> pystray.Icon:
    """Sets up and returns a pystray Icon instance.
    
    Parameters:
    - show_callback: Function to run to show/restore the window.
    - toggle_pause_callback: Function to run to toggle pause status.
    - exit_callback: Function to terminate the application.
    - icon_image: PIL Image used as the tray icon.
    """
    
    # Define system tray context menu items
    menu = pystray.Menu(
        pystray.MenuItem("Открыть таймер", lambda icon, item: show_callback(), default=True),
        pystray.MenuItem("Старт / Пауза", lambda icon, item: toggle_pause_callback()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Выход", lambda icon, item: exit_callback())
    )
    
    icon = pystray.Icon(
        "work_timer",
        icon_image,
        title="Work Timer (Помодоро)",
        menu=menu
    )
    
    return icon
