import subprocess
import time

scripts = ["12randomwords.py", "script_name.py", "hack.py"]

while True:
    print("⏳ Starting new hourly run...")
    for script in scripts:
        print(f"▶ Running {script}...")
        subprocess.run(["python3", script], check=True)

    print("✅ Finished one round. Waiting 1 hour...")
    time.sleep(3600)  # wait 3600 seconds = 1 hour
