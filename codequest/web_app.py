"""Mở giao diện web của game trong một cửa sổ desktop (pywebview + WebView2).

Một máy chủ nhỏ chỉ chạy trên máy (127.0.0.1):
- phục vụ trang web và hình ảnh, chỉ trong các thư mục webui/, gamekit/, assets/;
- nhận lệnh của trang qua POST /api/<tên hàm> (gọi WebApi). Mỗi lệnh phải kèm
  mã bí mật sinh ngẫu nhiên lúc mở game, nên trang web lạ không gọi được.

Chạy `python -m codequest.web_app --browser` để mở trong trình duyệt thường (dùng khi phát triển).
"""

from __future__ import annotations

import json
import secrets
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from .assets import APP_TITLE, BUNDLE_ROOT, backup_dir, user_data_dir
from .web_api import WebApi

SERVED_FOLDERS = ("webui", "gamekit", "assets")
API_METHODS = (
    "bootstrap", "level", "save_code", "run", "collection", "choose_hero", "buy_item", "finish_hero_pick",
    "save_settings", "backup", "restore", "completions", "music", "handbook",
)
TOKEN_HEADER = "X-Game-Token"
MAX_REQUEST_BYTES = 200_000
WINDOW_SIZE = (1440, 880)
MIN_WINDOW_SIZE = (1100, 700)


class GameServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, api: WebApi, token: str, root: Path) -> None:
        self.api = api
        self.token = token
        super().__init__(("127.0.0.1", 0), partial(GameRequestHandler, directory=str(root)))

    @property
    def port(self) -> int:
        return self.server_address[1]


class GameRequestHandler(SimpleHTTPRequestHandler):
    server: GameServer

    def send_head(self):  # type: ignore[no-untyped-def]
        path = unquote(urlsplit(self.path).path).lstrip("/")
        parts = Path(path).parts
        if not parts or parts[0] not in SERVED_FOLDERS or ".." in parts:
            self.send_error(404)
            return None
        return super().send_head()

    def do_POST(self) -> None:
        method_name = urlsplit(self.path).path.removeprefix("/api/")
        if self.headers.get(TOKEN_HEADER) != self.server.token or method_name not in API_METHODS:
            self.send_error(403)
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            self.send_error(413)
            return
        try:
            arguments = json.loads(self.rfile.read(length) or b"[]")
            result = getattr(self.server.api, method_name)(*arguments)
        except (KeyError, TypeError, ValueError) as error:
            self._send_json(400, {"error": str(error)})
            return
        if isinstance(result, bytes):
            self._send_bytes(result, "audio/wav")
            return
        self._send_json(200, result)

    def _send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def start_server(api: WebApi, root: Path = BUNDLE_ROOT) -> GameServer:
    server = GameServer(api, secrets.token_urlsafe(24), root)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def page_url(server: GameServer) -> str:
    return f"http://127.0.0.1:{server.port}/webui/index.html#token={server.token}"


def main(progress_file: Path | None = None, in_browser: bool = False) -> None:
    """Mở game giao diện web. Ném lỗi nếu máy không có WebView2 để nơi gọi chuyển sang bản pygame."""
    api = WebApi(progress_file or user_data_dir() / "progress.json", backup_dir())
    server = start_server(api)
    if in_browser:
        print(page_url(server))
        webbrowser.open(page_url(server))
        threading.Event().wait()
        return

    import webview

    try:
        webview.create_window(
            APP_TITLE,
            page_url(server),
            width=WINDOW_SIZE[0],
            height=WINDOW_SIZE[1],
            min_size=MIN_WINDOW_SIZE,
            background_color="#0a0e1f",
        )
        # Chỉ dùng Edge WebView2: không để pywebview lùi về trình duyệt IE cũ (vẽ sai giao diện).
        webview.start(gui="edgechromium")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main(in_browser="--browser" in sys.argv)
