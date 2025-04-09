import asyncio
import websockets
import sys
import json

async def test_websocket_connection(server_url):
    """Test a simple WebSocket connection to the specified server URL"""
    try:
        print(f"Connecting to WebSocket server at: {server_url}")
        
        # Connect with basic parameters
        async with websockets.connect(
            server_url,
            ping_interval=30,
            ping_timeout=30,
            close_timeout=30,
            max_size=None
        ) as websocket:
            print(f"✓ Successfully connected to {server_url}")
            
            # Try to send a simple message
            message = {
                "command": "test_connection",
                "client": "test_script"
            }
            
            print(f"Sending test message: {json.dumps(message)}")
            await websocket.send(json.dumps(message))
            
            # Try to receive a response (with 10 second timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("No response received within 10 seconds (this might be normal)")
            
            print("Connection test completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error connecting to WebSocket: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    # Get server URL from command line or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://35.164.116.189:38183"
    
    # Add /ws suffix if not present
    if not server_url.endswith('/ws'):
        server_url = f"{server_url}/ws"
    
    # Run the test
    asyncio.run(test_websocket_connection(server_url))