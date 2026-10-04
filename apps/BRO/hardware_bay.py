"""BRO Hardware Bay prototype.

Purpose:
- Give each attached controller a human-readable board identity.
- Show a per-pin assignment/readout table inside BRO.
- Establish the UI/data boundary for future live ESP32 node discovery and telemetry.

This first pass is intentionally host-side only. It does NOT reconfigure GPIOs, flash boards,
or send motor/power commands. Demo board records are placeholders until the BRO-NODE
serial protocol is implemented.
"""
import tkinter as tk
from tkinter import ttk


DEMO_BOARDS = {
    "DRIVE-A · ESP32-S3": {
        "status": "prototype / not connected",
        "firmware": "BRO-NODE draft",
        "supply": "--",
        "pins": [
            ("GPIO4", "PWM", "LEFT MOTOR", "0 %", "planned"),
            ("GPIO5", "PWM", "RIGHT MOTOR", "0 %", "planned"),
            ("GPIO6", "DIGITAL", "LEFT DIR", "LOW", "planned"),
            ("GPIO7", "DIGITAL", "RIGHT DIR", "LOW", "planned"),
            ("GPIO8", "ENCODER", "LEFT ENCODER A", "--", "planned"),
            ("GPIO9", "ENCODER", "LEFT ENCODER B", "--", "planned"),
            ("GPIO10", "ENCODER", "RIGHT ENCODER A", "--", "planned"),
            ("GPIO11", "ENCODER", "RIGHT ENCODER B", "--", "planned"),
            ("GPIO12", "ADC", "MOTOR CURRENT", "-- V", "planned"),
            ("GPIO13", "UNUSED", "UNASSIGNED", "--", "available"),
        ],
    },
    "SENSOR-A · ESP32-S3": {
        "status": "prototype / not connected",
        "firmware": "BRO-NODE draft",
        "supply": "--",
        "pins": [
            ("GPIO1", "I2C SDA", "IMU / SENSOR BUS", "--", "planned"),
            ("GPIO2", "I2C SCL", "IMU / SENSOR BUS", "--", "planned"),
            ("GPIO4", "DIGITAL", "BUMPER LEFT", "LOW", "planned"),
            ("GPIO5", "DIGITAL", "BUMPER RIGHT", "LOW", "planned"),
            ("GPIO6", "ADC", "SOLAR VOLTAGE", "-- V", "planned"),
            ("GPIO7", "ADC", "BATTERY VOLTAGE", "-- V", "planned"),
            ("GPIO8", "UART RX", "LIDAR", "--", "planned"),
            ("GPIO9", "UART TX", "LIDAR", "--", "planned"),
            ("GPIO10", "DIGITAL", "LIGHT SENSOR / AUX", "--", "available"),
            ("GPIO11", "UNUSED", "UNASSIGNED", "--", "available"),
        ],
    },
    "FACE-A · ESP32-S3": {
        "status": "prototype / not connected",
        "firmware": "BRO-NODE draft",
        "supply": "--",
        "pins": [
            ("GPIO1", "I2C SDA", "SERVICE OLED", "--", "planned"),
            ("GPIO2", "I2C SCL", "SERVICE OLED", "--", "planned"),
            ("GPIO4", "SPI", "COLOR TFT", "--", "planned"),
            ("GPIO5", "SPI", "COLOR TFT", "--", "planned"),
            ("GPIO6", "PWM", "FACE LIGHTS", "0 %", "planned"),
            ("GPIO7", "DIGITAL", "SOUND / AMP ENABLE", "LOW", "planned"),
            ("GPIO8", "ADC", "MIC LEVEL", "--", "planned"),
            ("GPIO9", "UNUSED", "UNASSIGNED", "--", "available"),
        ],
    },
}


class HardwareBay:
    """Read-only first-pass board/pin inspector for the BRO development sidebar."""

    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.LabelFrame(parent, text="Hardware Bay · prototype", padding=6)
        self.frame.pack(fill="x", pady=8)

        ttk.Label(
            self.frame,
            text="Board-aware pinout + telemetry workbench. Read-only until the BRO-NODE protocol is proven.",
            wraplength=290,
        ).pack(fill="x")

        top = ttk.Frame(self.frame)
        top.pack(fill="x", pady=(5, 3))
        self.board = tk.StringVar(value=next(iter(DEMO_BOARDS)))
        self.selector = ttk.Combobox(
            top,
            textvariable=self.board,
            values=tuple(DEMO_BOARDS),
            state="readonly",
            width=23,
        )
        self.selector.pack(side="left", fill="x", expand=True)
        self.selector.bind("<<ComboboxSelected>>", lambda _: self.show_board())
        ttk.Button(top, text="Rescan", command=self.rescan).pack(side="right", padx=(4, 0))

        self.identity = tk.StringVar()
        ttk.Label(self.frame, textvariable=self.identity, wraplength=290).pack(fill="x")

        columns = ("pin", "mode", "assignment", "readout", "state")
        self.table = ttk.Treeview(self.frame, columns=columns, show="headings", height=9)
        headings = {
            "pin": "Pin",
            "mode": "Mode",
            "assignment": "Assignment",
            "readout": "Live",
            "state": "State",
        }
        widths = {"pin": 52, "mode": 70, "assignment": 118, "readout": 62, "state": 70}
        for key in columns:
            self.table.heading(key, text=headings[key])
            self.table.column(key, width=widths[key], minwidth=42, stretch=(key == "assignment"))
        self.table.pack(fill="x", pady=4)

        controls = ttk.Frame(self.frame)
        controls.pack(fill="x")
        ttk.Button(controls, text="Copy pin map", command=self.copy_map).pack(side="left")
        ttk.Button(controls, text="Board details", command=self.copy_details).pack(side="right")

        ttk.Label(
            self.frame,
            text="Future: live node discovery · voltage/ADC · PWM duty/frequency · digital state · buses · faults · safe pin assignment",
            wraplength=290,
        ).pack(fill="x", pady=(4, 0))
        self.show_board()

    def current(self):
        return DEMO_BOARDS[self.board.get()]

    def show_board(self):
        record = self.current()
        self.identity.set(
            f"{self.board.get()}\nStatus: {record['status']} · FW: {record['firmware']} · supply: {record['supply']}"
        )
        for item in self.table.get_children():
            self.table.delete(item)
        for row in record["pins"]:
            self.table.insert("", "end", values=row)

    def rescan(self):
        # Placeholder on purpose: no board probing is performed until identity/handshake is defined.
        self.show_board()
        self.app.log("Hardware Bay rescan: demo inventory only; BRO-NODE discovery not implemented")

    def pin_map_text(self):
        record = self.current()
        lines = [self.board.get(), f"status={record['status']} firmware={record['firmware']} supply={record['supply']}"]
        lines += [f"{pin:>6} | {mode:<9} | {assignment:<22} | {readout:<8} | {state}" for pin, mode, assignment, readout, state in record["pins"]]
        return "\n".join(lines)

    def copy_map(self):
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(self.pin_map_text())
        self.app.log("Hardware Bay pin map copied: " + self.board.get())

    def copy_details(self):
        text = (
            self.pin_map_text()
            + "\n\nBRO-NODE draft goals:\n"
            + "IDENTITY · CAPABILITIES · GET PINMAP · GET TELEMETRY · SAFE ASSIGNMENT · FAULT REPORT"
        )
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(text)
        self.app.log("Hardware Bay board details copied: " + self.board.get())
