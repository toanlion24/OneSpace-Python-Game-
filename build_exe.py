"""Đóng gói OneSpace CodeQuest thành bản Windows để gửi cho học sinh.

Chạy:  python build_exe.py
Kết quả: release/OneSpace-CodeQuest-v<phiên bản>-Windows.zip
         (giải nén → bấm đúp OneSpace-CodeQuest.exe)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from codequest import __version__
from codequest.assets import LOGO_ICON_BOX
from codequest.engine import ALLOWED_MODULES

BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "dist"
RELEASE_DIR = ROOT / "release"
STAGING_KIT = BUILD_DIR / "gamekit"
APP_NAME = "OneSpace-CodeQuest"
RELEASE_NAME = f"{APP_NAME}-v{__version__}-Windows"

# Chỉ chép các thư mục ảnh game thật sự dùng (bỏ PSD, file zip, bản đồ Tiled...).
KIT_FOLDERS_USED = [
    "1 Main Characters",
    "2 Locations/Backgrounds",
    "2 Locations/Tiles/Tileset.png",
    "3 Objects/Checkpoints",
    "3 Objects/Gems",
    "4 Enemies",
    "6 Traps",
    "License.txt",
]

GUIDE = f"""ONESPACE CODEQUEST - HỌC PYTHON QUA TRÒ CHƠI (v{__version__})
==============================================================

Chơi như CodeCombat: viết code Python để điều khiển hero.
Học theo lộ trình HackerRank Python: 5 giai đoạn, 48 màn.
Dành cho học sinh THCS - THPT.

CÁCH MỞ GAME
1. Giải nén cả thư mục (chuột phải file .zip → Extract All).
   KHÔNG chạy trực tiếp bên trong file .zip.
2. Mở thư mục {APP_NAME}, bấm đúp {APP_NAME}.exe.
3. Nếu Windows hiện "Windows protected your PC":
   bấm "More info" (Thông tin thêm) → "Run anyway" (Vẫn chạy).

CÁCH CHƠI
- Chọn giai đoạn và màn ở menu, đọc phần Lý thuyết, viết code ở khung bên phải.
- Bấm Chạy (hoặc Ctrl+Enter) để hero làm theo code của bạn.
- Gợi ý: gợi hướng suy nghĩ khi bị bí.
- Gõ tiếng Việt: dùng bộ gõ Telex có sẵn trong game (F2 bật/tắt),
  chỉ có tác dụng trong dấu nháy "..." và ghi chú #.
  Nên TẮT Unikey/EVKey khi chơi để tránh gõ chồng.

LƯU TIẾN ĐỘ
- Tự lưu vào: %APPDATA%\\OneSpaceCodeQuest\\progress.json
- Muốn chơi lại từ đầu: xoá file progress.json đó.

Yêu cầu: Windows 10/11 64-bit. Không cần cài Python.
Đồ hoạ: bộ Free Simple Platformer Game Kit của CraftPix.net (xem gamekit/License.txt).
"""


def stage_assets() -> None:
    source_kit = ROOT / "gamekit"
    if STAGING_KIT.exists():
        shutil.rmtree(STAGING_KIT)
    for relative in KIT_FOLDERS_USED:
        source = source_kit / relative
        target = STAGING_KIT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def make_icon() -> Path:
    logo = Image.open(ROOT / "assets" / "onespace_logo.png").convert("RGBA")
    emblem = logo.crop(LOGO_ICON_BOX).resize((256, 256), Image.LANCZOS)
    icon_path = BUILD_DIR / "onespace.ico"
    emblem.save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return icon_path


def run_pyinstaller(icon_path: Path) -> None:
    separator = ";" if sys.platform.startswith("win") else ":"
    # Học sinh import các thư viện này bằng chuỗi lúc chạy, PyInstaller không tự thấy được.
    hidden_imports = [item for module in sorted(ALLOWED_MODULES) for item in ("--hidden-import", module)]
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--windowed",
        "--name", APP_NAME,
        "--icon", str(icon_path),
        "--add-data", f"{STAGING_KIT}{separator}gamekit",
        "--add-data", f"{ROOT / 'assets'}{separator}assets",
        *hidden_imports,
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR / "pyinstaller"),
        "--specpath", str(BUILD_DIR),
        "--exclude-module", "pytest",
        "--exclude-module", "tkinter",
        str(ROOT / "main.py"),
    ]
    subprocess.run(command, check=True)


def make_release() -> Path:
    app_dir = DIST_DIR / APP_NAME
    (app_dir / "HUONG DAN.txt").write_text(GUIDE, encoding="utf-8-sig")
    RELEASE_DIR.mkdir(exist_ok=True)
    archive_base = RELEASE_DIR / RELEASE_NAME
    archive = shutil.make_archive(str(archive_base), "zip", root_dir=DIST_DIR, base_dir=APP_NAME)
    return Path(archive)


def main() -> None:
    BUILD_DIR.mkdir(exist_ok=True)
    stage_assets()
    icon_path = make_icon()
    run_pyinstaller(icon_path)
    archive = make_release()
    size_mb = archive.stat().st_size / 1_000_000
    print(f"\nĐã tạo {archive} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
