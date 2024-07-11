import tkinter as tk
from tkinter import filedialog, messagebox

def read_file(file_path):
    with open(file_path, 'rb') as f:
        return bytearray(f.read())

def add_color_entry(data):
    color_count = int.from_bytes(data[16:18], 'little')
    offset_count_per_color = int.from_bytes(data[18:20], 'little')
    offset_start = 32
    data_start = offset_start + (color_count * offset_count_per_color * 4)
    
    offsets = [int.from_bytes(data[i:i+4], 'little') for i in range(offset_start, data_start, 4)]
    if color_count == 1:
        block_size = len(data) - offsets[0]
    else:
        block_size = offsets[offset_count_per_color] - offsets[0]
    offset_chunk_size = offset_count_per_color * 4
    
    new_color_data = data[offsets[-offset_count_per_color]:offsets[-1] + block_size]
    
    new_offsets = [
        (offset + block_size + offset_chunk_size) for offset in offsets[-offset_count_per_color:]
    ]
    
    updated_offsets = [offset + offset_chunk_size for offset in offsets]
    new_color_count = color_count + 1
    data[16:18] = new_color_count.to_bytes(2, 'little')
    
    new_offset_data = b''.join(offset.to_bytes(4, 'little') for offset in new_offsets)
    updated_offset_data = b''.join(offset.to_bytes(4, 'little') for offset in updated_offsets)
    
    new_data = (
        data[:16] +
        new_color_count.to_bytes(2, 'little') +
        data[18:32] +
        updated_offset_data +
        new_offset_data +
        data[data_start:] +
        new_color_data
    )
    
    return new_data

def select_file():
    file_path = filedialog.askopenfilename(
        title="Select a color patch file",
        filetypes=[("PAT files", "*.pat"), ("All files", "*.*")]
    )
    if file_path:
        data = read_file(file_path)
        root.file_data = data
        root.original_size = len(data)
        update_display()

def add_color():
    if hasattr(root, 'file_data'):
        root.file_data = add_color_entry(root.file_data)
        update_display()
    else:
        messagebox.showerror("Error", "No file loaded.")

def save_file():
    if hasattr(root, 'file_data'):
        file_path = filedialog.asksaveasfilename(
            title="Save the modified pat file",
            defaultextension=".bin",
            filetypes=[("PAT files", "*.pat"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'wb') as f:
                f.write(root.file_data)
            messagebox.showinfo("Success", "File saved successfully!")
    else:
        messagebox.showerror("Error", "No file loaded.")

def update_display():
    color_count = int.from_bytes(root.file_data[16:18], 'little')
    current_size = len(root.file_data)
    size_difference = current_size - root.original_size
    
    color_count_label.config(text=f"Current Color Count: {color_count}")
    original_size_label.config(text=f"Original Size: {root.original_size} bytes")
    new_size_label.config(text=f"New Size: {current_size} bytes")
    size_difference_label.config(text=f"Size Difference: {size_difference} bytes")

# GUI setup
root = tk.Tk()
root.title("Color Entry Adder")
root.geometry("400x320")

select_button = tk.Button(root, text="Select File", command=select_file)
select_button.pack(pady=10)

color_count_label = tk.Label(root, text="Current Color Count: 0")
color_count_label.pack(pady=5)

original_size_label = tk.Label(root, text="Original Size: 0 bytes")
original_size_label.pack(pady=5)

new_size_label = tk.Label(root, text="New Size: 0 bytes")
new_size_label.pack(pady=5)

size_difference_label = tk.Label(root, text="Size Difference: 0 bytes")
size_difference_label.pack(pady=5)

size_difference_label2 = tk.Label(root, text="(Menu models) Increase the offset location values by this amount.")
size_difference_label2.pack(pady=5)

add_color_button = tk.Button(root, text="Add Color", command=add_color)
add_color_button.pack(pady=10)

save_button = tk.Button(root, text="Save File", command=save_file)
save_button.pack(pady=10)

root.mainloop()
