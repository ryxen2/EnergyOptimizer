import subprocess
import ctypes
import os

# Check if running as admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Set Windows Power Plan to Power Saver
def set_power_saver():
    saver_guid = "a1841308-3541-4fab-bc81-f71556f20b4a"
    subprocess.run(["powercfg", "/setactive", saver_guid])
    print("[+] Power plan set to Power Saver")

# Lower maximum CPU frequency
def set_cpu_max_freq(percent=50):
    # percent = maximum CPU frequency (0-100)
    subprocess.run(["powercfg", "/setacvalueindex", "scheme_current",
                    "54533251-82be-4824-96c1-47b60b740d00",
                    "bc5038f7-23e0-4960-96da-33abaf5935ec", str(percent)])
    subprocess.run(["powercfg", "/setdcvalueindex", "scheme_current",
                    "54533251-82be-4824-96c1-47b60b740d00",
                    "bc5038f7-23e0-4960-96da-33abaf5935ec", str(percent)])
    subprocess.run(["powercfg", "/setactive", "scheme_current"])
    print(f"[+] CPU max frequency set to {percent}%")

# Dim display brightness (0-100)
def set_brightness(level=30):
    try:
        subprocess.run(f"powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})", shell=True)
        print(f"[+] Screen brightness set to {level}%")
    except:
        print("[-] Could not change brightness (maybe admin needed)")

# Disable unnecessary background apps (example: Windows Search, Superfetch)
def disable_services():
    services = ["SysMain", "WSearch"]
    for service in services:
        subprocess.run(["sc", "stop", service], stdout=subprocess.DEVNULL)
        subprocess.run(["sc", "config", service, "start= disabled"], stdout=subprocess.DEVNULL)
    print("[+] Disabled unnecessary services")

if __name__ == "__main__":
    if not is_admin():
        print("Please run this script as Administrator!")
        exit()

    set_power_saver()
    set_cpu_max_freq(40)  # Lower CPU max to 40%
    set_brightness(30)
    disable_services()

    print("\n Deep Eco Mode applied!")
