
import unittest
import os
import time
import threading
import json
import socket

from datetime import datetime
from machine import VirtualMachine, update_logical_clock_on_receive

class TestLogicalClockFunction(unittest.TestCase):
    """Test the standalone function to ensure it follows Lamport's update rule."""

    def test_update_logical_clock_on_receive(self):
        # If local_clock < message_clock
        new_clock = update_logical_clock_on_receive(local_clock=5, message_clock=10)
        self.assertEqual(
            new_clock, 11,
            
        )

        # If local_clock > message_clock
        new_clock = update_logical_clock_on_receive(local_clock=12, message_clock=10)
        self.assertEqual(
            new_clock, 13,
            
        )

        # If local_clock == message_clock
        new_clock = update_logical_clock_on_receive(local_clock=10, message_clock=10)
        self.assertEqual(
            new_clock, 11,
            
        )


class TestSingleMachine(unittest.TestCase):
    
    def setUp(self):
       
        self.test_config = {
            "machines": {
                "1": {"host": "127.0.0.1", "port": 6001}
            }
        }
        self.config_path = "test_config_single.json"
        with open(self.config_path, "w") as f:
            json.dump(self.test_config, f)

    def tearDown(self):
       
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        log_file = "log_1.txt"
        if os.path.exists(log_file):
            os.remove(log_file)

    def test_start_and_shutdown(self):
        # connect_peers=False means we have no indefinite loops trying to connect
        vm = VirtualMachine(machine_id="1", config_path=self.config_path, connect_peers=False)

        
        t = threading.Thread(target=vm.run)
        t.start()

        
        time.sleep(2)

      
        vm.shutdown()
        t.join(timeout=5)

        
        self.assertTrue(os.path.exists(vm.log_file_path), "Log file should exist after running.")
        with open(vm.log_file_path, "r") as f:
            logs = f.read()

        self.assertIn("Machine 1 log started", logs,
                      "Log file should start with a header indicating the machine started.")
        self.assertIn("INTERNAL", logs,
                      "A single machine with no peers should log at least one INTERNAL event.")


class TestMultipleMachines(unittest.TestCase):
  

    def setUp(self):
        # Create a config describing three machines
        self.test_config = {
            "machines": {
                "1": {"host": "127.0.0.1", "port": 6001},
                "2": {"host": "127.0.0.1", "port": 6002},
                "3": {"host": "127.0.0.1", "port": 6003}
            }
        }
        self.config_path = "test_config_multi.json"
        with open(self.config_path, "w") as f:
            json.dump(self.test_config, f)

       
        self.vm1 = VirtualMachine(machine_id="1", config_path=self.config_path, connect_peers=False)
        self.vm2 = VirtualMachine(machine_id="2", config_path=self.config_path, connect_peers=False)
        self.vm3 = VirtualMachine(machine_id="3", config_path=self.config_path, connect_peers=False)

      
        self.t1 = threading.Thread(target=self.vm1.run)
        self.t2 = threading.Thread(target=self.vm2.run)
        self.t3 = threading.Thread(target=self.vm3.run)

        self.t1.start()
        self.t2.start()
        self.t3.start()

    
        time.sleep(1)

        
        self.vm1.connect_to_peers()
        self.vm2.connect_to_peers()
        self.vm3.connect_to_peers()

        # Wait a bit, not much just a little 
        time.sleep(1)

    def tearDown(self):
        # Shut down all machines
        self.vm1.shutdown()
        self.vm2.shutdown()
        self.vm3.shutdown()


        self.t1.join(timeout=5)
        self.t2.join(timeout=5)
        self.t3.join(timeout=5)

        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        for m_id in ["1", "2", "3"]:
            log_file = f"log_{m_id}.txt"
            if os.path.exists(log_file):
                os.remove(log_file)

    def test_machines_can_connect_and_send(self):
        self.vm1.send_message("2")

        time.sleep(1)

        while not self.vm2.msg_queue.empty():
            self.vm2.process_message_queue()

        with open(self.vm2.log_file_path, "r") as f:
            logs_2 = f.read()
        self.assertIn("RECEIVE", logs_2,
                      "Machine 2 should have a RECEIVE event logged after Machine 1 sends a message.")

        with open(self.vm1.log_file_path, "r") as f:
            logs_1 = f.read()
        self.assertIn("SEND", logs_1,
                      "Machine 1 should have a SEND event logged after sending a message.")

if __name__ == "__main__":
    unittest.main()

