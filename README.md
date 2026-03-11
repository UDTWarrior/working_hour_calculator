# Flexible Work Hours Calculator

A command-line tool that calculates your leave time based on your arrival time and work shift schedule. It also shows adjusted leave times for early excuses and can set a popup reminder on Windows.

**By Eng. Ahmed Saleh — Planetarium Center, AAST, Abu Qir**

## Features

- **Three shift modes**: Winter (7h 15m), Summer (5h 15m), Ramadan (4h 15m)
- **Locked schedule**: Your selected shift is saved and remembered across sessions
- **Early excuse calculator**: Shows adjusted leave times for 30 min to 2.5 hour excuses
- **Popup reminder**: Schedules a Windows popup with a beep at your leave time
- **Cross-platform support**: Works on Windows, WSL, and Linux

## Usage

### Run from source

```bash
pip install -r requirements.txt
python work_timer.py
```

### Build a standalone `.exe`

```bash
pip install -r requirements.txt
pyinstaller --onefile --console work_timer.py
```

The executable will be in the `dist/` folder.

### Run the `.exe`

Just double-click `work_timer.exe`. A `work_timer_config.json` file will be created next to it to store your shift preference.

## Example Output

```
╔════════════════════════════════════════════════════╗
║   FLEXIBLE WORK HOURS CALCULATOR (LEAVE EARLY)     ║
╠════════════════════════════════════════════════════╣
║          Eng. Ahmed Saleh                          ║
║    Planetarium Center - AAST, Abu Qir              ║
╚════════════════════════════════════════════════════╝
🔒 Locked mode: Ramadan (4 hours 15 minutes)

🕐 Enter your arrival time (e.g., 8:30): 8:30

──────────────────────────────────────────────────
🏃 Arrival Time:          8:30 AM
🏠 RAMADAN LEAVING TIME:  12:45 PM
──────────────────────────────────────────────────
👇 If you take an excuse (leave early):
   🎟️  With 30 mins          excuse  ➜  12:15 PM
   🎟️  With 1 hour           excuse  ➜  11:45 AM
   🎟️  With 1 hour 30 mins   excuse  ➜  11:15 AM
   🎟️  With 2 hours          excuse  ➜  10:45 AM
   🎟️  With 2 hours 30 mins  excuse  ➜  10:15 AM
──────────────────────────────────────────────────
🔔 Set a popup reminder at leave time? (Y/n):
```

## Accepted Time Formats

| Format         | Example  |
|----------------|----------|
| `HH:MM`        | `8:30`   |
| `HH:MM AM/PM`  | `8:30 AM`|
| `HH:MMAM/PM`   | `8:30AM` |
| `HH AM/PM`     | `8 AM`   |

## Requirements

- Python 3.8+
- `colorama` (for colored terminal output)
- PowerShell (for popup reminders — available by default on Windows)
