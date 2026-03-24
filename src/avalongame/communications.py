import time
from multiprocessing import shared_memory, resource_tracker

class SharedMemoryComm:
    """
    A Shared Memory communication library implementing a 'Registry' handshake.
    
    Assumptions:
    1. The Server is the lifecycle owner (creates/unlinks memory).
    2. Communication is bidirectional using two buffers per player: 
       TOS (To-Server) and STO (Server-To-Client).
    3. Message size is capped at 1024 bytes.
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.registry_name = "avalon_registry"
        # shm_handles: stores persistent SharedMemory objects.
        # Server stores a dict: {player_name: [tos_obj, sto_obj]}
        # Client stores a list: [tos_obj, sto_obj]
        self.shm_handles = {} 
        self.my_name = None

    def handle_connections(self, timeout=30):
        """
        SERVER ONLY: Monitors the registry for new client registration strings.
        
        Args:
            timeout (int): Seconds to poll before returning None.
            
        Returns:
            str: The name of the player who just connected.
            None: If the timeout is reached without any new connections.
        """
        start_time = time.time()
        
        # Ensure the public registry exists for clients to find
        try:
            reg_shm = shared_memory.SharedMemory(name=self.registry_name, create=True, size=256)
        except FileExistsError:
            reg_shm = shared_memory.SharedMemory(name=self.registry_name)

        try:
            while time.time() - start_time < timeout:
                # Read registry and strip null bytes/whitespace
                raw_name = bytes(reg_shm.buf[:]).decode('utf-8').strip('\x00').strip()
                
                if raw_name:
                    p_name = raw_name
                    
                    # Initialize dedicated 1KB buffers for this specific player
                    # TOS = To-Server | STO = Server-To-Client
                    tos = shared_memory.SharedMemory(name=f"shm_tos_{p_name}", create=True, size=1024)
                    sto = shared_memory.SharedMemory(name=f"shm_sto_{p_name}", create=True, size=1024)
                    
                    self.shm_handles[p_name] = [tos, sto]
                    
                    # Clear registry to allow the next client to register
                    reg_shm.buf[:reg_shm.size] = b'\x00' * reg_shm.size
                    return p_name 
                
                time.sleep(0.1) 
        finally:
            reg_shm.close() # Server keeps registry alive, only closes local handle
            
        return None

    def connect_as_client(self, name):
        """
        CLIENT ONLY: Registers name in registry and attaches to server-created buffers.
        
        Args:
            name (str): The unique identifier for this client.
            
        Returns:
            bool: True if handshake and attachment succeeded, False otherwise.
        """
        self.my_name = name
        try:
            # Step 1: Write name to the public registry
            reg_shm = shared_memory.SharedMemory(name=self.registry_name)
            # Prevent Python's resource_tracker from unlinking the server's registry on exit
            resource_tracker.unregister(reg_shm._name, "shared_memory")
            
            encoded_name = name.encode('utf-8')
            reg_shm.buf[:len(encoded_name)] = encoded_name
            reg_shm.close() 
            
            # Step 2: Poll for the server to initialize the private player buffers
            retries = 50
            while retries > 0:
                try:
                    tos = shared_memory.SharedMemory(name=f"shm_tos_{name}")
                    sto = shared_memory.SharedMemory(name=f"shm_sto_{name}")
                    
                    # Unregister to avoid 'leaked shared_memory' warnings on client shutdown
                    resource_tracker.unregister(tos._name, "shared_memory")
                    resource_tracker.unregister(sto._name, "shared_memory")
                    
                    self.shm_handles = [tos, sto]
                    return True
                except FileNotFoundError:
                    time.sleep(0.2)
                    retries -= 1
            
            return False
            
        except FileNotFoundError:
            # Registry doesn't exist; Server is likely offline
            return False

    def send(self, msg, target):
        """
        Writes a message to the target's incoming buffer.
        
        Args:
            msg (str): Content to send.
            target (str): Name of player, or "Server" if called by Client.
        """
        shm = None
        # Use handle mapping based on whether caller is Client (list) or Server (dict)
        if target == "Server" and isinstance(self.shm_handles, list):
            shm = self.shm_handles[0] 
        elif isinstance(self.shm_handles, dict) and target in self.shm_handles:
            shm = self.shm_handles[target][1]

        if shm:
            try:
                # Zero out buffer before writing to prevent artifacts from previous messages
                encoded = str(msg).encode('utf-8')
                shm.buf[:shm.size] = b'\x00' * shm.size
                shm.buf[:len(encoded)] = encoded
            except Exception as e:
                print(f"Send error: {e}")

    def recv(self, source):
        """
        Reads from a buffer and clears it immediately (Consumer pattern).
        
        Args:
            source (str): Name of player, or "Server" if called by Client.
            
        Returns:
            list: [timestamp (float), source (str), message (str)]
            None: If the buffer is empty.
        """
        shm = None
        if source == "Server" and isinstance(self.shm_handles, list):
            shm = self.shm_handles[1] 
        elif isinstance(self.shm_handles, dict) and source in self.shm_handles:
            shm = self.shm_handles[source][0]

        if shm:
            try:
                raw = bytes(shm.buf[:]).decode('utf-8').strip('\x00')
                if raw:
                    # Wipe buffer so the next recv call returns None until a new message arrives
                    shm.buf[:shm.size] = b'\x00' * shm.size
                    return [time.time(), source, raw]
            except Exception:
                pass
        return None

    def cleanup(self):
        """
        SERVER ONLY: Closes and unlinks all memory blocks created by the server.
        Should be called during graceful shutdown to avoid OS memory leaks.
        """
        if isinstance(self.shm_handles, dict):
            for p_name, handles in self.shm_handles.items():
                for h in handles:
                    try:
                        h.close()   # Close local access
                        h.unlink()  # Notify OS to destroy the segment
                    except Exception:
                        pass
            self.shm_handles = {}

        # Finally, destroy the registry block
        try:
            reg = shared_memory.SharedMemory(name=self.registry_name)
            reg.close()
            reg.unlink()
        except:
            pass
