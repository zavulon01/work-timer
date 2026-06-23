import subprocess
import os
import sys

def send_notification(title: str, message: str):
    """Sends a native Windows Toast notification that is completely silent."""
    # Ensure text is properly escaped for PowerShell double quotes
    escaped_title = title.replace('"', '`"')
    escaped_message = message.replace('"', '`"')
    
    # PowerShell script using Windows Runtime ToastNotificationManager to display silent toast
    ps_script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    
    $textNodes = $template.GetElementsByTagName("text")
    $textNodes.Item(0).AppendChild($template.CreateTextNode("{escaped_title}")) | Out-Null
    $textNodes.Item(1).AppendChild($template.CreateTextNode("{escaped_message}")) | Out-Null
    
    $audio = $template.CreateElement("audio")
    $audio.SetAttribute("silent", "true")
    $template.SelectSingleNode("/toast").AppendChild($audio) | Out-Null
    
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows.SystemToast.Background").Show($toast)
    """
    
    try:
        # Hide the console window of the spawned powershell process
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # SW_HIDE
        
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW,
            capture_output=True,
            text=True,
            check=False
        )
    except Exception as e:
        # Simple print fallback if execution fails
        print(f"Failed to send native notification: {e}", file=sys.stderr)
        # Fallback to plyer if available
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name="Work Timer",
                timeout=5
            )
        except Exception:
            pass
