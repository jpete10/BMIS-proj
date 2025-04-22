import subprocess
import signal
import time
import os
import sys

PID_FILE = "athena.pid"


def start_ollama():
    print("[LAUNCHER] Starting Ollama server...")
    proc = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(1)
    return proc

def start_athena():
    print("[LAUNCHER] Starting Athena...")
    proc = subprocess.Popen(
        [sys.executable, "athena.py"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

    # Save PID to a file
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    return proc

def shutdown_process(proc, name):
    if proc and proc.poll() is None:
        print(f"[LAUNCHER] Shutting down {name}...")
        try:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
            proc.wait(timeout=5)
            print(f"[LAUNCHER] {name} stopped.")
        except Exception as e:
            print(f"[LAUNCHER] Failed to stop {name}: {e}")

def main():
    ollama_proc = start_ollama()
    athena_proc = start_athena()

    try:
        athena_proc.wait()
    except KeyboardInterrupt:
        print("\n[LAUNCHER] Keyboard interrupt received.")
    finally:
        shutdown_process(ollama_proc, "Ollama")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

if __name__ == "__main__":
    main()
