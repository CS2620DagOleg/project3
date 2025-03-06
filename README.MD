# Distributed System Simulation

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [File Structure](#file-structure)
4. [How to Run](#how-to-run)
5. [Testing](#testing)
6. [Design Decisions and Considerations](#design-decisions-and-considerations)
7. [Conclusion](#conclusion)

## 1. Overview

This repository implements a simulation of an asynchronous distributed system that leverages logical clocks based on Lamport’s algorithm. The simulation models multiple virtual machines running concurrently on a single physical machine. Each virtual machine communicates with its peers over TCP sockets, processes events asynchronously, and logs every event with detailed timestamps and logical clock values.

## 2. Features

- **Random Clock Rate:**  
  Each virtual machine runs at a clock speed randomly chosen between 1 and 6 ticks per second.

- **Logical Clock Management:**  
  Utilizes Lamport’s logical clock algorithm to maintain and update event order without requiring a synchronized physical clock.

- **Asynchronous Communication:**  
  Virtual machines listen on dedicated TCP sockets for incoming messages and establish connections to peer machines as defined in the configuration.

- **Detailed Event Logging:**  
  Every event (internal, send, or receive) is logged with the system time, event type, current logical clock value, and event details.

- **Configurable Network Setup:**  
  The configuration for each machine (host and port) is specified in `config.json`, allowing for flexible setup.

## 3. File Structure

- **config.json:**  
  Contains the configuration for each machine (host and port details).

- **machine.py:**  
  Implements the `VirtualMachine` class that handles:
  - Server functionality (listening for incoming messages)
  - Client functionality (connecting to peers)
  - Logical clock management using Lamport’s algorithm
  - Event processing and logging

- **run_machine.py:**  
  A script to launch a single virtual machine. It takes the machine ID as a command-line argument and starts the machine.

- **start_all.py:**  
  A helper script to launch all virtual machines simultaneously, with a slight delay between startups to prevent race conditions.

- **tests/test_machine.py:**  
  Contains unit tests (using Python’s `unittest` framework) that verify:
  - Logical clock updates
  - Configuration loading
  - Event logging
  - Message processing (send and receive)
  - Proper shutdown and resource cleanup

## 4. How to Run

### Prerequisites

- **Python 3.12 or later:**  
  Ensure you have a compatible Python version installed.

- **No External Dependencies:**  
  The simulation uses built-in Python modules (socket, threading, etc.), so no additional packages are required.

### Running the Virtual Machines

1. **Configure the Machines:**  
   Verify that `config.json` is set up correctly. By default, it configures three machines on `localhost` with ports 5001, 5002, and 5003.

2. **Launch Individual Machines:**  
   Open separate terminal windows for each machine and run:
   ```bash
   python run_machine.py 1
   python run_machine.py 2
   python run_machine.py 3
   ```
   Each virtual machine will:
   - Listen for incoming messages.
   - Connect to its peers.
   - Log events to its respective log file (e.g., `log_1.txt`, `log_2.txt`, `log_3.txt`).

3. **Launch All Machines Simultaneously:**  
   Alternatively, you can start all machines at once using:
   ```bash
   python start_all.py
   ```
   This script launches each machine with a short delay between startups to avoid connection race conditions.

## 5. Testing

A comprehensive suite of unit tests is included to validate the functionality of the simulation. To run the tests in verbose mode, use:

```bash
pip install coverage
```

```bash
python -m coverage run -m unittest testrun.py
```
And finally to generate a coverage report run
```bash
python -m coverage report

```

These commands will run the test and generate a coverage report. We are standing at 89 percent coverage report currently. Despite the warnings, the final OK message confirms that the virtual machines successfully ran, exchanged messages, and updated their logical clocks correctly.

## 6. Design Decisions and Considerations

- **Logical Clock Synchronization:**  
  Lamport’s algorithm is used for its simplicity and effectiveness in ordering events without relying on a physical clock.

- **Asynchronous Event Processing:**  
  Using threads and non-blocking sockets, each virtual machine operates independently, reflecting real-world distributed systems.

- **Resource Management:**  
  Special attention is given to properly closing sockets during shutdown to prevent resource leaks. Unit tests are provided to ensure that resource cleanup is handled correctly.

- **Scalability:**  
  The system is designed to be scalable. To add more machines, update `config.json` with additional entries and launch extra instances using the provided scripts.

## 7. Conclusion

This distributed system simulation provides a practical platform for studying asynchronous processes and logical clock synchronization in a distributed environment. We experiment with different configurations and observe how events are ordered across virtual machines.
