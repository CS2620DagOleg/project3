import socket
import threading
import queue
import time
import random
import json
import os
from datetime import datetime

def update_logical_clock_on_receive(local_clock, message_clock):
    """Update the local logical clock based on a received message clock."""
    return max(local_clock, message_clock) + 1

class VirtualMachine:
    def __init__(self, machine_id, config_path="config.json", connect_peers=True):
        self.machine_id = str(machine_id)
        self.config = self.load_config(config_path)
        self.host = self.config["machines"][self.machine_id]["host"]
        self.port = self.config["machines"][self.machine_id]["port"]
        # Determine peers by removing self from the configuration.
        self.peers = {mid: info for mid, info in self.config["machines"].items() if mid != self.machine_id}
        self.clock_rate = random.randint(1, 6)  # ticks per second
        self.logical_clock = 0
        self.msg_queue = queue.Queue()
        self.log_file_path = f"log_{self.machine_id}.txt"
        with open(self.log_file_path, "a") as f:
            f.write(f"Machine {self.machine_id} log started at {datetime.now()}\n")
            f.write(f"Clock rate: {self.clock_rate} ticks per second\n")
        self.running = True
        # Start the server thread.
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        # Dictionary to hold outgoing client sockets to peers.
        self.peer_sockets = {}
        if connect_peers:
            self.connect_to_peers()

    def load_config(self, config_path):
        with open(config_path, "r") as f:
            return json.load(f)

    def run_server(self):
        """Run the TCP server that listens for incoming messages."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
            except socket.timeout:
                continue
            client_thread = threading.Thread(target=self.handle_client, args=(conn,), daemon=True)
            client_thread.start()

    def handle_client(self, conn):
        """Handle an incoming connection and enqueue messages."""
        with conn:
            file_obj = conn.makefile("r")
            for line in file_obj:
                line = line.strip()
                if line.startswith("clock:"):
                    try:
                        message_clock = int(line.split("clock:")[1])
                        self.msg_queue.put(message_clock)
                    except ValueError:
                        continue

    def connect_to_peers(self):
        """Establish client connections to all peer machines."""
        for peer_id, info in self.peers.items():
            connected = False
            while not connected and self.running:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((info["host"], info["port"]))
                    self.peer_sockets[peer_id] = s
                    connected = True
                except ConnectionRefusedError:
                    s.close()  # Close socket on failure to avoid resource warnings.
                    time.sleep(1)

    def send_message(self, peer_id):
        """Send a message (the current logical clock) to the specified peer."""
        if peer_id in self.peer_sockets:
            # Increment the clock before sending according to Lamport's rules.
            self.logical_clock += 1
            message = f"clock:{self.logical_clock}\n"
            try:
                self.peer_sockets[peer_id].sendall(message.encode())
                self.log_event("SEND", f"Sent to machine {peer_id}")
            except Exception as e:
                self.log_event("ERROR", f"Failed to send to machine {peer_id}: {e}")
        else:
            self.log_event("ERROR", f"No connection to machine {peer_id}")

    def log_event(self, event_type, details):
        """Log an event with system time, current logical clock, and event details."""
        system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{system_time} | {event_type} | Clock: {self.logical_clock} | {details}\n"
        with open(self.log_file_path, "a") as f:
            f.write(log_entry)
        print(f"Machine {self.machine_id}: {log_entry.strip()}")

    def process_message_queue(self):
        """Process one message from the message queue if available."""
        if not self.msg_queue.empty():
            message_clock = self.msg_queue.get()
            self.logical_clock = update_logical_clock_on_receive(self.logical_clock, message_clock)
            queue_length = self.msg_queue.qsize()
            self.log_event("RECEIVE", f"Message clock: {message_clock}, Queue length: {queue_length}")
            return True
        return False

    def run(self):
        """Main loop for processing clock cycles and events."""
        while self.running:
            start_time = time.time()
            processed = self.process_message_queue()
            if not processed:
                event_choice = random.randint(1, 10)
                if event_choice == 1:
                    peer_id = sorted(self.peers.keys())[0]
                    self.send_message(peer_id)
                elif event_choice == 2:
                    if len(self.peers) > 1:
                        peer_id = sorted(self.peers.keys())[1]
                        self.send_message(peer_id)
                    else:
                        peer_id = sorted(self.peers.keys())[0]
                        self.send_message(peer_id)
                elif event_choice == 3:
                    for peer_id in sorted(self.peers.keys()):
                        self.send_message(peer_id)
                else:
                    self.logical_clock += 1
                    self.log_event("INTERNAL", "Internal event")
            elapsed = time.time() - start_time
            tick_duration = 1.0 / self.clock_rate
            if elapsed < tick_duration:
                time.sleep(tick_duration - elapsed)

    def shutdown(self):
        """Cleanly shutdown the machine, closing all sockets."""
        self.running = False
        try:
            self.server_socket.close()
        except Exception:
            pass
        for sock in self.peer_sockets.values():
            try:
                sock.close()
            except Exception:
                pass
