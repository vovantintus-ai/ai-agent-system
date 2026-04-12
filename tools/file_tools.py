"""
File Tools - Windows compatible
"""

import os
import shutil
from pathlib import Path

# Safe base: user's home directory (C:\Users\Username)
SAFE_BASE = str(Path.home())


def _safe_path(path: str) -> str:
    """Ensure path is within safe directory"""
    abs_path = str(Path(os.path.expanduser(path)).resolve())
    if not abs_path.startswith(SAFE_BASE):
        raise PermissionError(f"Access denied: {path}. Only allowed in {SAFE_BASE}")
    return abs_path


class FileTools:
    def read_file(self, path: str) -> str:
        safe = _safe_path(path)
        if not os.path.exists(safe):
            return f"File not found: {path}"
        if os.path.getsize(safe) > 1_000_000:
            return "File too large (>1MB)."
        with open(safe, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def write_file(self, path: str, content: str) -> str:
        safe = _safe_path(path)
        os.makedirs(os.path.dirname(safe), exist_ok=True)
        with open(safe, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ File saved: {path} ({len(content)} chars)"

    def list_directory(self, path: str = ".") -> str:
        safe = _safe_path(path)
        if not os.path.exists(safe):
            return f"Directory not found: {path}"
        items = []
        for item in sorted(os.listdir(safe)):
            full = os.path.join(safe, item)
            if os.path.isdir(full):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(full)
                items.append(f"📄 {item} ({self._fmt(size)})")
        return f"Contents of {path}:\n" + "\n".join(items) if items else "Empty directory"

    def delete_file(self, path: str) -> str:
        safe = _safe_path(path)
        if not os.path.exists(safe):
            return f"Not found: {path}"
        if os.path.isdir(safe):
            os.rmdir(safe)
            return f"✅ Directory deleted: {path}"
        os.remove(safe)
        return f"✅ File deleted: {path}"

    def move_file(self, source: str, destination: str) -> str:
        safe_src = _safe_path(source)
        safe_dst = _safe_path(destination)
        if not os.path.exists(safe_src):
            return f"Source not found: {source}"
        shutil.move(safe_src, safe_dst)
        return f"✅ Moved: {source} → {destination}"

    def _fmt(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
