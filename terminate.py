import os
import subprocess

PID_FILE = "athena.pid"

def stop_athena():
    if not os.path.exists(PID_FILE):
        print("Athena is not running (no PID file found).")
        return

    with open(PID_FILE, "r") as f:
        pid = f.read().strip()

    print(f"Stopping Athena (PID {pid})...")

    try:
        # Use taskkill to forcibly and cleanly terminate the process and its children
        subprocess.call(["taskkill", "/PID", pid, "/T", "/F"])
        print("Athena shutdown signal sent.")
        os.remove(PID_FILE)
    except Exception as e:
        print(f"Failed to stop Athena: {e}")

if __name__ == "__main__":
    stop_athena()
