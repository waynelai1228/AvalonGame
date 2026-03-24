import sys
import os
import time

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from avalongame.communications import SharedMemoryComm

def run_server():
    # Initialize library
    comm = SharedMemoryComm()
    
    print("[Server] Phase 1: Handshake. Waiting for a client to register...")
    
    # 1. TEST CONNECTION: Blocks here until a client writes to the registry
    # We use a 60-second timeout to give you time to switch tmux panes.
    player_name = comm.handle_connections(timeout=60)

    if not player_name:
        print("[Server] Error: No client connected within timeout.")
        comm.cleanup()
        return

    print(f"[Server] Handshake Success: '{player_name}' is connected.")

    # 2. TEST IMMEDIATE SEND (Server-to-Client)
    # This tests the STO pipe immediately after handle_connections creates it.
    print(f"[Server] Sending welcome message to {player_name}...")
    comm.send(f"Welcome {player_name}! Connection verified.", player_name)

    print(f"[Server] Phase 2: Communication. Listening for messages...")

    try:
        active = True
        while active:
            # 3. TEST RECEIVE (Client-to-Server)
            incoming = comm.recv(player_name)
            
            if incoming:
                timestamp, sender, msg = incoming
                print(f"[Server] Received from {sender}: {msg}")
                
                # 4. TEST ACKNOWLEDGEMENT (Server-to-Client)
                reply = f"ACK: I received your message '{msg}'"
                print(f"[Server] Sending acknowledgment...")
                comm.send(reply, sender)
                
                # Exit logic
                if "quit" in msg.lower():
                    print(f"[Server] Shutting down per {sender}'s request.")
                    active = False
            
            # Small sleep to keep CPU usage low during polling
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[Server] Interrupted by user.")
    finally:
        # 5. TEST CLEANUP: Destroy all SHM regions
        print("[Server] Cleaning up shared memory...")
        comm.cleanup()

if __name__ == "__main__":
    run_server()
