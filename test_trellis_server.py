import asyncio
import websockets
import json
import base64
import os
import argparse
from PIL import Image
import io

async def test_trellis_server(server_url, image_path):
    """Test complete interaction with Trellis WebSocket server"""
    try:
        print(f"Connecting to Trellis server at: {server_url}")
        
        # Connect with basic parameters
        async with websockets.connect(
            server_url,
            ping_interval=30,
            ping_timeout=30,
            close_timeout=60,
            max_size=None
        ) as websocket:
            print(f"✓ Successfully connected to {server_url}")
            
            # Load and encode the image
            print(f"Loading image from: {image_path}")
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the command message with proper parameters
            message = {
                'command': 'process_single',
                'image': image_data,
                'params': {
                    'seed': 1,
                    'sparse_steps': 12,
                    'sparse_cfg_strength': 7.5,
                    'slat_steps': 12,
                    'slat_cfg_strength': 3,
                    'simplify': 0.95,
                    'texture_size': 1024
                }
            }
            
            print("Sending image processing request...")
            await websocket.send(json.dumps(message))
            
            # Get initial response (should return task acceptance)
            initial_response = await websocket.recv()
            initial_data = json.loads(initial_response)
            print(f"Initial response: {json.dumps(initial_data, indent=2)}")
            
            if initial_data.get('status') != 'accepted':
                print(f"❌ Request not accepted: {initial_data.get('message')}")
                return False
            
            task_id = initial_data.get('task_id')
            print(f"✓ Task accepted with ID: {task_id}")
            
            # Wait for processing completion
            print("Waiting for processing to complete...")
            while True:
                result = await websocket.recv()
                result_data = json.loads(result)
                print(f"Received: {json.dumps(result_data, indent=2)}")
                
                if result_data.get('status') == 'success':
                    session_id = result_data.get('session_id')
                    print(f"✓ Processing successful! Session ID: {session_id}")
                    
                    # Optional: Download files
                    # Uncomment if you want to download the resulting files
                    # await download_file(websocket, session_id, task_id, 'glb')
                    # await download_file(websocket, session_id, task_id, 'video')
                    
                    return True
                    
                elif result_data.get('status') == 'error':
                    print(f"❌ Processing failed: {result_data.get('message')}")
                    return False
                
                # Add progress updates if applicable
                else:
                    print(f"Status update: {result_data}")
            
    except Exception as e:
        print(f"❌ Error in Trellis interaction: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

async def download_file(websocket, session_id, task_id, file_type):
    """Download processed file (glb or video)"""
    try:
        file_extension = 'mp4' if file_type == 'video' else 'glb'
        output_path = f"output_{session_id}.{file_extension}"
        
        print(f"➜ Downloading {file_type} file...")
        offset = 0
        chunks = []
        
        # Collect chunks
        while True:
            command = f"get_{file_type}_chunk"
            request = {
                'command': command,
                'session_id': session_id,
                'task_id': task_id,
                'offset': offset,
                'size': 50000  # 50KB chunks
            }
            
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            chunk_data = json.loads(response)
            
            if chunk_data.get('status') != 'success':
                if chunk_data.get('message') == 'EOF':
                    break
                raise ValueError(f"Server error: {chunk_data.get('message')}")
            
            chunk = base64.b64decode(chunk_data['data'])
            if not chunk:
                break
                
            chunks.append(chunk)
            offset += len(chunk)
            
            if offset % (1024 * 1024) == 0:  # Show progress every 1MB
                print(f"  Downloaded: {offset/1024/1024:.1f} MB")
        
        # Write all chunks to file
        with open(output_path, 'wb') as f:
            for chunk in chunks:
                f.write(chunk)

        print(f"✓ Downloaded {file_type} file to {output_path}")
        return output_path
            
    except Exception as e:
        print(f"✗ Error downloading {file_type} file: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Trellis WebSocket server')
    parser.add_argument('--server', default='ws://35.164.116.189:38183/ws', help='Trellis server URL')
    parser.add_argument('--image', required=True, help='Path to image file to process')
    args = parser.parse_args()
    
    # Run the test
    asyncio.run(test_trellis_server(args.server, args.image))