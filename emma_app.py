import tkinter as tk
from gui.main_window import EmmaWindow
from core.config import ensure_config

if __name__ == "__main__":
    ensure_config()
        root = tk.Tk()
            app = EmmaWindow(root)
                root.mainloop()