import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import sys
import os

class MiniMacroUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MiniMacro - Two-Pass Macroprocessor")
        self.geometry("900x700")

        # Dark theme settings
        self.bg_color = "#121212"
        self.fg_color = "#E0E0E0"
        self.btn_bg = "#333333"
        self.btn_fg = "#FFFFFF"
        self.btn_active = "#555555"
        self.text_bg = "#1E1E1E"

        self.configure(bg=self.bg_color)

        self.selected_file = None

        self.create_widgets()

    def create_widgets(self):
        # Top Frame for controls
        top_frame = tk.Frame(self, bg=self.bg_color, pady=15)
        top_frame.pack(fill=tk.X)

        # Title Label
        title_label = tk.Label(top_frame, text="MiniMacro Processor", font=("Helvetica", 18, "bold"), bg=self.bg_color, fg=self.fg_color)
        title_label.pack(pady=(0, 10))

        # Buttons Frame
        btn_frame = tk.Frame(top_frame, bg=self.bg_color)
        btn_frame.pack()

        # Select File Button
        self.select_btn = tk.Button(btn_frame, text="Select Input File", font=("Helvetica", 12),
                                    bg=self.btn_bg, fg=self.btn_fg, activebackground=self.btn_active,
                                    activeforeground=self.btn_fg, relief=tk.FLAT, padx=10, pady=5,
                                    command=self.select_file)
        self.select_btn.pack(side=tk.LEFT, padx=10)

        # Run Button
        self.run_btn = tk.Button(btn_frame, text="Run Macroprocessor", font=("Helvetica", 12),
                                 bg=self.btn_bg, fg=self.btn_fg, activebackground=self.btn_active,
                                 activeforeground=self.btn_fg, relief=tk.FLAT, padx=10, pady=5,
                                 command=self.run_processor)
        self.run_btn.pack(side=tk.LEFT, padx=10)

        # Selected File Label
        self.file_label = tk.Label(top_frame, text="No file selected", font=("Helvetica", 10), bg=self.bg_color, fg="#AAAAAA")
        self.file_label.pack(pady=(10, 0))

        # Output Text Area
        text_frame = tk.Frame(self, bg=self.bg_color, padx=20, pady=10)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(text_frame, bg=self.text_bg, fg=self.fg_color, font=("Consolas", 11),
                                   wrap=tk.WORD, yscrollcommand=scrollbar.set, relief=tk.FLAT, padx=10, pady=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output_text.yview)

        # Set text as read-only initially
        self.output_text.config(state=tk.DISABLED)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Input Program",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Selected: {os.path.basename(file_path)}", fg="#4CAF50")

            # Clear output text
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"File selected: {file_path}\nReady to run.\n")
            self.output_text.config(state=tk.DISABLED)

    def run_processor(self):
        if not self.selected_file:
            messagebox.showwarning("No File", "Please select an input file first.")
            return

        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Running main.py with {os.path.basename(self.selected_file)}...\n")
        self.output_text.insert(tk.END, "-" * 60 + "\n")
        self.output_text.update()

        try:
            # Run the main.py script
            process = subprocess.run(
                [sys.executable, "main.py", self.selected_file],
                capture_output=True,
                text=True,
                check=False
            )

            # Display stdout
            if process.stdout:
                self.output_text.insert(tk.END, process.stdout)

            # Display stderr if there were errors
            if process.stderr:
                self.output_text.insert(tk.END, "\n[ERRORS]\n" + process.stderr)

            if process.returncode != 0:
                self.output_text.insert(tk.END, f"\nProcess exited with code {process.returncode}\n")

        except Exception as e:
            self.output_text.insert(tk.END, f"\nFailed to execute processor: {str(e)}\n")

        finally:
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = MiniMacroUI()
    app.mainloop()
