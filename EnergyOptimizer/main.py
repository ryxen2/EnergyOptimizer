import psutil
import os
import time
import pandas as pd
import matplotlib.pyplot as plt

def get_system_snapshot():
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "running_processes": len(psutil.pids()),
        "battery_percent": psutil.sensors_battery().percent if psutil.sensors_battery() else None
    }

def suggest_optimizations(snapshot):
    suggestions = []

    if snapshot["cpu_usage"] > 70:
        suggestions.append("Close heavy CPU-consuming apps (e.g., Chrome, VS Code, etc.).")

    if snapshot["memory_usage"] > 80:
        suggestions.append("Free up RAM — close background tabs or restart memory-heavy apps.")

    if snapshot["running_processes"] > 200:
        suggestions.append("Too many processes running — consider disabling startup programs.")

    if snapshot["battery_percent"] and snapshot["battery_percent"] < 20:
        suggestions.append("Plug in your device or enable Battery Saver Mode.")

    
    try:
        import screen_brightness_control as sbc
        current_brightness = sbc.get_brightness(display=0)[0]
        if current_brightness > 70:
            sbc.set_brightness(50)
            suggestions.append("Brightness reduced from {}% to 50% to save power.".format(current_brightness))
    except Exception:
        suggestions.append("Brightness optimization not supported on this device.")

    if not suggestions:
        suggestions.append("System already optimized! Great job ")

    return suggestions

def run_energy_optimizer(duration=60):
    print(" Running energy optimization monitor...\n")
    logs = []
    start_time = time.time()

    while time.time() - start_time < duration:
        snapshot = get_system_snapshot()
        snapshot["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        snapshot["suggestions"] = "; ".join(suggest_optimizations(snapshot))
        logs.append(snapshot)
        print(f"[{snapshot['timestamp']}] CPU: {snapshot['cpu_usage']}%  MEMORY: {snapshot['memory_usage']}%  {snapshot['suggestions']}")
        time.sleep(10)

    df = pd.DataFrame(logs)
    df.to_csv("power_optimizer_log.csv", index=False)
    print("\n Optimization session completed. Log saved to power_optimizer_log.csv")
    return df

if __name__ == "__main__":
    data = run_energy_optimizer(duration=12000)  
