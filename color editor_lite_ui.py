import struct
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk

class PatFile:
    def __init__(self, filename=None):
        self.filename = filename
        self.magic = b""
        self.patch_count = 0
        self.geometry_patches_per_color_patch = 0
        self.patches = []

    def read(self):
        with open(self.filename, 'rb') as f:
            # Read magic number
            self.magic = f.read(4)
            if self.magic != b'Pat0':
                raise ValueError("Not a valid .pat file")

            # Read padding
            padding = f.read(12)

            # Read patch count and geometry patches per color patch
            patch_count_and_geometry = f.read(4)
            self.patch_count, self.geometry_patches_per_color_patch = struct.unpack('<HH', patch_count_and_geometry)

            # Read the offsets in the header
            while f.tell() % 16 != 0:
                pad_byte = f.read(1)

            for _ in range(self.patch_count):
                paint_patches = []
                for _ in range(self.geometry_patches_per_color_patch):
                    offset_bytes = f.read(4)
                    offset = struct.unpack('<I', offset_bytes)[0]
                    paint_patches.append(offset)
                self.patches.append(paint_patches)

            # Read the color patches based on the offsets
            for paint_index, paint_patches in enumerate(self.patches):
                paint_data = []
                for offset in paint_patches:
                    f.seek(offset)
                    offset_data = f.read(8)
                    target_offset, patch_size = struct.unpack('<II', offset_data)

                    actual_patch_size = patch_size
                    remaining_bytes = (4 - patch_size % 4) % 4  # Calculate padding bytes
                    trunc_patch_size = patch_size + remaining_bytes
                    patch_data = f.read(trunc_patch_size)

                    colors = [(patch_data[i], patch_data[i+1], patch_data[i+2], patch_data[i+3]) for i in range(0, len(patch_data), 4)]
                    paint_data.append({
                        'target_offset': target_offset,
                        'patch_size': trunc_patch_size,
                        'colors': colors,
                        'actual_patch_size': actual_patch_size
                    })

                self.patches[paint_index] = {
                    'header_offsets': paint_patches,
                    'paint_data': paint_data
                }

    def save(self, filename):
        with open(filename, 'wb') as f:
            # Write magic and padding
            f.write(b"Pat0")
            f.write(b'\x00' * 12)

            # Write patch count and geometry patches per color patch
            f.write(struct.pack('<H', self.patch_count))
            f.write(struct.pack('<H', self.geometry_patches_per_color_patch))

            # Pad to next factor of 16
            f.write(b'\x00' * (16 - (f.tell() % 16)))

            # Write header entries
            for paint in self.patches:
                for header_offset in paint['header_offsets']:
                    f.write(struct.pack('<I', header_offset))

            # Write patch data
            for paint in self.patches:
                for patch_data in paint['paint_data']:
                    f.write(struct.pack('<II', patch_data['target_offset'], patch_data['actual_patch_size']))
                    for color in patch_data['colors']:
                        f.write(struct.pack('<4B', *color))

    def get_patches(self):
        return self.patches
        
class PatEditor(tk.Tk):
    def __init__(self, pat_file):
        super().__init__()
        self.title("PAT File Editor")
        self.geometry("720x600")
        self.pat_file = pat_file
        self.create_widgets()

    def create_widgets(self):
        # Create a notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        for paint_index, paint in enumerate(self.pat_file.get_patches()):
            paint_frame = ttk.Frame(self.notebook)
            self.notebook.add(paint_frame, text=f"Paint {paint_index}")

        # Add buttons for Save, Export, and Import
        save_button = ttk.Button(self, text="Save", command=self.save_file)
        save_button.pack(side='left', padx=5, pady=5)

        export_button = ttk.Button(self, text="Export to PNG", command=self.export_png)
        export_button.pack(side='left', padx=5, pady=5)

        load_button = ttk.Button(self, text="Import PNG", command=self.load_png)
        load_button.pack(side='left', padx=5, pady=5)

    def save_file(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".pat", filetypes=[("PAT files", "*.pat"), ("All files", "*.*")])
        if save_path:
            self.pat_file.save(save_path)
            messagebox.showinfo("Save", "File saved successfully")

    def export_png(self):
        export_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if export_path:
            self.create_png(export_path)
            messagebox.showinfo("Export", "PNG exported successfully")

    def create_png(self, path):
        paint_index = self.notebook.index('current')
        colors = [color for patch_data in self.pat_file.get_patches()[paint_index]['paint_data'] for color in patch_data['colors']]
        size = len(colors)
        image = Image.new("RGBA", (size, 1), (255, 255, 255, 0))
        for i, color in enumerate(colors):
            mapped_color = (color[0], color[1], color[2], color[3])
            image.putpixel((i, 0), mapped_color)
        image.save(path)

    def load_png(self):
        png_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if png_path:
            try:
                self.update_from_png(png_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PNG: {e}")

    def update_from_png(self, png_path):
        paint_index = self.notebook.index('current')
        paint = self.pat_file.get_patches()[paint_index]
    
        try:
            png_image = Image.open(png_path)
            png_pixels = png_image.load()
    
            # Ensure PNG width matches the number of colors in the current paint
            if png_image.width != sum(len(patch['colors']) for patch in paint['paint_data']):
                messagebox.showerror("Error", "PNG width does not match number of colors in the current paint")
                return
    
            color_index = 0
            for patch_data in paint['paint_data']:
                for color_idx, color in enumerate(patch_data['colors']):
                    new_color = png_pixels[color_index, 0]
                    patch_data['colors'][color_idx] = new_color
                    color_index += 1

            messagebox.showinfo("Load PNG", "PNG loaded successfully and applied to current paint")
    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update from PNG: {e}")

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PAT File Selector")
        self.geometry("300x200")  # Set a reasonable default window size
        self.create_widgets()

    def create_widgets(self):
        open_button = ttk.Button(self, text="Open PAT File", command=self.open_pat_file)
        open_button.pack(expand=True)

    def open_pat_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PAT files", "*.pat"), ("All files", "*.*")])
        if file_path:
            try:
                pat = PatFile(file_path)
                pat.read()
                editor = PatEditor(pat)
                self.withdraw()  # Hide the main window
                editor.mainloop()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

# Run the main app
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
