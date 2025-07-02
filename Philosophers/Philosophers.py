import threading
import random
import time
import socket
import json
from collections import defaultdict

class Philosopher(threading.Thread):
    def __init__(self, id, host, port, neighbors):
        threading.Thread.__init__(self)
        self.id = id
        self.host = host
        self.port = port
        self.neighbors = neighbors  # {left: (host, port), right: (host, port)}
        self.state = "thinking"
        self.left_fork = False
        self.right_fork = False
        self.message_queue = []
        self.lock = threading.Lock()
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(2)
        
    def run(self):
        # Start listening for messages
        listener = threading.Thread(target=self.listen_for_messages)
        listener.start()
        
        while self.running:
            if self.state == "thinking":
                # Random thinking time
                time.sleep(random.uniform(1, 3))
                self.state = "hungry"
                print(f"Philosopher {self.id} is now hungry")
                
            elif self.state == "hungry":
                self.request_forks()
                
            elif self.state == "eating":
                # Eating time
                time.sleep(random.uniform(1, 2))
                self.release_forks()
                self.state = "thinking"
                print(f"Philosopher {self.id} finished eating and is now thinking")
    
    def listen_for_messages(self):
        while self.running:
            try:
                client_socket, _ = self.server_socket.accept()
                data = client_socket.recv(1024).decode()
                if data:
                    message = json.loads(data)
                    self.handle_message(message)
                client_socket.close()
            except:
                continue
    
    def handle_message(self, message):
        with self.lock:
            self.message_queue.append(message)
            msg_type = message["type"]
            
            if msg_type == "request":
                fork_id = message["fork"]
                requester = message["from"]
                
                # Only respond if we're not using the fork
                if fork_id == "left" and not self.right_fork:
                    self.send_message(requester, {"type": "response", "fork": "right"})
                elif fork_id == "right" and not self.left_fork:
                    self.send_message(requester, {"type": "response", "fork": "left"})
            
            elif msg_type == "response":
                fork = message["fork"]
                if fork == "left":
                    self.left_fork = True
                else:
                    self.right_fork = True
                
                if self.left_fork and self.right_fork:
                    self.state = "eating"
                    print(f"Philosopher {self.id} is now EATING")
    
    def request_forks(self):
        # Request left fork from left neighbor
        self.send_message(self.neighbors["left"], {
            "type": "request",
            "fork": "right",  # my left is their right
            "from": (self.host, self.port)
        })
        
        # Request right fork from right neighbor
        self.send_message(self.neighbors["right"], {
            "type": "request",
            "fork": "left",  # my right is their left
            "from": (self.host, self.port)
        })
    
    def release_forks(self):
        # Release forks by sending messages to neighbors
        self.send_message(self.neighbors["left"], {
            "type": "release",
            "fork": "right"
        })
        
        self.send_message(self.neighbors["right"], {
            "type": "release",
            "fork": "left"
        })
        
        self.left_fork = False
        self.right_fork = False
    
    def send_message(self, neighbor, message):
        host, port = neighbor
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(json.dumps(message).encode())
        except:
            pass  # Simulate network unreliability
    
    def stop(self):
        self.running = False
        self.server_socket.close()

def dining_philosophers():
    # Configuration for 5 philosophers in a ring
    philosophers_config = [
        {"id": 0, "host": "localhost", "port": 5000, "left": ("localhost", 5004), "right": ("localhost", 5001)},
        {"id": 1, "host": "localhost", "port": 5001, "left": ("localhost", 5000), "right": ("localhost", 5002)},
        {"id": 2, "host": "localhost", "port": 5002, "left": ("localhost", 5001), "right": ("localhost", 5003)},
        {"id": 3, "host": "localhost", "port": 5003, "left": ("localhost", 5002), "right": ("localhost", 5004)},
        {"id": 4, "host": "localhost", "port": 5004, "left": ("localhost", 5003), "right": ("localhost", 5000)},
    ]
    
    # Create and start philosophers
    philosophers = []
    for config in philosophers_config:
        p = Philosopher(config["id"], config["host"], config["port"], 
                       {"left": config["left"], "right": config["right"]})
        philosophers.append(p)
        p.start()
    
    # Let them run for a while
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        for p in philosophers:
            p.stop()
            p.join()

if __name__ == "__main__":
    print("Starting Dining Philosophers Distributed Simulation...")
    dining_philosophers()