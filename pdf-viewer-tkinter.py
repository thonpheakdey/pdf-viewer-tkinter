import fitz
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import io


class PDFViewer:

    def __init__(self, root):

        self.root = root
        self.root.title("PDF Viewer")
        self.root.geometry("1000x750")
        self.root.configure(bg="#1e1e1e")

        self.current_doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.current_image = None

        self.invert_colors = False
        self.fullscreen = False  # NEW: track fullscreen state

        self.setup_ui()


    def setup_ui(self):

        toolbar = tk.Frame(self.root, bg="#2b2b2b")
        toolbar.pack(fill=tk.X)

        tk.Button(toolbar, text="Open PDF", command=self.open_pdf,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10, pady=10)

        self.prev_btn = tk.Button(toolbar, text="◀", command=self.prev_page, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.page_label = tk.Label(toolbar, text="Page 0/0", bg="#2b2b2b", fg="white")
        self.page_label.pack(side=tk.LEFT, padx=10)

        self.next_btn = tk.Button(toolbar, text="▶", command=self.next_page, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(toolbar, text="Zoom +", command=self.zoom_in).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Zoom -", command=self.zoom_out).pack(side=tk.LEFT, padx=5)

        tk.Button(toolbar, text="Reset", command=self.reset_zoom).pack(side=tk.LEFT, padx=5)

        # Invert colors button
        self.invert_btn = tk.Button(toolbar, text="Invert Colors", command=self.toggle_invert,
                                    bg="#444", fg="white")
        self.invert_btn.pack(side=tk.LEFT, padx=15)

        # NEW FULLSCREEN BUTTON
        self.fullscreen_btn = tk.Button(toolbar, text="⛶ Fullscreen", command=self.toggle_fullscreen,
                                        bg="#555", fg="white")
        self.fullscreen_btn.pack(side=tk.LEFT, padx=5)

        viewer_frame = tk.Frame(self.root, bg="#1e1e1e")
        viewer_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(viewer_frame, bg="#1e1e1e")

        vbar = tk.Scrollbar(viewer_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        hbar = tk.Scrollbar(viewer_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")

        viewer_frame.grid_rowconfigure(0, weight=1)
        viewer_frame.grid_columnconfigure(0, weight=1)

        self.image_id = None

        self.canvas.bind("<MouseWheel>", self.mouse_wheel)

        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))

        self.root.bind("<Left>", lambda e: self.prev_page())
        self.root.bind("<Right>", lambda e: self.next_page())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())  # NEW: F11 key for fullscreen
        self.root.bind("<Escape>", lambda e: self.exit_fullscreen())  # NEW: Escape to exit fullscreen


    def open_pdf(self):

        file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])

        if not file:
            return

        self.current_doc = fitz.open(file)
        self.total_pages = len(self.current_doc)
        self.current_page = 0
        self.zoom_level = 1

        self.update_buttons()
        self.display_page()


    def display_page(self):

        if not self.current_doc:
            return

        page = self.current_doc[self.current_page]

        matrix = fitz.Matrix(self.zoom_level, self.zoom_level)

        pix = page.get_pixmap(matrix=matrix)

        img_data = pix.tobytes("png")

        image = Image.open(io.BytesIO(img_data))

        # APPLY COLOR INVERSION
        if self.invert_colors:
            image = ImageOps.invert(image.convert("RGB"))

        self.current_image = ImageTk.PhotoImage(image)

        if self.image_id:
            self.canvas.delete(self.image_id)

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        img_w = self.current_image.width()
        img_h = self.current_image.height()

        x = max(canvas_w / 2, img_w / 2)
        y = max(canvas_h / 2, img_h / 2)

        self.image_id = self.canvas.create_image(x, y, image=self.current_image, anchor="center")

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.page_label.config(text=f"Page {self.current_page+1}/{self.total_pages}")


    def toggle_invert(self):

        self.invert_colors = not self.invert_colors

        if self.invert_colors:
            self.invert_btn.config(bg="#2196F3", text="Invert ON")
        else:
            self.invert_btn.config(bg="#444", text="Invert Colors")

        self.display_page()


    # NEW FULLSCREEN METHODS
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        
        if self.fullscreen:
            self.fullscreen_btn.config(text="✕ Exit Fullscreen", bg="#d32f2f")
        else:
            self.fullscreen_btn.config(text="⛶ Fullscreen", bg="#555")
        
        # Update display after fullscreen toggle
        if self.current_doc:
            self.display_page()


    def exit_fullscreen(self):
        if self.fullscreen:
            self.toggle_fullscreen()


    def mouse_wheel(self, event):

        ctrl = (event.state & 0x4) != 0

        if ctrl:

            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

        else:

            if event.delta < 0:
                self.next_page()
            else:
                self.prev_page()


    def prev_page(self):

        if self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            self.update_buttons()


    def next_page(self):

        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.display_page()
            self.update_buttons()


    def update_buttons(self):

        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)


    def zoom_in(self):

        self.zoom_level += 0.25
        self.display_page()


    def zoom_out(self):

        if self.zoom_level > 0.5:
            self.zoom_level -= 0.25
            self.display_page()


    def reset_zoom(self):

        self.zoom_level = 1
        self.display_page()


def main():

    root = tk.Tk()

    PDFViewer(root)

    root.mainloop()


if __name__ == "__main__":
    main()