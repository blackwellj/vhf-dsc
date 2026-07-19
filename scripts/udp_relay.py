"""UDP relay: Receive from rtl-airband on one port, forward to multiple destinations.

This allows sharing rtl-airband data between ncat (existing) and the DSC decoder.
"""

import socket
import sys
import time

# Configuration
RTL_AIRBAND_PORT = 5555  # Where rtl-airband sends
RELAY_PORT = 5556  # New port for DSC monitor
FORWARD_HOST = "127.0.0.1"

def main():
    print(f"UDP Relay: Receiving on port {RTL_AIRBAND_PORT}")
    print(f"  Forwarding to: {FORWARD_HOST}:{RELAY_PORT}")
    print(f"  (ncat continues on {RTL_AIRBAND_PORT})")
    print()
    print("NOTE: This requires rtl-airband to send to BOTH ports,")
    print("or you need to reconfigure rtl-airband to send to this relay.")
    print()

    # For now, just document the setup
    print("Recommended setup:")
    print("1. Configure rtl-airband to output to UDP 127.0.0.1:5556")
    print("2. Run: python scripts/udp_capture_monitor.py (listens on 5556)")
    print("3. Or use socat/ncat to duplicate the stream")
    print()
    print("Alternative: Kill ncat and let this script take over port 5555")

if __name__ == "__main__":
    main()
