import tkinter as tk
from tkinter import filedialog, messagebox
import struct
import os

# Define constants
MAGIC = b'CAR4'
OFFSET_SECTION_SIZE = 10 * 4
ASSET_NAMES = [
    "CarInfo", "CarCollision", "MainModel", "MainModelColorPatch",
    "WheelModel", "WheelColorPatch", "WingModelSet",
    "TireModel_0", "TireModel_1", "DriverModel"
]
DEFAULT_EXTENSIONS = {
    "MainModelColorPatch": ".pat",
    "WheelColorPatch": ".pat"
}

class FileExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Model File Extractor and Rebuilder")
        self.root.geometry("400x100")
        
        self.offsets = []
        self.file_data = None

        self.select_file_btn = tk.Button(root, text="Extract Model", command=self.extractor_load_file)
        self.select_file_btn.pack(pady=10)
        
        self.rebuild_file_btn = tk.Button(root, text="Rebuild Model", command=self.rebuilder_load_file)
        self.rebuild_file_btn.pack(pady=10)

    def extractor_load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if not file_path:
            return
        
        with open(file_path, "rb") as f:
            self.file_data = f.read()
        
        if self.file_data[:4] != MAGIC:
            messagebox.showerror("Error", "Invalid model file format!")
            return

        print (f"Extractor:  Model file loaded")
            
        self.extract_offsets()
        self.show_asset_selection()
        
    def rebuilder_load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if not file_path:
            return
        
        with open(file_path, "rb") as f:
            self.file_data = f.read()
        
        if self.file_data[:4] != MAGIC:
            messagebox.showerror("Error", "Invalid model file format!")
            return
        
        print (f"Rebuilder:  Model file loaded")
            
        self.extract_offsets()
        self.rebuild_file()
    
    def extract_offsets(self):
        self.offsets = []
        offset_section = self.file_data[16:16+OFFSET_SECTION_SIZE]
        for i in range(0, OFFSET_SECTION_SIZE, 4):
            offset, = struct.unpack_from("<I", offset_section, i)
            self.offsets.append(offset)
    
    def show_asset_selection(self):
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.title("Select Assets to Extract")
        self.selection_window.geometry("300x300")

        self.asset_vars = []
        for i, offset in enumerate(self.offsets):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.selection_window, text=ASSET_NAMES[i], variable=var)
            chk.pack(anchor="w")
            if offset == 0:
                chk.config(state=tk.DISABLED)
            self.asset_vars.append((ASSET_NAMES[i], var))
        
        extract_btn = tk.Button(self.selection_window, text="Extract Selected", command=self.extract_selected)
        extract_btn.pack(pady=10)
    
    def extract_selected(self):
        files_saved = False
        for i, (asset_name, var) in enumerate(self.asset_vars):
            if var.get():
                start_offset = self.offsets[i]
                end_offset = self.find_next_offset(i)
                asset_data = self.file_data[start_offset:end_offset]
                
                ext = DEFAULT_EXTENSIONS.get(asset_name, ".bin")
                output_path = filedialog.asksaveasfilename(defaultextension=ext, initialfile=asset_name, filetypes=[("All files", "*.*")])
                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(asset_data)
                    files_saved = True
        
        if files_saved:
            messagebox.showinfo("Success", "Selected assets have been extracted.")
        self.selection_window.destroy()
    
    def find_next_offset(self, index):
        for next_offset in self.offsets[index + 1:]:
            if next_offset != 0:
                return next_offset
        return len(self.file_data)

    def rebuild_file(self):
        Rebuilder(self.root, self.file_data, self.offsets)

class Rebuilder:
    def __init__(self, root, original_file_data, original_offsets):
        self.root = root
        self.original_file_data = original_file_data
        self.original_offsets = original_offsets
        self.new_assets = {}

        self.select_input_folder()

    def select_input_folder(self):
        self.input_folder = filedialog.askdirectory()
        if not self.input_folder:
            return
        
        self.detect_assets()
        self.show_asset_selection()

    def detect_assets(self):
        self.detected_assets = {}
        for asset_name in ASSET_NAMES:
            ext = DEFAULT_EXTENSIONS.get(asset_name, ".bin")
            asset_path = os.path.join(self.input_folder, f"{asset_name}{ext}")
            if os.path.isfile(asset_path):
                self.detected_assets[asset_name] = asset_path

    def show_asset_selection(self):
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.title("Select Assets to Replace")
        self.selection_window.geometry("300x300")

        self.asset_vars = []
        for asset_name in ASSET_NAMES:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.selection_window, text=asset_name, variable=var)
            chk.pack(anchor="w")
            if asset_name not in self.detected_assets:
                chk.config(state=tk.DISABLED)
            self.asset_vars.append((asset_name, var))
        
        replace_btn = tk.Button(self.selection_window, text="Replace Selected", command=self.replace_selected)
        replace_btn.pack(pady=10)

    def replace_selected(self):
        for asset_name, var in self.asset_vars:
            if var.get() and asset_name in self.detected_assets:
                with open(self.detected_assets[asset_name], "rb") as f:
                    self.new_assets[asset_name] = f.read()
        
        self.rebuild_model_file()
        self.selection_window.destroy()
        messagebox.showinfo("Success", "Model file has been rebuilt with selected assets.")

    def rebuild_model_file(self):
        new_file_data = bytearray(self.original_file_data[:16 + OFFSET_SECTION_SIZE + 8])
        new_offsets = list(self.original_offsets)
        current_offset = 16 + OFFSET_SECTION_SIZE + 8
        
        for i, asset_name in enumerate(ASSET_NAMES):
            if asset_name in self.new_assets:
                asset_data = self.new_assets[asset_name]
                padded_data = self.pad_to_16_bytes(asset_data)
                new_file_data.extend(padded_data)
                new_offsets[i] = current_offset
                current_offset += len(padded_data)
            else:
                start_offset = self.original_offsets[i]
                if start_offset != 0:
                    end_offset = self.find_next_offset(i)
                    asset_data = self.original_file_data[start_offset:end_offset]
                    padded_data = self.pad_to_16_bytes(asset_data)
                    new_file_data.extend(padded_data)
                    new_offsets[i] = current_offset
                    current_offset += len(padded_data)
                else:
                    new_offsets[i] = 0
        
        # Update the total byte count
        total_byte_count = len(new_file_data)
        struct.pack_into("<I", new_file_data, 8, total_byte_count)

        new_file_data[16:16 + OFFSET_SECTION_SIZE] = struct.pack("<" + "I" * 10, *new_offsets)
        new_file_path = filedialog.asksaveasfilename(defaultextension="", initialfile="NewModel", filetypes=[("Model files", "*.*")])
        if new_file_path:
            with open(new_file_path, "wb") as f:
                f.write(new_file_data)

    def pad_to_16_bytes(self, data):
        padding_needed = (16 - (len(data) % 16)) % 16
        return data + b'\x00' * padding_needed

    def find_next_offset(self, index):
        for next_offset in self.original_offsets[index + 1:]:
            if next_offset != 0:
                return next_offset
        return len(self.original_file_data)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileExtractor(root)
    root.mainloop()
