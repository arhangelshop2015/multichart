"""Chrome DevTools Protocol helpers for Multichart v4."""

from __future__ import annotations

import asyncio
import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

import websockets

from config import VIEWPORT_HEIGHT, VIEWPORT_WIDTH, deviceScaleFactor


@dataclass
class CDPResponse:
    id: int
    result: Dict[str, Any]


class ChromeCDP:
    """Thin CDP client for creating/activating tabs and taking screenshots."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9333) -> None:
        self.host = host
        self.port = port
        self._message_id = 0

    def _next_id(self) -> int:
        self._message_id += 1
        return self._message_id

    def _version_url(self) -> str:
        return f"http://{self.host}:{self.port}/json/version"

    def _websocket_url(self) -> str:
        with urllib.request.urlopen(self._version_url()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["webSocketDebuggerUrl"]

    async def _send_cmd(
        self,
        websocket: websockets.WebSocketClientProtocol,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> CDPResponse:
        payload: Dict[str, Any] = {
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }
        if session_id:
            payload["sessionId"] = session_id
        await websocket.send(json.dumps(payload))
        while True:
            raw = await websocket.recv()
            message = json.loads(raw)
            if message.get("id") == payload["id"]:
                return CDPResponse(id=message["id"], result=message.get("result", {}))

    async def _attach_to_target(
        self, websocket: websockets.WebSocketClientProtocol, target_id: str
    ) -> str:
        response = await self._send_cmd(
            websocket,
            "Target.attachToTarget",
            {"targetId": target_id, "flatten": True},
        )
        return response.result["sessionId"]

    async def _set_viewport(
        self, websocket: websockets.WebSocketClientProtocol, session_id: str
    ) -> None:
        await self._send_cmd(
            websocket,
            "Emulation.setDeviceMetricsOverride",
            {
                "width": VIEWPORT_WIDTH,
                "height": VIEWPORT_HEIGHT,
                "deviceScaleFactor": deviceScaleFactor,
                "mobile": False,
            },
            session_id=session_id,
        )

    async def _capture_screenshot(
        self,
        websocket: websockets.WebSocketClientProtocol,
        session_id: str,
        clip: Optional[Dict[str, Any]] = None,
    ) -> str:
        params: Dict[str, Any] = {"format": "png", "fromSurface": True}
        if clip:
            params["clip"] = clip
        response = await self._send_cmd(
            websocket, "Page.captureScreenshot", params, session_id=session_id
        )
        return response.result["data"]

    async def open_url(self, url: str) -> str:
        async with websockets.connect(self._websocket_url()) as websocket:
            response = await self._send_cmd(
                websocket, "Target.createTarget", {"url": url}
            )
            return response.result["targetId"]

    async def activate_tab(self, target_id: str) -> None:
        async with websockets.connect(self._websocket_url()) as websocket:
            await self._send_cmd(
                websocket, "Target.activateTarget", {"targetId": target_id}
            )

    async def capture_screenshot(self, target_id: str) -> str:
        async with websockets.connect(self._websocket_url()) as websocket:
            session_id = await self._attach_to_target(websocket, target_id)
            await self._send_cmd(websocket, "Page.enable", session_id=session_id)
            await self._set_viewport(websocket, session_id)
            return await self._capture_screenshot(websocket, session_id)

    def open_url_sync(self, url: str) -> str:
        return asyncio.run(self.open_url(url))

    def activate_tab_sync(self, target_id: str) -> None:
        asyncio.run(self.activate_tab(target_id))

    def capture_screenshot_sync(self, target_id: str) -> str:
        return asyncio.run(self.capture_screenshot(target_id))
