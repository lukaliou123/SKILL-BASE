"""
miniHexa BLE control entry.
Supports:
  - 14 built-in action groups
  - movement control (forward/back/left/right/turn/stop)
  - real-time distance notification via BLE notify
  - auto-stop on obstacle detection
Source: https://github.com/lukaliou123/SKILL-BASE (2026-03-17)
"""

import asyncio
import json
import os
import re
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "miniHexa"
RX_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # write
TX_UUID = "0000ffe2-0000-1000-8000-00805f9b34fb"  # notify

SCRIPT_DIR = os.path.dirname(__file__)
MAP_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "references", "actions_map.json"))
LEGACY_MAP_FILE = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "actions_map.json"))

# Auto-stop threshold (mm)
OBSTACLE_THRESHOLD_MM = 200


class BLERobot:
    def __init__(self, obstacle_threshold: int = OBSTACLE_THRESHOLD_MM):
        map_file = MAP_FILE if os.path.exists(MAP_FILE) else LEGACY_MAP_FILE
        with open(map_file, encoding="utf-8") as f:
            self._map = json.load(f)
        self._client: BleakClient | None = None
        self._address: str | None = None
        self._distance_mm: int = 9999
        self._battery_mv: int = 0
        self._obstacle_threshold = obstacle_threshold
        self._on_obstacle = None  # callback: async fn(dist_mm)
        self._moving = False

    async def connect(self, timeout: float = 10.0):
        print("[BLE] scanning...")
        devices = await BleakScanner.discover(timeout=8.0)
        target = next((d for d in devices if d.name == DEVICE_NAME), None)
        if not target:
            raise RuntimeError("miniHexa BLE device not found")
        self._address = target.address
        self._client = BleakClient(target.address, timeout=timeout)
        await self._client.connect()
        await self._client.start_notify(TX_UUID, self._on_notify)
        print(f"[BLE] connected {DEVICE_NAME} @ {target.address}")

    async def disconnect(self):
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        print("[BLE] disconnected")

    def _on_notify(self, _handle, data: bytearray):
        """Receive payload in format: $battery$distance$"""
        text = data.decode(errors="ignore")
        m = re.search(r"\$(\d+)\$(\d+)\$", text)
        if m:
            self._battery_mv = int(m.group(1))
            self._distance_mm = int(m.group(2))
            if self._moving and self._distance_mm < self._obstacle_threshold:
                asyncio.ensure_future(self._handle_obstacle())

    async def _handle_obstacle(self):
        self._moving = False
        await self._send(b"C|0|0|0&")
        msg = f"[BLE] obstacle detected ({self._distance_mm}mm), stopped."
        print(msg)
        if self._on_obstacle:
            await self._on_obstacle(self._distance_mm)

    async def _send(self, cmd: bytes):
        if not self._client or not self._client.is_connected:
            raise RuntimeError("BLE not connected")
        # response=True required on macOS (FFE1 char property is 'write', not 'write-without-response')
        await self._client.write_gatt_char(RX_UUID, cmd, response=True)

    async def play(self, name: str):
        """Trigger action group by action name."""
        actions = self._map["actions"]
        if name not in actions:
            print(f"[BLE] unknown action: {name}")
            return
        aid = actions[name]["id"]
        cmd = f"K|1|{aid}&".encode()
        await self._send(cmd)
        print(f"[BLE] action: {name} (K|1|{aid}&)")

    async def move(self, direction: str, duration_s: float = 0):
        """
        Send movement command.
        If duration_s > 0, auto-stop after duration.
        """
        movements = self._map["movement"]
        if direction not in movements:
            print(f"[BLE] unknown direction: {direction}")
            return
        cmd = movements[direction]["cmd"].encode()
        self._moving = direction not in ("停止", "复位")
        await self._send(cmd)
        print(f"[BLE] move: {direction} ({movements[direction]['cmd']})")
        if duration_s > 0 and self._moving:
            await asyncio.sleep(duration_s)
            await self.stop()

    async def stop(self):
        self._moving = False
        await self._send(b"C|0|0|0&")
        print("[BLE] stop")

    @property
    def distance_mm(self) -> int:
        return self._distance_mm

    @property
    def battery_mv(self) -> int:
        return self._battery_mv

    def set_obstacle_callback(self, coro):
        self._on_obstacle = coro

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *_):
        await self.disconnect()


async def cli():
    async with BLERobot() as robot:
        print("\nactions:", list(robot._map["actions"].keys()))
        print("moves:", list(robot._map["movement"].keys()))
        print("input action/move, q to quit\n")

        while True:
            s = input("cmd> ").strip()
            if s.lower() in {"q", "quit"}:
                break
            if s in robot._map["actions"]:
                await robot.play(s)
            elif s in robot._map["movement"]:
                await robot.move(s)
            else:
                print("unknown command")


if __name__ == "__main__":
    asyncio.run(cli())
