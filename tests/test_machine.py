import unittest
import tempfile
import os
import io
import socket
import threading
import time
from machine import VirtualMachine, update_logical_clock_on_receive

# A fake socket class to capture sent messages and track closure.
class FakeSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False
    def sendall(self, data):
        self.sent_messages.append(data)
    def close(self):
        self.closed = True

# Updated FakeConnection that supports the context manager protocol.
class FakeConnection:
    def __init__(self, message_str):
        self.file = io.StringIO(message_str)
    def makefile(self, mode):
        return self.file
    def close(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

class TestLogicalClock(unittest.TestCase):
    def test_update_logical_clock_on_receive(self):
        # When the local clock is greater than the message clock.
        self.assertEqual(update_logical_clock_on_receive(5, 3), 6)
        # When the message clock is greater than the local clock.
        self.assertEqual(update_logical_clock_on_receive(2, 7), 8)
        # When both clocks are equal.
        self.assertEqual(update_logical_clock_on_receive(4, 4), 5)

class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file.
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        config_content = (
            '{"machines": {'
            '"1": {"host": "127.0.0.1", "port": 5001}, '
            '"2": {"host": "127.0.0.1", "port": 5002}'
            '}}'
        )
        self.temp_config.write(config_content)
        self.temp_config.close()
        # Disable peer connections for testing.
        self.vm = VirtualMachine("1", config_path=self.temp_config.name, connect_peers=False)
    def tearDown(self):
        self.vm.shutdown()
        os.unlink(self.temp_config.name)
    def test_load_config(self):
        self.assertIn("machines", self.vm.config)
        self.assertIn("1", self.vm.config["machines"])

class TestLogEvent(unittest.TestCase):
    def setUp(self):
        # Create a temporary log file.
        self.temp_log = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt')
        self.temp_log.close()
        # Create a temporary config file.
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        config_content = (
            '{"machines": {'
            '"1": {"host": "127.0.0.1", "port": 5001}, '
            '"2": {"host": "127.0.0.1", "port": 5002}'
            '}}'
        )
        self.temp_config.write(config_content)
        self.temp_config.close()
        self.vm = VirtualMachine("1", config_path=self.temp_config.name, connect_peers=False)
        self.vm.log_file_path = self.temp_log.name  # Override the log file path.
    def tearDown(self):
        self.vm.shutdown()
        os.unlink(self.temp_log.name)
        os.unlink(self.temp_config.name)
    def test_log_event(self):
        self.vm.logical_clock = 10
        self.vm.log_event("TEST", "Testing log_event")
        with open(self.temp_log.name, 'r') as f:
            contents = f.read()
        self.assertIn("TEST", contents)
        self.assertIn("Clock: 10", contents)

class TestProcessMessageQueue(unittest.TestCase):
    def setUp(self):
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        config_content = (
            '{"machines": {'
            '"1": {"host": "127.0.0.1", "port": 5001}, '
            '"2": {"host": "127.0.0.1", "port": 5002}'
            '}}'
        )
        self.temp_config.write(config_content)
        self.temp_config.close()
        self.vm = VirtualMachine("1", config_path=self.temp_config.name, connect_peers=False)
    def tearDown(self):
        self.vm.shutdown()
        os.unlink(self.temp_config.name)
    def test_process_message_queue(self):
        initial_clock = self.vm.logical_clock
        # Enqueue a message with a clock value higher than the current clock.
        self.vm.msg_queue.put(initial_clock + 5)
        processed = self.vm.process_message_queue()
        self.assertTrue(processed)
        # The new clock should be max(initial, initial+5) + 1 = initial+6.
        self.assertEqual(self.vm.logical_clock, initial_clock + 6)

class TestSendMessage(unittest.TestCase):
    def setUp(self):
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        config_content = (
            '{"machines": {'
            '"1": {"host": "127.0.0.1", "port": 5001}, '
            '"2": {"host": "127.0.0.1", "port": 5002}'
            '}}'
        )
        self.temp_config.write(config_content)
        self.temp_config.close()
        self.vm = VirtualMachine("1", config_path=self.temp_config.name, connect_peers=False)
        # Override the peer socket with a fake socket.
        fake_socket = FakeSocket()
        self.vm.peer_sockets["2"] = fake_socket
        self.fake_socket = fake_socket
    def tearDown(self):
        self.vm.shutdown()
        os.unlink(self.temp_config.name)
    def test_send_message(self):
        self.vm.logical_clock = 20
        self.vm.send_message("2")
        # After sending, the logical clock should be incremented.
        self.assertEqual(self.vm.logical_clock, 21)
        # Verify the fake socket received the message.
        self.assertIn(b"clock:21\n", self.fake_socket.sent_messages)

class TestHandleClient(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file for a dummy VM instance.
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        config_content = (
            '{"machines": {'
            '"1": {"host": "127.0.0.1", "port": 5001}, '
            '"2": {"host": "127.0.0.1", "port": 5002}'
            '}}'
        )
        self.temp_config.write(config_content)
        self.temp_config.close()
        self.vm = VirtualMachine("1", config_path=self.temp_config.name, connect_peers=False)
    def tearDown(self):
        self.vm.shutdown()
        os.unlink(self.temp_config.name)
    def test_handle_client(self):
        fake_message = "clock:42\n"
        fake_conn = FakeConnection(fake_message)
        # Run handle_client in a separate thread to mimic threaded behavior.
        thread = threading.Thread(target=self.vm.handle_client, args=(fake_conn,))
        thread.start()
        thread.join(timeout=1)
        # Check that the message was enqueued.
        self.assertFalse(self.vm.msg_queue.empty())
        msg_clock = self.vm.msg_queue.get()
        self.assertEqual(msg_clock, 42)

class TestShutdown(unittest.TestCase):
    def setUp(self):
        self.temp_config = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
        config_content = (
            '{"machines": {'
            '"1": {"host": "127.0.0.1", "port": 5001}, '
            '"2": {"host": "127.0.0.1", "port": 5002}'
            '}}'
        )
        self.temp_config.write(config_content)
        self.temp_config.close()
        self.vm = VirtualMachine("1", config_path=self.temp_config.name, connect_peers=False)
        # Wait for the server thread to initialize server_socket.
        timeout = 1.0
        start_time = time.time()
        while not hasattr(self.vm, "server_socket") and time.time() - start_time < timeout:
            time.sleep(0.01)
    def tearDown(self):
        self.vm.shutdown()
        os.unlink(self.temp_config.name)
    def test_shutdown(self):
        # Set up a fake peer socket to check that close() is called.
        fake_socket = FakeSocket()
        self.vm.peer_sockets["2"] = fake_socket
        self.vm.shutdown()
        self.assertTrue(fake_socket.closed)
        # If server_socket exists, check that accept() fails.
        if hasattr(self.vm, "server_socket"):
            with self.assertRaises(OSError):
                self.vm.server_socket.accept()

if __name__ == "__main__":
    unittest.main()
