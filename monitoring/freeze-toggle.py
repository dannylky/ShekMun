#!/usr/bin/env python3
"""
freeze-toggle.py - tiny desktop toggle that sends the global Windows
hotkey Ctrl+Shift+Z on every button press.

The button label alternates between "Freeze" and "UnFreeze". Each press
sends Ctrl+Shift+Z to whatever window has focus, using the native
SendInput API (no third-party dependencies).

Usage:
  python freeze-toggle.py
"""

import ctypes
import ctypes.wintypes
import tkinter as tk

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_Z = 0x5A
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    _anonymous_ = ("i",)
    _fields_ = [("type", ctypes.wintypes.DWORD), ("i", _I)]


def send_ctrl_shift_z():
    """Press Ctrl+Shift+Z: ctrl down, shift down, z down, z up, shift up, ctrl up."""
    seq = [
        (VK_CONTROL, 0),
        (VK_SHIFT, 0),
        (VK_Z, 0),
        (VK_Z, KEYEVENTF_KEYUP),
        (VK_SHIFT, KEYEVENTF_KEYUP),
        (VK_CONTROL, KEYEVENTF_KEYUP),
    ]
    inputs = []
    for vk, flags in seq:
        entry = INPUT()
        entry.type = INPUT_KEYBOARD
        entry.ki.wVk = vk
        entry.ki.wScan = 0
        entry.ki.dwFlags = flags
        entry.ki.time = 0
        entry.ki.dwExtraInfo = None
        inputs.append(entry)
    ctypes.windll.user32.SendInput(
        len(inputs), (INPUT * len(inputs))(*inputs), ctypes.sizeof(INPUT)
    )


class FreezeToggleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Freeze Toggle")
        self.root.resizable(False, False)
        self.frozen = False

        self.button = tk.Button(
            root,
            text="Freeze",
            font=("Segoe UI", 14, "bold"),
            width=12,
            height=2,
            command=self.toggle,
        )
        self.button.pack(padx=16, pady=16)

    def toggle(self):
        self.frozen = not self.frozen
        self.button.config(text="UnFreeze" if self.frozen else "Freeze")
        send_ctrl_shift_z()


def main():
    root = tk.Tk()
    FreezeToggleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()