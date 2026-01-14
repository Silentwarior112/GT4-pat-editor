import os
import struct
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


class PatFile:
    def __init__(self, filename=None):
        self.filename = filename
        self.magic = b""
        self.patch_count = 0
        self.geometry_patches_per_color_patch = 0
        self.patches = []

    def read(self):
        self.patches = []

        with open(self.filename, 'rb') as f:
            self.magic = f.read(4)
            if self.magic != b'Pat0':
                raise ValueError("Not a valid .pat file (missing Pat0 magic)")

            f.read(12)  # padding

            patch_count_and_geometry = f.read(4)
            self.patch_count, self.geometry_patches_per_color_patch = struct.unpack('<HH', patch_count_and_geometry)

            while f.tell() % 16 != 0:
                f.read(1)

            raw_offsets = []
            for _ in range(self.patch_count):
                paint_patches = []
                for _ in range(self.geometry_patches_per_color_patch):
                    offset_bytes = f.read(4)
                    if len(offset_bytes) != 4:
                        raise ValueError("Unexpected EOF while reading header offsets")
                    offset = struct.unpack('<I', offset_bytes)[0]
                    paint_patches.append(offset)
                raw_offsets.append(paint_patches)

            for paint_patches in raw_offsets:
                paint_data = []
                for header_offset in paint_patches:
                    f.seek(header_offset)

                    offset_data = f.read(8)
                    if len(offset_data) != 8:
                        raise ValueError(f"Unexpected EOF while reading patch header at 0x{header_offset:X}")

                    target_offset, patch_size = struct.unpack('<II', offset_data)

                    remaining_bytes = (4 - patch_size % 4) % 4
                    padded_size = patch_size + remaining_bytes

                    patch_data = f.read(padded_size)
                    if len(patch_data) != padded_size:
                        raise ValueError(f"Unexpected EOF while reading patch bytes at 0x{header_offset:X}")

                    colors = [
                        (patch_data[i], patch_data[i + 1], patch_data[i + 2], patch_data[i + 3])
                        for i in range(0, len(patch_data), 4)
                    ]

                    paint_data.append({
                        'target_offset': target_offset,
                        'actual_patch_size': patch_size,
                        'padded_patch_size': padded_size,
                        'colors': colors,
                        'header_offset': header_offset
                    })

                self.patches.append({
                    'header_offsets': paint_patches,
                    'paint_data': paint_data
                })

    def get_patches(self):
        return self.patches

    def build_patch_bytes(self, patch_data: dict) -> bytes:
        raw = bytearray()
        for (r, g, b, a) in patch_data['colors']:
            raw += struct.pack('<4B', r, g, b, a)
        return bytes(raw[:patch_data['actual_patch_size']])

    def apply_paints_to_copies(
        self,
        target_path: str,
        paint_indices=None,
        output_dir=None,
        output_stem=None
    ):
        """
        Creates one patched output file per paint (never modifies the original).
        FAIL-FAST: if ANY selected paint contains ANY patch that would exceed EOF,
        the function raises ValueError and does nothing (no folder, no files).
        """
        if paint_indices is None:
            paint_indices = list(range(len(self.patches)))
        else:
            paint_indices = sorted(set(int(x) for x in paint_indices))

        if not os.path.isfile(target_path):
            raise FileNotFoundError(f"Target file not found:\n{target_path}")

        file_size = os.path.getsize(target_path)

        # --------- PREFLIGHT EOF CHECK (FAIL FAST) ----------
        eof_errors = []
        for pi in paint_indices:
            if pi < 0 or pi >= len(self.patches):
                eof_errors.append(f"Paint {pi}: out of range (PAT has {len(self.patches)} paints).")
                continue

            paint = self.patches[pi]
            for gi, patch_data in enumerate(paint["paint_data"]):
                target_offset = patch_data["target_offset"]
                patch_len = patch_data["actual_patch_size"]  # strict size (no padding)
                end_offset = target_offset + patch_len

                # target_offset itself should also be inside file
                if target_offset < 0 or target_offset > file_size:
                    eof_errors.append(
                        f"Paint {pi}, GeoPatch {gi}: target_offset 0x{target_offset:X} outside file "
                        f"(file size 0x{file_size:X})."
                    )
                elif end_offset > file_size:
                    eof_errors.append(
                        f"Paint {pi}, GeoPatch {gi}: would exceed EOF.\n"
                        f"  target_offset: 0x{target_offset:X}\n"
                        f"  patch_size:    0x{patch_len:X}\n"
                        f"  end:           0x{end_offset:X}\n"
                        f"  file_size:     0x{file_size:X}"
                    )

        if eof_errors:
            # Keep the popup readable: show up to first ~10 issues, with a count
            max_show = 10
            shown = eof_errors[:max_show]
            more = len(eof_errors) - len(shown)
            msg = "Cannot apply patches: one or more selected patches exceed EOF (or are invalid).\n\n"
            msg += "\n\n".join(shown)
            if more > 0:
                msg += f"\n\n...and {more} more."
            raise ValueError(msg)
        # ---------------------------------------------------

        src_dir = os.path.dirname(target_path)
        base = os.path.basename(target_path)
        stem, ext = os.path.splitext(base)

        if output_stem is None:
            output_stem = stem
        if output_dir is None:
            output_dir = os.path.join(src_dir, f"{stem}_allcolors")

        # Only now do we create the folder (since preflight passed)
        os.makedirs(output_dir, exist_ok=True)

        outputs = []

        for out_idx, pi in enumerate(paint_indices):
            out_name = f"{output_stem}_{out_idx:02d}{ext}"
            out_path = os.path.join(output_dir, out_name)

            # Copy original -> output
            shutil.copy2(target_path, out_path)
            logs = [f"Created: {out_name}", f"== Applying Paint {pi} =="]

            paint = self.patches[pi]
            with open(out_path, "r+b") as tf:
                for gi, patch_data in enumerate(paint["paint_data"]):
                    target_offset = patch_data["target_offset"]
                    patch_bytes = self.build_patch_bytes(patch_data)  # already truncated to actual size
                    tf.seek(target_offset)
                    tf.write(patch_bytes)
                    logs.append(f"[OK] GeoPatch {gi}: wrote 0x{len(patch_bytes):X} bytes to 0x{target_offset:X}")

            outputs.append({
                "paint_index": pi,
                "out_path": out_path,
                "logs": logs
            })

        return output_dir, outputs


class PatchApplicatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Color Patch Applicator (.pat)")
        self.geometry("760x560")

        self.pat = None
        self.pat_path = tk.StringVar(value="")
        self.target_path = tk.StringVar(value="")

        self.paint_vars = []
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        pat_row = ttk.Frame(top)
        pat_row.pack(fill="x", pady=(0, 6))
        ttk.Label(pat_row, text="PAT file:").pack(side="left")
        ttk.Entry(pat_row, textvariable=self.pat_path).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(pat_row, text="Browse…", command=self._browse_pat).pack(side="left")

        tgt_row = ttk.Frame(top)
        tgt_row.pack(fill="x", pady=(0, 6))
        ttk.Label(tgt_row, text="Target file:").pack(side="left")
        ttk.Entry(tgt_row, textvariable=self.target_path).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(tgt_row, text="Browse…", command=self._browse_target).pack(side="left")

        mid = ttk.Frame(self, padding=(10, 0, 10, 10))
        mid.pack(fill="both", expand=True)

        left = ttk.Labelframe(mid, text="Paints to output", padding=10)
        left.pack(side="left", fill="y")

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=(0, 8))
        ttk.Button(btns, text="All", command=self._select_all).pack(side="left")
        ttk.Button(btns, text="None", command=self._select_none).pack(side="left", padx=(6, 0))

        self.paint_list_frame = ttk.Frame(left)
        self.paint_list_frame.pack(fill="y", expand=True)

        right = ttk.Labelframe(mid, text="Log", padding=10)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self.log_text = tk.Text(right, wrap="none", height=10)
        self.log_text.pack(fill="both", expand=True)

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Output Selected Paint Files", command=self._apply).pack(side="right")

        self._log("Load a .pat file, choose a target, then output selected paints.")

    def _log(self, msg: str):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")

    def _browse_pat(self):
        path = filedialog.askopenfilename(filetypes=[("PAT files", "*.pat"), ("All files", "*.*")])
        if not path:
            return
        try:
            pat = PatFile(path)
            pat.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read PAT:\n{e}")
            return

        self.pat = pat
        self.pat_path.set(path)
        self._rebuild_paint_checklist()

        self._log(f"Loaded PAT: {os.path.basename(path)}")
        self._log(f"PatchCount: {pat.patch_count} | GeoPatches/ColorPatch: {pat.geometry_patches_per_color_patch}")
        self._log(f"Detected paints: {len(pat.get_patches())}")

    def _browse_target(self):
        path = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if not path:
            return
        self.target_path.set(path)
        self._log(f"Target set: {os.path.basename(path)}")

    def _rebuild_paint_checklist(self):
        for child in self.paint_list_frame.winfo_children():
            child.destroy()
        self.paint_vars = []

        if not self.pat:
            return

        for i in range(len(self.pat.get_patches())):
            v = tk.BooleanVar(value=True)
            self.paint_vars.append(v)
            ttk.Checkbutton(self.paint_list_frame, text=f"Paint {i}", variable=v).pack(anchor="w")

    def _select_all(self):
        for v in self.paint_vars:
            v.set(True)

    def _select_none(self):
        for v in self.paint_vars:
            v.set(False)

    def _apply(self):
        if not self.pat:
            messagebox.showwarning("Missing PAT", "Please load a .pat file first.")
            return

        target = self.target_path.get().strip()
        if not target:
            messagebox.showwarning("Missing Target", "Please choose a target file.")
            return

        selected = [i for i, v in enumerate(self.paint_vars) if v.get()]
        if not selected:
            messagebox.showwarning("Nothing Selected", "Select at least one Paint to output.")
            return

        try:
            out_dir, outputs = self.pat.apply_paints_to_copies(
                target_path=target,
                paint_indices=selected
            )
        except ValueError as e:
            # FAIL-FAST EOF (or other validation) error: clear, direct popup
            messagebox.showerror("Patch exceeds EOF", str(e))
            return
        except Exception as e:
            messagebox.showerror("Output Failed", f"Failed to output patched files:\n{e}")
            return

        self._log("")
        self._log("=== OUTPUT RESULT ===")
        self._log(f"Folder: {out_dir}")
        for item in outputs:
            self._log("")
            pi = item["paint_index"]
            out_path = item["out_path"]
            self._log(f"--- Paint {pi} -> {os.path.basename(out_path)} ---")
            for line in item["logs"]:
                self._log(line)

        messagebox.showinfo("Done", f"Finished.\nOutput folder:\n{out_dir}")


if __name__ == "__main__":
    app = PatchApplicatorApp()
    app.mainloop()
