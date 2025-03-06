import socket
import threading
import queue
import time
import random
import json
import os
from datetime import datetime

def update_logical_clock_on_receive(local_clock, message_clock):
    ''' 
    :param local_clock: The current logical clock value of this machine.
    :param message_clock: The logical clock value received from another machine.
    :return: The updated logical clock value.
    '''
    return max(local_clock, message_clock) + 1

class VirtualMachine:
    def __init__(self, machine_id, config_path="config.json", connect_peers=True):
        ''' 
        :param machine_id: Unique identifier for this machine.
        :param config_path: Path to the configuration JSON file.
        :param connect_peers: Flag indicating whether to connect to peer machines immediately.
        '''
        self.machine_id = str(machine_id)
        self.config = self.load_config(config_path)
        self.host = self.config["machines"][self.machine_id]["host"]
        self.port = self.config["machines"][self.machine_id]["port"]
        
        # Build a dictionary of peer machines (all except this machine)
        self.peers = {mid: info for mid, info in self.config["machines"].items() if mid != self.machine_id}
        
        # Set a random clock rate between 1 and 6 ticks per second.
        self.clock_rate = random.randint(1, 6)
        self.logical_clock = 0  # Initialize the logical clock to 0
        self.msg_queue = queue.Queue()  # Queue to store incoming message clock values
        
        # Set up logging: Each machine writes events to its own log file.
        self.log_file_path = f"log_{self.machine_id}.txt"
        with open(self.log_file_path, "a") as f:
            f.write(f"Machine {self.machine_id} log started at {datetime.now()}\n")
            f.write(f"Clock rate: {self.clock_rate} ticks per second\n")
        
        self.running = True  # Control flag for the main loop
        
        # Start the server thread to handle incoming connections
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        
        # Dictionary to hold sockets for communication with peers
        self.peer_sockets = {}
        if connect_peers:
            self.connect_to_peers()

    def load_config(self, config_path):
        '''
        :param config_path: Path to the configuration file.
        :return: A dictionary containing configuration settings.
        '''
        with open(config_path, "r") as f:
            return json.load(f)

    def run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        # Set a timeout to periodically check if the server should continue running.
        self.server_socket.settimeout(1.0)
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
            except socket.timeout:
                continue  # No incoming connection; check again
            # Start a new thread to handle the incoming connection
            client_thread = threading.Thread(target=self.handle_client, args=(conn,), daemon=True)
            client_thread.start()

    def handle_client(self, conn):
        ''' 
        :param conn: The socket connection from a peer.
        '''
        with conn:
            file_obj = conn.makefile("r")
            for line in file_obj:
                line = line.strip()
                if line.startswith("clock:"):
                    try:
                        message_clock = int(line.split("clock:")[1])
                        self.msg_queue.put(message_clock)
                    except ValueError:
                        # If the conversion fails, ignore this line.
                        continue

    def connect_to_peers(self):
        for peer_id, info in self.peers.items():
            connected = False
            while not connected and self.running:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((info["host"], info["port"]))
                    self.peer_sockets[peer_id] = s
                    connected = True
                except ConnectionRefusedError:
                    s.close()  # Close socket to avoid resource leak
                    time.sleep(1)

    def send_message(self, peer_id):
        ''' 
        :param peer_id: Identifier of the peer machine to send the message to.
        '''
        if peer_id in self.peer_sockets:
            self.logical_clock += 1  # Increment the logical clock before sending
            message = f"clock:{self.logical_clock}\n"
            try:
                self.peer_sockets[peer_id].sendall(message.encode())
                self.log_event("SEND", f"Sent to machine {peer_id}")
            except Exception as e:
                self.log_event("ERROR", f"Failed to send to machine {peer_id}: {e}")
        else:
            self.log_event("ERROR", f"No connection to machine {peer_id}")

    def log_event(self, event_type, details):
        '''  
        :param event_type: A string representing the type of event (e.g., SEND, RECEIVE, INTERNAL, ERROR).
        :param details: A descriptive message with event-specific details.
        '''
        system_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{system_time} | {event_type} | Clock: {self.logical_clock} | {details}\n"
        with open(self.log_file_path, "a") as f:
            f.write(log_entry)
        print(f"Machine {self.machine_id}: {log_entry.strip()}")

    def process_message_queue(self):
        if not self.msg_queue.empty():
            message_clock = self.msg_queue.get()
            self.logical_clock = update_logical_clock_on_receive(self.logical_clock, message_clock)
            queue_length = self.msg_queue.qsize()
            self.log_event("RECEIVE", f"Message clock: {message_clock}, Queue length: {queue_length}")
            return True
        return False

    def run(self):
        while self.running:
            start_time = time.time()
            processed = self.process_message_queue()
            if not processed:
                event_choice = random.randint(1, 10)
                if event_choice == 1:
                    # Send a message to the first peer (alphabetically sorted)
                    peer_id = sorted(self.peers.keys())[0]
                    self.send_message(peer_id)
                elif event_choice == 2:
                    # If a second peer exists, send a message to it; otherwise, send to the first peer
                    if len(self.peers) > 1:
                        peer_id = sorted(self.peers.keys())[1]
                        self.send_message(peer_id)
                    else:
                        peer_id = sorted(self.peers.keys())[0]
                        self.send_message(peer_id)
                elif event_choice == 3:
                    # Send a message to all peers
                    for peer_id in sorted(self.peers.keys()):
                        self.send_message(peer_id)
                else:
                    # Perform an internal event: simply increment the logical clock
                    self.logical_clock += 1
                    self.log_event("INTERNAL", "Internal event")
            # Maintain the clock rate by sleeping for the remainder of the tick duration
            elapsed = time.time() - start_time
            tick_duration = 1.0 / self.clock_rate
            if elapsed < tick_duration:
                time.sleep(tick_duration - elapsed)

    def shutdown(self):
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
