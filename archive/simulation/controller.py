"""Real-time simulation controller (stub)."""

import json

class SimulationController:
    def __init__(self):
        self.sse_clients = []

    def add_sse_client(self, client_generator):
        """
        Add SSE client for real-time streaming.
        :param client_generator: Generator object for SSE client.
        """
        self.sse_clients.append(client_generator)

    def remove_sse_client(self, client_generator):
        """
        Remove SSE client.
        :param client_generator: Generator object for SSE client.
        """
        if client_generator in self.sse_clients:
            self.sse_clients.remove(client_generator)

    def send_sse_data(self, data):
        """
        Send data to all SSE clients.
        :param data: Data to send (dictionary).
        """
        json_data = json.dumps(data)
        for client in self.sse_clients.copy():
            try:
                client.send(f"data: {json_data}\n\n")
            except:
                # Remove disconnected clients
                self.sse_clients.remove(client)
