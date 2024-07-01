import struct
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk

class ScrolledCanvas(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        self.scrollable_frame = ttk.Frame(self)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.configure(
                scrollregion=self.bbox("all")
            )
        )

        self.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.configure(yscrollcommand=self.scrollbar.set)

        self.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

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
            print(f"Magic: {self.magic}")
            if self.magic != b'Pat0':
                raise ValueError("Not a valid .pat file")

            # Read padding
            padding = f.read(12)
            print(f"Padding: {padding}")

            # Read patch count and geometry patches per color patch
            patch_count_and_geometry = f.read(4)
            self.patch_count, self.geometry_patches_per_color_patch = struct.unpack('<HH', patch_count_and_geometry)
            print(f"Patch Count: {self.patch_count}, Geometry Patches per Color Patch: {self.geometry_patches_per_color_patch}")

            # Read the offsets in the header
            while f.tell() % 16 != 0:
                pad_byte = f.read(1)
                print(f"Padding Byte: {pad_byte}")

            for _ in range(self.patch_count):
                paint_patches = []
                for _ in range(self.geometry_patches_per_color_patch):
                    offset_bytes = f.read(4)
                    offset = struct.unpack('<I', offset_bytes)[0]
                    paint_patches.append(offset)
                    print(f"Header Offset: {offset}, Bytes: {offset_bytes}")
                self.patches.append(paint_patches)

            # Read the color patches based on the offsets
            for paint_index, paint_patches in enumerate(self.patches):
                paint_data = []
                for offset in paint_patches:
                    f.seek(offset)
                    offset_data = f.read(8)
                    target_offset, patch_size = struct.unpack('<II', offset_data)
                    print(f"Target Offset: {target_offset}, Patch Size: {patch_size}, Bytes: {offset_data}")

                    # Read patch data
                    actual_patch_size = patch_size
                    remaining_bytes = (4 - patch_size % 4) % 4  # Calculate padding bytes
                    trunc_patch_size = patch_size + remaining_bytes
                    patch_data = f.read(trunc_patch_size)
                    print(f"Patch Data: {actual_patch_size}")

                    colors = [(patch_data[i], patch_data[i+1], patch_data[i+2], patch_data[i+3]) for i in range(0, len(patch_data), 4)]
                    paint_data.append({
                        'target_offset': target_offset,
                        'patch_size': trunc_patch_size,
                        'colors': colors,
                        'actual_patch_size': actual_patch_size
                    })
                    print(f"Colors: {colors}")

                self.patches[paint_index] = {
                    'header_offsets': paint_patches,
                    'paint_data': paint_data
                }

    def save(self, filename):
        try:
            with open(filename, 'wb') as f:
                # Write magic and padding
                f.write(b"Pat0")
                f.write(b'\x00' * 12)

                # Write patch count and geometry patches per color patch
                patch_count = self.patch_count
                geometry_patches_per_color_patch = self.geometry_patches_per_color_patch
                f.write(struct.pack('<H', patch_count))
                f.write(struct.pack('<H', geometry_patches_per_color_patch))

                print(f"patch_count: {patch_count}")
                print(f"patch_count: {geometry_patches_per_color_patch}")

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

        except IOError as e:
            raise IOError(f"Failed to save file: {e}")

    def get_patches(self):
        return self.patches
        
class CollapsibleFrame(ttk.Frame):
    def __init__(self, parent, text="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text = text

        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", pady=5)

        self.toggle_button = ttk.Button(self.header_frame, text=self.text, command=self.toggle)
        self.toggle_button.pack(side="left")

        self.sub_frame = ttk.Frame(self)

        self.collapsed = True
        self.toggle()

    def toggle(self):
        if self.collapsed:
            self.sub_frame.pack(fill="x", padx=5)
            self.collapsed = False
        else:
            self.sub_frame.pack_forget()
            self.collapsed = True

class PatEditor(tk.Tk):
    def __init__(self, pat_file):
        super().__init__()
        self.title("PAT File Editor")
        self.geometry("720x600")
        self.pat_file = pat_file
        self.create_widgets()

    def create_widgets(self):
        self.canvas = ScrolledCanvas(self)
        self.canvas.pack(expand=True, fill='both')

        self.notebook = ttk.Notebook(self.canvas.scrollable_frame)
        self.notebook.pack(expand=True, fill='both')

        for paint_index, paint in enumerate(self.pat_file.patches):
            paint_frame = ttk.Frame(self.notebook)
            self.notebook.add(paint_frame, text=f"Paint {paint_index}")

            color_frame = ttk.Frame(paint_frame)
            color_frame.pack(expand=True, fill='both')

            for patch_data in paint['paint_data']:
                for color_index, color in enumerate(patch_data['colors']):
                    if color_index % 32 == 0:
                        row_frame = ttk.Frame(color_frame)
                        row_frame.pack(side='top', fill='x')
                
                    color_swatch = tk.Canvas(row_frame, width=16, height=16)
                    color_swatch.pack(side='left', padx=2, pady=2)
                
                    rgb_color = color[:3]
                    hex_color = self.rgb_to_hex(rgb_color)
                    color_swatch.create_rectangle(0, 0, 16, 16, fill=hex_color)

        save_button = ttk.Button(self, text="Save", command=self.save_file)
        save_button.pack(side='left', padx=5, pady=5)

        export_button = ttk.Button(self, text="Export to PNG", command=self.export_png)
        export_button.pack(side='left', padx=5, pady=5)

        load_button = ttk.Button(self, text="Import PNG", command=self.load_png)
        load_button.pack(side='left', padx=5, pady=5)

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def rgb_to_hex(self, rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def save_file(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".pat", filetypes=[("PAT files", "*.pat")])
        if save_path:
            self.pat_file.save(save_path)
            messagebox.showinfo("Save", "File saved successfully")

    def export_png(self):
        export_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
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
        png_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
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

            # Update GUI with new colors
            for patch_data in paint['paint_data']:
                for color_index, new_color in enumerate(patch_data['colors']):
                    rgb_hex = self.rgb_to_hex(new_color[:3])
                    patch_data['color_canvases'][color_index].delete("all")  # Clear previous rectangle
                    patch_data['color_canvases'][color_index].create_rectangle(0, 0, 30, 20, fill=rgb_hex)  # Update color swatch
                    patch_data['color_labels'][color_index].config(text=f"RGBO: {new_color}")  # Update color label

            messagebox.showinfo("Load PNG", "PNG loaded successfully and applied to current paint")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update from PNG: {e}")

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

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
        file_path = filedialog.askopenfilename(filetypes=[("PAT files", "*.pat")])
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