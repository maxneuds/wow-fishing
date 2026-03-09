import win32gui
import win32con
import win32process
import win32api

def find_and_activate_wow_window():
    """
    Find the World of Warcraft window and bring it to the foreground.
    Returns True if successful, False otherwise.
    """
    # Find the window by title (case-sensitive)
    hwnd = win32gui.FindWindow(None, "World of Warcraft")

    if hwnd == 0:
        print("World of Warcraft window not found.")
        return False

    return force_activate_window(hwnd)

def force_activate_window(hwnd):
    """
    Forcefully activate a window by attaching to its thread.
    This works around Windows' security restrictions on SetForegroundWindow.
    """
    try:
        # Get the thread ID of the target window
        _, target_thread_id = win32process.GetWindowThreadProcessId(hwnd)

        # Get the current thread ID
        current_thread_id = win32api.GetCurrentThreadId()

        # Attach the current thread to the target window's thread
        win32process.AttachThreadInput(current_thread_id, target_thread_id, True)

        # Restore the window if it's minimized
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # Bring to foreground
        win32gui.SetForegroundWindow(hwnd)

        # Detach the threads
        win32process.AttachThreadInput(current_thread_id, target_thread_id, False)

        return True
    except Exception as e:
        print(f"Failed to activate window: {e}")
        return False
    """
    Find a window by partial title match.
    Useful if the full title varies (e.g., with realm names).
    """
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if partial_title.lower() in title.lower():
                windows.append((hwnd, title))
        return True

    windows = []
    win32gui.EnumWindows(callback, windows)

    return windows

def activate_wow_window():
    """
    More robust version that searches for WoW windows with partial title match.
    """
    wow_windows = find_window_by_partial_title("World of Warcraft")

    if not wow_windows:
        print("No World of Warcraft windows found.")
        return False

    # Use the first matching window
    hwnd, title = wow_windows[0]
    print(f"Activating window: {title}")

    # Try the robust activation method
    return force_activate_window(hwnd)

if __name__ == "__main__":
    activate_wow_window()
