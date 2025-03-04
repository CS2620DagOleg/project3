import subprocess
import time

# List of machine IDs to start
machines = ["1", "2", "3"]


processes = []
for machine_id in machines:
    p = subprocess.Popen(["python", "run_machine.py", machine_id])
    processes.append(p)
    time.sleep(0.5)  # Small delay to avoid race conditions

try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down all machines...")
    for p in processes:
        p.terminate()
