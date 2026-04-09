#!/usr/bin/env python3
"""
Simple TCP Tunnel Server for Render
Accepts connections from tunnel clients and forwards to local services
"""

import socket
import threading
import signal
import sys
import os
import time

# Simple in-memory token storage
VALID_TOKENS = set()

def load_tokens():
    """Load valid tokens from environment or generate default"""
    token_env = os.environ.get('TUNNEL_TOKEN')
    if token_env:
        VALID_TOKENS.add(token_env.strip())
        print(f"[SERVER] Loaded token from environment")
    else:
        # Generate a default token for first run - SHOW ONLY ONCE
        import secrets
        default_token = secrets.token_urlsafe(32)
        VALID_TOKENS.add(default_token)
        print("=" * 50)
        print("DEFAULT TUNNEL TOKEN (SAVE THIS):")
        print(f"{default_token}")
        print("=" * 50)
        print("[SERVER] Save the token above - you'll need it for your tunnel client")
        print("[SERVER] Set TUNNEL_TOKEN environment variable in Render for persistence")

def validate_token(token):
    """Validate authentication token"""
    return token.strip() in VALID_TOKENS

class TunnelServer:
    def __init__(self, host='0.0.0.0', port=None):
        self.host = host
        self.port = int(port) if port else int(os.environ.get('PORT', 4444))
        self.server_socket = None
        self.running = False
        self.active_tunnels = 0
        self.total_connections = 0

    def start(self):
        """Start the tunnel server"""
        load_tokens()

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"[SERVER] Tunnel server listening on {self.host}:{self.port}")
            print(f"[SERVER] Waiting for tunnel client connections...")
            print(f"[SERVER] Press Ctrl+C to stop")
            print("-" * 50)

            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    self.total_connections += 1
                    print(f"[SERVER] [{time.strftime('%H:%M:%S')}] Connection #{self.total_connections} from {address[0]}:{address[1]}")

                    # Handle each client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.error as e:
                    if self.running:
                        print(f"[SERVER] Socket error: {e}")
                    break

        except Exception as e:
            print(f"[SERVER] Failed to start server: {e}")
        finally:
            self.stop()

    def handle_client(self, client_socket, client_address):
        """Handle individual tunnel client connection"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        try:
            # 1. Receive and validate token
            token_data = client_socket.recv(1024).decode('utf-8').strip()
            if not token_data:
                client_socket.send(b"ERROR: No token provided\n")
                client_socket.close()
                print(f"[SERVER] [{client_id}] Rejected: No token")
                return

            token = token_data.split()[0] if ' ' in token_data else token_data

            if not validate_token(token):
                client_socket.send(b"ERROR: Invalid token\n")
                client_socket.close()
                print(f"[SERVER] [{client_id}] Rejected: Invalid token")
                return

            client_socket.send(b"READY: Waiting for target specification...\n")
            print(f"[SERVER] [{client_id}] Authenticated successfully")

            # 2. Receive target specification (host:port)
            target_data = client_socket.recv(1024).decode('utf-8').strip()
            if not target_data or ':' not in target_data:
                client_socket.send(b"ERROR: Invalid target format. Use host:port\n")
                client_socket.close()
                print(f"[SERVER] [{client_id}] Rejected: Invalid target format")
                return

            target_host, target_port_str = target_data.split(':', 1)
            try:
                target_port = int(target_port_str)
            except ValueError:
                client_socket.send(b"ERROR: Invalid port number\n")
                client_socket.close()
                print(f"[SERVER] [{client_id}] Rejected: Invalid port number")
                return

            # 3. Establish tunnel
            tunnel_id = self.total_connections  # Use connection count as tunnel ID for simplicity
            client_socket.send(f"TUNNEL {tunnel_id} ESTABLISHED -> {target_host}:{target_port}\n".encode())
            print(f"[SERVER] [{client_id}] Tunnel {tunnel_id} established: {target_host}:{target_port}")

            # 4. Forward traffic
            self.forward_traffic(client_socket, target_host, target_port, tunnel_id, client_id)

        except Exception as e:
            print(f"[SERVER] [{client_id}] Handler error: {e}")
            try:
                client_socket.send(b"ERROR: Internal server error\n")
            except:
                pass
        finally:
            try:
                client_socket.close()
            except:
                pass

    def forward_traffic(self, client_socket, target_host, target_port, tunnel_id, client_id):
        """Forward traffic between tunnel client and target service"""
        target_socket = None
        try:
            # Connect to target service
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(10)
            target_socket.connect((target_host, target_port))
            target_socket.settimeout(None)

            print(f"[SERVER] [{client_id}] Connected to target {target_host}:{target_port} for tunnel {tunnel_id}")

            # Bidirectional forwarding with byte counting
            def forward_data(source, destination, direction, bytes_counter):
                try:
                    while True:  # Run until connection breaks
                        data = source.recv(4096)
                        if not data:
                            break
                        destination.send(data)
                        bytes_counter[0] += len(data)
                except:
                    pass  # Connection closed or error
                finally:
                    pass

            client_to_target = [0]
            target_to_client = [0]

            t1 = threading.Thread(target=forward_data, args=(client_socket, target_socket, "client→target", client_to_target), daemon=True)
            t2 = threading.Thread(target=forward_data, args=(target_socket, client_socket, "target→client", target_to_client), daemon=True)

            t1.start()
            t2.start()

            t1.join()
            t2.join()

            print(f"[SERVER] [{client_id}] Tunnel {tunnel_id} closed:")
            print(f"[SERVER] [{client_id}]   Client→Target: {self.format_bytes(client_to_target[0])}")
            print(f"[SERVER] [{client_id}]   Target→Client: {self.format_bytes(target_to_client[0])}")

        except Exception as e:
            print(f"[SERVER] [{client_id}] Failed to connect to target {target_host}:{target_port}: {e}")
            try:
                client_socket.send(f"ERROR: Cannot connect to {target_host}:{target_port}\n".encode())
            except:
                pass
        finally:
            if target_socket:
                try:
                    target_socket.close()
                except:
                    pass

    def format_bytes(self, bytes_val):
        """Format bytes in human readable format"""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_val / (1024 * 1024 * 1024):.1f} GB"

    def stop(self):
        """Stop the tunnel server"""
        print(f"\n[SERVER] Shutting down tunnel server...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print(f"[SERVER] Tunnel server stopped")
        print(f"[SERVER] Total connections handled: {self.total_connections}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stop()
        sys.exit(0)

if __name__ == "__main__":
    server = TunnelServer()
    server.start()