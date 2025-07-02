import threading
import time
import random

class Node(threading.Thread):
    def __init__(self, node_id, num_nodes, message_loss_percentage, is_alive):
        threading.Thread.__init__(self)
        self.node_id = node_id
        self.num_nodes = num_nodes
        self.message_loss_percentage = message_loss_percentage
        self.is_alive = is_alive

        # State variables for the algorithm
        self.requesting_cs = False
        self.in_cs = False
        self.clock = 0
        self.request_timestamp = 0  # CRITICAL FIX: Stores the timestamp of this node's request
        self.outstanding_replies = 0
        self.deferred_replies = []
        self.nodes = []
        self.lock = threading.Lock() # CRITICAL FIX: Ensures thread safety for each node

    def set_nodes(self, nodes):
        self.nodes = nodes

    def receive_request(self, requester_id, timestamp):
        if not self.is_alive:
            return

        with self.lock:
            print(f"Node {self.node_id}: Received REQUEST from Node {requester_id} with timestamp {timestamp}")
            self.clock = max(self.clock, timestamp) + 1

            # The core logic of the Ricart-Agrawala algorithm
            # Defer if we are in CS, or if we are requesting and have a higher priority
            # (lower timestamp, or same timestamp with lower ID).
            if self.in_cs or \
               (self.requesting_cs and \
               (self.request_timestamp < timestamp or (self.request_timestamp == timestamp and self.node_id < requester_id))):
                print(f"Node {self.node_id}: Deferring REPLY to Node {requester_id} (My Prio: ({self.request_timestamp}, {self.node_id}) vs Theirs: ({timestamp}, {requester_id}))")
                self.deferred_replies.append(requester_id)
            else:
                self.send_reply(requester_id)

    def send_reply(self, destination_id):
        # This function doesn't need a lock because it only reads its own ID
        # and calls a method on another node (which will acquire its own lock).
        if not self.is_alive or random.randint(0, 99) < self.message_loss_percentage:
            print(f"Node {self.node_id}: Simulating message loss of REPLY to Node {destination_id}")
            return

        print(f"Node {self.node_id}: Sending REPLY to Node {destination_id}")
        self.nodes[destination_id].receive_reply(self.node_id)

    def receive_reply(self, sender_id):
        if not self.is_alive or not self.requesting_cs:
            return

        with self.lock:
            print(f"Node {self.node_id}: Received REPLY from Node {sender_id}")
            self.outstanding_replies -= 1

    def request_critical_section(self):
        if not self.is_alive:
            return

        with self.lock:
            self.requesting_cs = True
            self.clock += 1
            self.request_timestamp = self.clock # CRITICAL FIX: Save the timestamp of this request
            self.outstanding_replies = self.num_nodes - 1

        print(f"Node {self.node_id}: Requesting Critical Section with timestamp {self.request_timestamp}")

        for i in range(self.num_nodes):
            if i != self.node_id:
                # Simulate potential message loss
                if random.randint(0, 99) >= self.message_loss_percentage:
                    self.nodes[i].receive_request(self.node_id, self.request_timestamp)
                else:
                    print(f"Node {self.node_id}: Simulating message loss of REQUEST to Node {i}")

    def run(self):
        # Nodes start at random times to increase contention
        time.sleep(random.uniform(0, 1))
        if not self.is_alive: return

        self.request_critical_section()

        # Wait until all replies are received
        while self.is_alive:
            with self.lock:
                if self.outstanding_replies == 0:
                    break
            time.sleep(0.05)

        if self.is_alive:
            # --- ENTER CRITICAL SECTION ---
            with self.lock:
                self.in_cs = True
            print(f"\n✅✅✅ Node {self.node_id} entered Critical Section ✅✅✅\n")
            time.sleep(random.uniform(1, 2)) # Simulate work
            print(f"\n❌❌❌ Node {self.node_id} exiting Critical Section ❌❌❌\n")
            # --- EXIT CRITICAL SECTION ---

            with self.lock:
                self.in_cs = False
                self.requesting_cs = False
                # Reply to all deferred requests
                for requester_id in self.deferred_replies:
                    self.send_reply(requester_id)
                self.deferred_replies = []

def main():
    # --- Simulation Parameters ---
    NUM_NODES = 5
    # Needs to be 0.9
    MESSAGE_LOSS_PERCENTAGE = 0
    NODE_STATUS = [True] * NUM_NODES
    # ---------------------------

    nodes = [Node(i, NUM_NODES, MESSAGE_LOSS_PERCENTAGE, NODE_STATUS[i]) for i in range(NUM_NODES)]
    for node in nodes:
        node.set_nodes(nodes)

    threads = []
    print("Starting all node threads to run concurrently...")
    for i in range(NUM_NODES):
        if nodes[i].is_alive:
            thread = nodes[i]
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()

    print("\nSimulation finished.")

if __name__ == "__main__":
    main()