import ctypes
import os
import sys
import json
import base64
import shutil
import subprocess
from datetime import datetime, timedelta
from colorama import init, Fore, Style

# Force UTF-8 console encoding on Windows for emoji support
if sys.platform == "win32":
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    sys.stdout.reconfigure(encoding="utf-8")

init(autoreset=True)

WORK_HOUR_OPTIONS = {
    "winter": {"name": "Winter", "duration": timedelta(hours=7, minutes=15)},
    "summer": {"name": "Summer", "duration": timedelta(hours=5, minutes=15)},
    "ramadan": {"name": "Ramadan", "duration": timedelta(hours=4, minutes=15)},
}

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "work_timer_config.json")


def format_duration(duration):
    total_minutes = int(duration.total_seconds() // 60)
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours} hours {minutes} minutes"


def format_time(dt):
    return dt.strftime("%I:%M %p").lstrip("0")


def load_locked_schedule():
    if not os.path.exists(CONFIG_FILE):
        return None

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

    schedule_key = data.get("schedule")
    if schedule_key in WORK_HOUR_OPTIONS:
        return schedule_key
    return None


def save_locked_schedule(schedule_key):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump({"schedule": schedule_key}, file, ensure_ascii=False, indent=2)


def get_leave_datetime(arrival_time, base_work_duration):
    now = datetime.now()
    arrival_today = datetime.combine(now.date(), arrival_time.time())
    leave_datetime = arrival_today + base_work_duration
    return leave_datetime


def is_wsl():
    if sys.platform != "linux":
        return False

    if os.environ.get("WSL_DISTRO_NAME"):
        return True

    try:
        with open("/proc/version", "r", encoding="utf-8") as file:
            return "microsoft" in file.read().lower()
    except OSError:
        return False


def find_powershell_executable():
    if sys.platform == "win32":
        candidates = ["powershell", "pwsh"]
    elif is_wsl():
        candidates = [
            "powershell.exe",
            "pwsh.exe",
            "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
            "/mnt/c/Program Files/PowerShell/7/pwsh.exe",
        ]
    else:
        candidates = ["pwsh", "powershell"]

    for candidate in candidates:
        resolved_path = shutil.which(candidate)
        if resolved_path:
            return resolved_path
        if os.path.isabs(candidate) and os.path.exists(candidate):
            return candidate

    return None


def schedule_popup_reminder(leave_datetime, schedule_name):
    powershell_executable = find_powershell_executable()
    if not powershell_executable:
        if is_wsl():
            return False, "PowerShell executable not found in WSL."
        return False, "PowerShell executable not found."

    target_str = leave_datetime.strftime("%Y-%m-%d %H:%M")
    title = "Work Timer Reminder"
    message = f"Time to leave work ({schedule_name})."
    script = f"""
$target = [datetime]::ParseExact('{target_str}', 'yyyy-MM-dd HH:mm', $null)
$seconds = [int][math]::Ceiling(($target - (Get-Date)).TotalSeconds)
if ($seconds -gt 0) {{
    Start-Sleep -Seconds $seconds
}}
[console]::Beep(1200, 500)
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show(
    '{message}',
    '{title}',
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
) | Out-Null
"""
    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")

    popen_kwargs = {
        "args": [powershell_executable, "-NoProfile", "-WindowStyle", "Hidden", "-EncodedCommand", encoded_script],
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }

    if sys.platform == "win32":
        # Use CREATE_NEW_PROCESS_GROUP only — DETACHED_PROCESS prevents GUI popups
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

    try:
        subprocess.Popen(**popen_kwargs)
        return True, None
    except OSError as ex:
        return False, str(ex)


def parse_arrival_time(arrival_str):
    formats_to_try = ["%I:%M %p", "%I:%M%p", "%H:%M", "%I %p"]

    for fmt in formats_to_try:
        try:
            parsed = datetime.strptime(arrival_str, fmt)
            return parsed
        except ValueError:
            continue

    return None


def select_locked_schedule():
    existing_schedule = load_locked_schedule()

    if existing_schedule:
        option = WORK_HOUR_OPTIONS[existing_schedule]
        print(f"{Fore.GREEN}🔒 Locked mode: {option['name']} ({format_duration(option['duration'])})")
        print(f"{Fore.CYAN}Press Enter to keep it, or type C then Enter to change: ", end="")
        change_choice = input(f"{Style.RESET_ALL}").strip().lower()

        if change_choice != "c":
            return option

    print(f"\n{Fore.CYAN}Choose your working hours mode:")
    print(f"{Fore.WHITE}1) Winter  - 7 hours 15 minutes")
    print(f"{Fore.WHITE}2) Summer  - 5 hours 15 minutes")
    print(f"{Fore.WHITE}3) Ramadan - 4 hours 15 minutes")

    option_map = {"1": "winter", "2": "summer", "3": "ramadan"}
    while True:
        print(f"{Fore.YELLOW}Enter option number (1-3): ", end="")
        selected = input(f"{Style.RESET_ALL}").strip()

        if selected in option_map:
            schedule_key = option_map[selected]
            save_locked_schedule(schedule_key)
            option = WORK_HOUR_OPTIONS[schedule_key]
            print(f"{Fore.GREEN}✅ Saved and locked: {option['name']} ({format_duration(option['duration'])})")
            return option

        print(f"{Fore.RED}{Style.BRIGHT}❌ Invalid choice. Please enter 1, 2, or 3.")


