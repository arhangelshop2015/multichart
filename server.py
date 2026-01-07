"""HTTP API for Multichart v4."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional

from capture import capture_retina_png
from chrome import ChromeCDP
from ui import MultiChartGrid


class MultichartService:
    def __init__(self) -> None:
        self.chrome = ChromeCDP()
        self.grid = MultiChartGrid()

    def open_url(self, url: str, row: Optional[int], col: Optional[int]) -> Dict[str, Any]:
        target_id = self.chrome.open_url_sync(url)
        if row is None or col is None:
            cell = self.grid.next_empty_cell()
            if cell is None:
                raise ValueError("No empty cells available")
            row, col = cell.row, cell.col
        self.grid.assign_tab(row, col, target_id)
        return {"targetId": target_id, "row": row, "col": col}

    def activate_cell(self, x: int, y: int) -> Dict[str, Any]:
        cell = self.grid.cell_for_point(x, y)
        if cell is None:
            raise ValueError("Point outside grid")
        target_id = self.grid.tab_for_cell(cell.row, cell.col)
        if not target_id:
            raise ValueError("No tab assigned to cell")
        self.chrome.activate_tab_sync(target_id)
        return {"targetId": target_id, "row": cell.row, "col": cell.col}

    def capture_cell(self, row: int, col: int, output_path: str) -> Dict[str, Any]:
        target_id = self.grid.tab_for_cell(row, col)
        if not target_id:
            raise ValueError("No tab assigned to cell")
        path = capture_retina_png(self.chrome, target_id, output_path)
        return {"targetId": target_id, "path": path}


SERVICE = MultichartService()


class RequestHandler(BaseHTTPRequestHandler):
    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(payload)

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json()
            if self.path == "/open":
                result = SERVICE.open_url(
                    payload["url"], payload.get("row"), payload.get("col")
                )
                self._send_json(200, result)
                return
            if self.path == "/click":
                result = SERVICE.activate_cell(payload["x"], payload["y"])
                self._send_json(200, result)
                return
            if self.path == "/capture":
                result = SERVICE.capture_cell(
                    payload["row"], payload["col"], payload["output"]
                )
                self._send_json(200, result)
                return
            self._send_json(404, {"error": "not_found"})
        except (KeyError, ValueError) as exc:
            self._send_json(400, {"error": str(exc)})


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    server = HTTPServer((host, port), RequestHandler)
    print(f"Multichart v4 API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
