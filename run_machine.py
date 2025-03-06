import sys
from machine import VirtualMachine

def main():
    # Check if the required command-line argument (machine_id) is provided.
    if len(sys.argv) < 2:
        print("Usage: python run_machine.py <machine_id>")
        sys.exit(1)
    
    # Extract machine ID from the command-line arguments.
    machine_id = sys.argv[1]
    
    # Create a VirtualMachine instance using the provided machine ID.
    vm = VirtualMachine(machine_id)
    
    try:
        # Run the main event loop of the virtual machine.
        vm.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C interruption and shutdown the machine gracefully.
        print("Machine shutting down.")

# When the script is executed directly, call the main function.
if __name__ == "__main__":
    main()