def display_leave_times(arrival_time, leave_datetime, schedule_name):
    print("\n" + f"{Fore.WHITE}" + "─" * 50)
    print(f"{Fore.WHITE}🏃 Arrival Time:          {Fore.WHITE}{Style.BRIGHT}{format_time(arrival_time)}")
    print(f"{Fore.GREEN}{Style.BRIGHT}🏠 {schedule_name.upper()} LEAVING TIME: {format_time(leave_datetime)}")
    print(f"{Fore.WHITE}" + "─" * 50)

    print(f"{Fore.CYAN}👇 If you take an excuse (leave early):")

    excuses = [
        (30, "30 mins"),
        (60, "1 hour"),
        (90, "1 hour 30 mins"),
        (120, "2 hours"),
        (150, "2 hours 30 mins"),
    ]

    max_len = max(len(label) for _, label in excuses)

    for minutes_subtracted, label in excuses:
        early_leave_time = leave_datetime - timedelta(minutes=minutes_subtracted)
        print(f"{Fore.MAGENTA}   🎟️  With {label:<{max_len}} excuse  ➜  {Fore.YELLOW}{Style.BRIGHT}{format_time(early_leave_time)}")

    print(f"{Fore.WHITE}" + "─" * 50)


def prompt_popup_reminder(leave_datetime, schedule_name):
    print(f"{Fore.CYAN}🔔 Set a popup reminder at leave time? (Y/n): ", end="")
    popup_choice = input(f"{Style.RESET_ALL}").strip().lower()

    if popup_choice == "n":
        return

    popup_set, popup_error = schedule_popup_reminder(leave_datetime, schedule_name)
    if popup_set:
        time_str = format_time(leave_datetime)
        date_str = leave_datetime.strftime("%Y-%m-%d")
        print(f"{Fore.GREEN}✅ Popup reminder scheduled for {date_str} {time_str}.")
    else:
        print(f"{Fore.YELLOW}⚠️ Could not schedule popup reminder.")
        if popup_error:
            print(f"{Fore.LIGHTBLACK_EX}   Details: {popup_error}")


def calculate_leave_time():
    print(f"\n{Fore.CYAN}{Style.BRIGHT}╔════════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}{Style.BRIGHT}║   FLEXIBLE WORK HOURS CALCULATOR (LEAVE EARLY)     ║")
    print(f"{Fore.CYAN}{Style.BRIGHT}╠════════════════════════════════════════════════════╣")
    print(f"{Fore.CYAN}{Style.BRIGHT}║          Eng. Ahmed Saleh                          ║")
    print(f"{Fore.CYAN}{Style.BRIGHT}║    Planetarium Center - AAST, Abu Qir              ║")
    print(f"{Fore.CYAN}{Style.BRIGHT}╚════════════════════════════════════════════════════╝")

    selected_option = select_locked_schedule()
    base_work_duration = selected_option["duration"]
    schedule_name = selected_option["name"]
    print(f"{Fore.CYAN}ℹ️  Active Shift ({schedule_name}): {format_duration(base_work_duration)}")

    while True:
        print(f"\n{Fore.YELLOW}🕐 Enter your arrival time (e.g., 8:30): ", end="")
        arrival_str = input(f"{Style.RESET_ALL}").strip()

        arrival_time = parse_arrival_time(arrival_str)

        if not arrival_time:
            print(f"{Fore.RED}{Style.BRIGHT}❌ Error: Invalid format. Please try again (e.g., 8:30).")
            continue

        leave_datetime = get_leave_datetime(arrival_time, base_work_duration)
        now = datetime.now()

        if leave_datetime <= now:
            today_str = now.strftime("%Y-%m-%d")
            tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"{Fore.YELLOW}⚠️ Calculated leave time already passed today ({today_str}).")
            print(f"{Fore.CYAN}Keep it on {today_str} (may alert immediately), or type T for {tomorrow_str}: ", end="")
            day_choice = input(f"{Style.RESET_ALL}").strip().lower()
            if day_choice == "t":
                leave_datetime += timedelta(days=1)

        display_leave_times(arrival_time, leave_datetime, schedule_name)
        prompt_popup_reminder(leave_datetime, schedule_name)
        break

    print(f"\n{Fore.LIGHTBLACK_EX}Press Enter to exit...", end="")
    input()


if __name__ == "__main__":
    calculate_leave_time()
