import sys
import os
import time

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from avalongame.communications import SharedMemoryComm

def run_client(player_name):
    # 1. Initialize library
    comm = SharedMemoryComm()
    
    print(f"[{player_name}] Phase 1: Handshake. Writing to registry...")
    
    # 2. TEST CONNECTION: 
    # This writes the name to 'avalon_registry' and waits for the server 
    # to create 'shm_tos_Alice' and 'shm_sto_Alice'.
    if not comm.connect_as_client(player_name):
        print(f"[{player_name}] Error: Handshake failed. Is the server running?")
        return

    print(f"[{player_name}] Handshake Complete. Persistent handles established.")

    # 3. TEST IMMEDIATE RECEIVE (Server-to-Client)
    # The server sends a Welcome message immediately upon handshake.
    print(f"[{player_name}] Waiting for Server Welcome...")
    welcome_received = False
    for _ in range(20):  # Poll for ~2 seconds
        incoming = comm.recv("Server")
        if incoming:
            print(f"[{player_name}] Received Welcome: {incoming[2]}")
            welcome_received = True
            break
        time.sleep(0.1)
    
    if not welcome_received:
        print(f"[{player_name}] Warning: Never received initial Welcome.")

    # 4. TEST SEND (Client-to-Server)
    greeting = f"Hello from {player_name}!"
    print(f"[{player_name}] Sending greeting: '{greeting}'")
    comm.send(greeting, "Server")

    # 5. TEST ACKNOWLEDGEMENT (Server-to-Client)
    # The server should reply specifically to our greeting.
    print(f"[{player_name}] Waiting for Server Acknowledgement...")
    ack_received = False
    for _ in range(50):  # Poll for ~5 seconds
        reply = comm.recv("Server")
        if reply:
            print(f"[{player_name}] Received Acknowledgement: {reply[2]}")
            ack_received = True
            break
        time.sleep(0.1)

    if not ack_received:
        print(f"[{player_name}] Error: Server did not acknowledge greeting.")

    # 6. TEST SHUTDOWN TRIGGER
    # Sending 'quit' will make the test_server.py exit its loop.
    print(f"[{player_name}] Sending 'quit' to terminate test...")
    time.sleep(1)
    comm.send("quit", "Server")
    print(f"[{player_name}] Client test complete.")

if __name__ == "__main__":
    # Usage: python test_client.py Alice
    name = sys.argv[1] if len(sys.argv) > 1 else "Alice"
    run_client(name)
