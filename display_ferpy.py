import tkinter as tk
import threading
import time
import math

class FerpyDisplay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.title('Ferpy Loading Display')
        self.state = 'boot'  # 'boot', 'loading', 'line', 'stationary'
        self.text_var = tk.StringVar()
        self.text_var.set('Starting...')
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        self.angle = 0
        self.running = True
        self._lock = threading.Lock()
        self._boot_sequence_done = False
        self.root.after(100, self._draw)
        self.root.after(100, self._boot_sequence)

    def _boot_sequence(self):
        # Show boot messages in sequence
        def set_text(msg):
            self.text_var.set(msg)
            self._draw()
        set_text('Starting...')
        self.root.update()
        self.root.after(1000, lambda: set_text('Loading files...'))
        self.root.after(2000, lambda: set_text('Setting program...'))
        def finish():
            self._boot_sequence_done = True
            self.set_state('loading')
        self.root.after(3000, finish)

    def set_state(self, state):
        with self._lock:
            self.state = state
        self._draw()

    def _draw(self):
        self.canvas.delete('all')
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        cx, cy = w // 2, h // 2
        r = min(w, h) // 8
        # Draw text if in boot sequence
        if not self._boot_sequence_done:
            self.canvas.create_text(cx, cy, text=self.text_var.get(), fill='white', font=('Arial', 48, 'bold'))
        else:
            # Draw loading animation or state
            if self.state == 'loading':
                # Spinning circle
                start = self.angle % 360
                extent = 270
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline='#00ffcc', width=16)
                self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=start, extent=extent, style=tk.ARC, outline='#00ffcc', width=24)
                self.angle = (self.angle + 6) % 360
            elif self.state == 'line':
                # Straight line (horizontal)
                self.canvas.create_line(cx - r, cy, cx + r, cy, fill='#00ffcc', width=24, capstyle=tk.ROUND)
            elif self.state == 'stationary':
                # Stationary circle
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline='#00ffcc', width=24)
        if self.running:
            self.root.after(33, self._draw)  # ~30 FPS

    def run(self):
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.root.destroy()

# Singleton instance and thread
_display_instance = None
_display_thread = None

def start_display():
    global _display_instance, _display_thread
    if _display_instance is not None:
        return
    def run():
        global _display_instance
        _display_instance = FerpyDisplay()
        _display_instance.run()
    _display_thread = threading.Thread(target=run, daemon=True)
    _display_thread.start()
    # Wait a bit for the window to appear
    time.sleep(0.2)

def set_display_state(state):
    if _display_instance:
        _display_instance.set_state(state)

def stop_display():
    if _display_instance:
        _display_instance.stop()