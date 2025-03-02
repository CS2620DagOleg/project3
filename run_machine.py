import sys
from machine import VirtualMachine

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_machine.py <machine_id>")
        sys.exit(1)
    machine_id = sys.argv[1]
    vm = VirtualMachine(machine_id)
    try:
        vm.run()
    except KeyboardInterrupt:
        print("Machine shutting down.")

if __name__ == "__main__":
    main()
