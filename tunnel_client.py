#!/usr/bin/env python3
"""
Simple TCP Tunnel Client for Debian/Ubuntu - Display Only Mode
Connects to Render tunnel server and shows connection status (no input allowed)
Usage: python3 tunnel_client.py --server SERVER --token TOKEN --local-port PORT
"""

import socket
import threading
import time
import sys
import argparse
import os

def log(message, force_newline=False):
    """Timestamped logging - in display mode, just show info"""
    timestamp = time.strftime('%H:%M:%S')
    if force_newline:
        print(f"[{timestamp}] {message}")
    else:
        # In display mode, we might overwrite or just append
        print(f"[{timestamp}] {message}")

class TunnelClientDisplay:
    def __init__(self, server_host, server_port, auth_token, local_host='127.0.0.1', local_port=None):
        self.server_host = server_host
        self.server_port = int(server_port)
        self.auth_token = auth_token.strip()
        self.local_host = local_host
        self.local_port = int(local_port) if local_port else None
        self.running = False
        self.tunnel_socket = None
        self.local_socket = None
        self.reconnect_delay = 5
        self.bytes_transferred = {'client_to_local': 0, 'local_to_client': 0}
        self.tunnel_established = False
        self.connection_time = None

    def start(self):
        """Start the tunnel client in display-only mode"""
        if not self.validate_inputs():
            return False

        self.show_banner()
        self.running = True
        self.connection_loop()
        return True

    def show_banner(self):
        """Show initial banner"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=" * 60)
        print("           TCP TUNNEL CLIENT - DISPLAY MODE")
        print("=" * 60)
        print(f"Server: {self.server_host}:{self.server_port}")
        print(f"Local Target: {self.local_host}:{self.local_port}")
        print(f"Status: Connecting...")
        print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        print("NOTE: This is display-only mode. No command input accepted.")
        print("      Tunnel status updates will appear below.")
        print("=" * 60)

    def validate_inputs(self):
        """Validate input parameters"""
        if not all([self.server_host, self.auth_token, self.local_port]):
            self.log_error("Error: server, token, and local-port are required")
            return False
        if len(self.auth_token) < 10:
            self.log_error("Error: Invalid token format")
            return False
        return True

    def log_error(self, message):
        """Log error message"""
        print(f"[{time.strftime('%H:%M:%S')}] ERROR: {message}")

    def log_info(self, message):
        """Log info message"""
        print(f"[{time.strftime('%H:%M:%S')}] INFO: {message}")

    def log_success(self, message):
        """Log success message"""
        print(f"[{time.strftime('%H:%M:%S')}] SUCCESS: {message}")

    def connection_loop(self):
        """Main connection loop with auto-reconnect"""
        while self.running:
            try:
                self.log_info(f"Connecting to tunnel server {self.server_host}:{self.server_port}...")
                self.tunnel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.tunnel_socket.settimeout(10)
                self.tunnel_socket.connect((self.server_host, self.server_port))
                self.tunnel_socket.settimeout(None)

                self.log_success("Connected to tunnel server")
                self.handle_tunnel_session()

            except Exception as e:
                self.log_error(f"Connection failed: {e}")
                if self.running:
                    self.log_info(f"Retrying in {self.reconnect_delay}s...")
                    # Show reconnect countdown without breaking display
                    for i in range(self.reconnect_delay, 0, -1):
                        if not self.running:
                            break
                        sys.stdout.write(f"\rReconnecting in {i}s... ")
                        sys.stdout.flush()
                        time.sleep(1)
                    sys.stdout.write("\r" + " " * 20 + "\r")  # Clear line
                    sys.stdout.flush()
            finally:
                self.cleanup_resources()
                # Small delay before retry to avoid spamming
                if self.running:
                    time.sleep(1)

    def handle_tunnel_session(self):
        """Handle the tunnel session"""
        try:
            # 1. Send auth token
            self.log_info("Sending authentication token...")
            self.tunnel_socket.send((self.auth_token + '\n').encode())

            # 2. Wait for auth response
            response = self._receive_line()
            if not response:
                self.log_error("No auth response received")
                return

            self.log_info(f"Auth response: {response.strip()}")

            if not response.startswith("TUNNEL_READY"):
                self.log_error("Authentication failed - invalid token")
                return

            # 3. Send local target specification
            target = f"{self.local_host}:{self.local_port}"
            self.log_info(f"Specifying target service: {target}")
            self.tunnel_socket.send((target + '\n').encode())

            # 4. Wait for tunnel confirmation
            response = self._receive_line()
            if not response:
                self.log_error("No tunnel confirmation received")
                return

            self.log_info(f"Tunnel response: {response.strip()}")

            if not response.startswith("TUNNEL"):
                self.log_error("Tunnel establishment failed")
                return

            # Extract tunnel ID if present
            parts = response.split()
            tunnel_id = parts[1] if len(parts) > 1 else "unknown"
            self.tunnel_established = True
            self.connection_time = time.time()

            self.show_connection_established(tunnel_id)

            # 5. Connect to local service and start forwarding
            self.connect_and_forward_display()

        except Exception as e:
            self.log_error(f"Session error: {e}")
        finally:
            self.cleanup_resources()

    def _receive_line(self):
        """Receive a line of data from socket"""
        try:
            data = b""
            while self.running:
                chunk = self.tunnel_socket.recv(1)
                if not chunk:
                    break
                data += chunk
                if chunk == b'\n':
                    break
            return data.decode('utf-8', errors='ignore')
        except:
            return None

    def show_connection_established(self, tunnel_id):
        """Show that connection is established and switch to display-only"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=" * 60)
        print("           TCP TUNNEL CLIENT - ACTIVE TUNNEL")
        print("=" * 60)
        print(f"Tunnel ID:     {tunnel_id}")
        print(f"Server:        {self.server_host}:{self.server_port}")
        print(f"Local Target:  {self.local_host}:{self.local_port}")
        print(f"Status:        🟢 ACTIVE")
        print(f"Connected:     {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.connection_time))}")
        print("-" * 60)
        print("TRAFFIC STATISTICS (updated every 5 seconds):")
        print("=" * 60)

    def connect_and_forward_display(self):
        """Connect to local service and start forwarding with display updates"""
        try:
            # Connect to local service
            self.log_info(f"Connecting to local service {self.local_host}:{self.local_port}...")
            self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.local_socket.settimeout(10)
            self.local_socket.connect((self.local_host, self.local_port))
            self.local_socket.settimeout(None)
            self.log_success("Connected to local service")

            # Start bidirectional forwarding with periodic display updates
            def forward_and_update(source, destination, direction, bytes_counter):
                try:
                    last_update = time.time()
                    while self.running:
                        data = source.recv(4096)
                        if not data:
                            break
                        destination.send(data)
                        bytes_counter[0] += len(data)

                        # Update display every 5 seconds
                        now = time.time()
                        if now - last_update >= 5:
                            self.update_display()
                            last_update = now

                except Exception as e:
                    if self.running:
                        self.log_error(f"Forward error ({direction}): {e}")
                finally:
                    pass

            # Byte counters
            server_to_local = [0]
            local_to_server = [0]

            # Start forwarding threads
            t1 = threading.Thread(target=forward_and_update, args=(self.tunnel_socket, self.local_socket, "server→local", server_to_local), daemon=True)
            t2 = threading.Thread(target=forward_and_update, args=(self.local_socket, self.tunnel_socket, "local→server", local_to_server), daemon=True)

            t1.start()
            t2.start()

            # Main display update loop
            self.display_update_loop()

            # Wait for forwarding threads
            t1.join()
            t2.join()

        except Exception as e:
            self.log_error(f"Failed to connect to local service: {e}")

    def display_update_loop(self):
        """Main loop for updating the display"""
        last_update = time.time()
        update_interval = 5  # seconds

        while self.running and self.tunnel_established:
            try:
                now = time.time()
                if now - last_update >= update_interval:
                    self.update_display()
                    last_update = now
                time.sleep(0.1)  # Small sleep to prevent CPU hogging
            except Exception as e:
                if self.running:
                    self.log_error(f"Display update error: {e}")
                break

    def update_display(self):
        """Update the traffic statistics display"""
        try:
            # Calculate elapsed time
            elapsed = int(time.time() - self.connection_time) if self.connection_time else 0
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            time_str = f"{hours:02d}:{hours:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"

            # Clear and redisplay stats area (lines after the header)
            # We'll use a simple approach: clear lines and reprint
            sys.stdout.write("\033[7;0f")  # Move to line 7, column 0 (after header)
            sys.stdout.write("\033[J")      # Clear from cursor to end of screen

            print(f"Connection Time: {time_str}")
            print(f"Server → Local:  {self.format_bytes(self.bytes_transferred['client_to_local'])}")
            print(f"Local → Server:  {self.format_bytes(self.bytes_transferred['local_to_client'])}")
            print(f"Current Rate:    Calculating...")  # Simplified for now
            print("-" * 60)
            print("STATUS: 🟢 TUNNEL ACTIVE - PRESS CTRL+C TO STOP")
            print("=" * 60)
            sys.stdout.flush()
        except:
            pass  # Ignore display errors to keep tunnel running

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

    def cleanup_resources(self):
        """Cleanup connections"""
        try:
            if self.local_socket:
                self.local_socket.close()
                self.local_socket = None
        except:
            pass
        try:
            if self.tunnel_socket:
                self.tunnel_socket.close()
                self.tunnel_socket = None
        except:
            pass

    def show_disconnected(self):
        """Show disconnected state"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("=" * 60)
        print("           TCP TUNNEL CLIENT - DISCONNECTED")
        print("=" * 60)
        print(f"Server: {self.server_host}:{self.server_port}")
        print(f"Local:  {self.local_host}:{self.local_port}")
        print(f"Status: 🔴 DISCONNECTED")
        print(f"Time:   {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print("Attempting to reconnect...")
        print("=" * 60)

    def stop(self):
        """Stop the client"""
        self.log_info("Shutdown signal received...")
        self.running = False
        self.cleanup_resources()

def main():
    parser = argparse.ArgumentParser(description='TCP Tunnel Client - Display Only Mode')
    parser.add_argument('--server', required=True, help='Tunnel server hostname (e.g., service.onrender.com)')
    parser.add_argument('--token', required=True, help='Authentication token from server logs')
    parser.add_argument('--local-port', type=int, required=True, help='Local service port to expose')
    parser.add_argument('--local-host', default='127.0.0.1', help='Local service host (default: 127.0.0.1)')
    parser.add_argument('--server-port', type=int, default=4444, help='Tunnel server port (default: 4444)')

    args = parser.parse_args()

    client = TunnelClientDisplay(
        server_host=args.server,
        server_port=args.server_port,
        auth_token=args.token,
        local_host=args.local_host,
        local_port=args.local_port
    )

    try:
        if client.start():
            # Main loop - just wait for interrupt
            while client.running:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n")  # New line for clean exit
        client.show_disconnected()
        time.sleep(1)  # Show disconnected state briefly
    finally:
        client.stop()

if __name__ == "__main__":
    main()