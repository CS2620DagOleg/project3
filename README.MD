# Distributed System Simulation

Our repo contains a simulation of a small, asynchronous distributed system with logical clocks.

## Overview

Each virtual machine:
- Runs on a randomly chosen clock rate between 1 and 6 ticks per second.
- Maintains a logical clock updated using Lamport’s algorithm.
- Listens on a TCP socket for incoming messages.
- Connects to every other machine (as defined in `config.json`) for sending messages.
- Logs every event (send, receive, or internal) to its own log file.

## File Structure

- **config.json:** Contains the configuration for each machine (host and port).
- **machine.py:** Implements the `VirtualMachine` class which encapsulates server/client communication, logical clock handling, and event processing.
- **run_machine.py:** Launches a virtual machine. Run it with a command-line argument for the machine ID.
- **tests/test_machine.py:** Unit tests (using `unittest`) for key functions such as the logical clock update.
- **lab_notebook.txt:** A lab notebook where design decisions and observations are recorded.

## How to Run

1. Ensure `config.json` is correctly set up (default uses three machines on localhost).
2. Open three terminal windows and start each machine:
   ```bash
   python run_machine.py 1
   python run_machine.py 2
   python run_machine.py 3

## Testing 

```bash
python -m unittest discover tests -v
