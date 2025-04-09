import json
import aiohttp
import os
import base64
import websockets
import asyncio
from PIL import Image
import io
import numpy as np
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TrellisNode')

# Main Trellis Client for WebSocket communication
class TrellisClientComfy:
    def __init__(self, server_url, download_dir='trellis_downloads'):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    async def connect(self):
        """Connect to WebSocket server"""
        if self.websocket and not self.websocket.closed:
            logger.info("Already connected")
            return True

        try:
            url = f"{self.server_url.rstrip('/')}/ws"
            logger.info(f"Connecting to {url}")
            
            self.websocket = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=10,
                max_size=None
            )
            
            self.connected = True
            logger.info("✓ Successfully connected to server")
            return True
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            self.websocket = None
            return False

    async def disconnect(self):
        if self.websocket:
            try:
                await self.websocket.close()
                self.websocket = None
                self.connected = False
                logger.info("✓ Disconnected from server")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")

    async def ensure_connection(self):
        """Ensure WebSocket connection is active"""
        if not self.connected or not self.websocket or self.websocket.closed:
            return await self.connect()
        return True

    async def process_image(self, image_data, params=None):
        """Process an image using WebSocket connection"""
        if not await self.ensure_connection():
            raise ValueError("Could not establish connection to server")

        try:
            # Convert image data to base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            # Default parameters
            default_params = {
                'seed': 1,
                'sparse_steps': 12,
                'sparse_cfg_strength': 7.5,
                'slat_steps': 12,
                'slat_cfg_strength': 3,
                'simplify': 0.95,
                'texture_size': 1024
            }
            if params:
                default_params.update(params)

            # Prepare message
            message = {
                'command': 'process_single',
                'image': encoded_image,
                'params': default_params
            }

            # Send request
            await self.websocket.send(json.dumps(message))
            logger.info("Sent image processing request")

            # Get initial response
            initial_response = await self.websocket.recv()
            initial_data = json.loads(initial_response)

            if initial_data.get('status') != 'accepted':
                raise ValueError(f"Request not accepted: {initial_data.get('message')}")

            task_id = initial_data.get('task_id')
            logger.info(f"Task accepted with ID: {task_id}")

            # Wait for processing completion
            while True:
                result = await self.websocket.recv()
                result_data = json.loads(result)
                
                if result_data.get('status') == 'success':
                    return {
                        'task_id': task_id,
                        'session_id': result_data.get('session_id'),
                        'status': 'success'
                    }
                elif result_data.get('status') == 'error':
                    raise ValueError(result_data.get('message', 'Processing failed'))

        except Exception as e:
            logger.error(f"Error in process_image: {e}")
            self.connected = False  # Mark as disconnected on error
            raise

    async def download_file(self, session_id, task_id, file_type):
        """Download processed file (glb or video)"""
        try:
            file_extension = 'mp4' if file_type == 'video' else 'glb'
            output_path = os.path.join(self.download_dir, f"{session_id}_output.{file_extension}")
            
            logger.info(f"➜ Downloading {file_type} file...")
            offset = 0
            chunks = []  # Store chunks temporarily
            
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
                
                await self.websocket.send(json.dumps(request))
                response = await self.websocket.recv()
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
            
            # Write all chunks to file
            with open(output_path, 'wb') as f:
                for chunk in chunks:
                    f.write(chunk)

            logger.info(f"✓ Downloaded {file_type} file to {output_path}")
            return output_path
                
        except Exception as e:
            logger.error(f"✗ Error downloading {file_type} file: {e}")
            return None


# ComfyUI Node Definitions
class TrellisProcessNode:
    """Node that processes an image through Trellis WebSocket server"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "server_url": ("STRING", {"default": "ws://18.199.134.45:46173"}),
                "seed": ("INT", {"default": 1, "min": 1, "max": 2147483647}),
                "sparse_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "sparse_cfg_strength": ("FLOAT", {"default": 7.5, "min": 0.0, "max": 10.0, "step": 0.1}),
                "slat_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "slat_cfg_strength": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "simplify": ("FLOAT", {"default": 0.95, "min": 0.9, "max": 0.98, "step": 0.01}),
                "texture_size": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 512}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("glb_path", "video_path")
    FUNCTION = "process"
    CATEGORY = "Trellis"

    async def _process_async(self, image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                           slat_steps, slat_cfg_strength, simplify, texture_size):
        # Convert ComfyUI image format to bytes
        image_pil = Image.fromarray((image[0] * 255).astype(np.uint8))
        
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        image_pil.save(temp_file.name)
        temp_file.close()
        
        # Read the file as bytes
        with open(temp_file.name, 'rb') as f:
            image_bytes = f.read()
        
        # Clean up the temporary file
        os.unlink(temp_file.name)
        
        # Setup parameters
        params = {
            'seed': seed,
            'sparse_steps': sparse_steps,
            'sparse_cfg_strength': sparse_cfg_strength,
            'slat_steps': slat_steps,
            'slat_cfg_strength': slat_cfg_strength,
            'simplify': simplify,
            'texture_size': texture_size
        }
        
        # Validate texture_size to ensure it's one of the allowed values
        valid_texture_sizes = [512, 1024, 1536, 2048]
        if params['texture_size'] not in valid_texture_sizes:
            # Round to nearest valid size
            params['texture_size'] = min(valid_texture_sizes, key=lambda x: abs(x - params['texture_size']))
            logger.warning(f"Adjusted texture_size to {params['texture_size']}")
            
        # Process image
        client = TrellisClientComfy(server_url)
        try:
            result = await client.process_image(image_bytes, params)
            
            if not result or result.get('status') != 'success':
                logger.error("Processing failed")
                return None, None
                
            # Download files
            glb_path = await client.download_file(result['session_id'], result['task_id'], 'glb')
            video_path = await client.download_file(result['session_id'], result['task_id'], 'video')
            
            # Disconnect when done
            await client.disconnect()
            
            return glb_path, video_path
        
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            if client.connected:
                await client.disconnect()
            return None, None

    def process(self, image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                slat_steps, slat_cfg_strength, simplify, texture_size):
        # Create event loop and run async process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            glb_path, video_path = loop.run_until_complete(
                self._process_async(image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                                  slat_steps, slat_cfg_strength, simplify, texture_size)
            )
            return (glb_path or "", video_path or "")
        finally:
            loop.close()


# Alternative REST API approach for Trellis Communication
class TrellisRESTNode:
    """Node that processes an image through Trellis REST API"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_url": ("STRING", {"default": "http://localhost:8000"}),
                "seed": ("INT", {"default": 1, "min": 1, "max": 2147483647}),
                "sparse_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "sparse_cfg_strength": ("FLOAT", {"default": 7.5, "min": 0.0, "max": 10.0, "step": 0.1}),
                "slat_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "slat_cfg_strength": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "simplify": ("FLOAT", {"default": 0.95, "min": 0.9, "max": 0.98, "step": 0.01}),
                "texture_size": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 512}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("glb_path", "video_path")
    FUNCTION = "process"
    CATEGORY = "Trellis"

    async def _process_api_async(self, image, api_url, seed, sparse_steps, sparse_cfg_strength, 
                              slat_steps, slat_cfg_strength, simplify, texture_size):
        # Convert ComfyUI image format to bytes
        image_pil = Image.fromarray((image[0] * 255).astype(np.uint8))
        
        # Save to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        image_pil.save(temp_file.name)
        temp_file.close()
        
        # Setup parameters
        params = {
            'seed': seed,
            'sparse_steps': sparse_steps,
            'sparse_cfg_strength': sparse_cfg_strength,
            'slat_steps': slat_steps,
            'slat_cfg_strength': slat_cfg_strength,
            'simplify': simplify,
            'texture_size': texture_size
        }
        
        # Submit via REST API
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/process"
            
            # Prepare form data with file and parameters
            form_data = aiohttp.FormData()
            form_data.add_field('image', 
                                open(temp_file.name, 'rb'),
                                filename='image.png',
                                content_type='image/png')
            form_data.add_field('parameters', json.dumps(params))
            
            # Submit request
            async with session.post(url, data=form_data) as response:
                # Clean up temp file
                os.unlink(temp_file.name)
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error: {response.status} - {error_text}")
                    return None, None
                
                result = await response.json()
                
                if result.get('status') != 'accepted':
                    logger.error(f"Request not accepted: {result.get('message')}")
                    return None, None
                
                # Poll for status until complete
                filename = result.get('filename')
                while True:
                    await asyncio.sleep(2)  # Poll every 2 seconds
                    
                    async with session.get(f"{api_url}/status/{filename}") as status_response:
                        if status_response.status != 200:
                            logger.error(f"Failed to get status: {status_response.status}")
                            return None, None
                        
                        status_data = await status_response.json()
                        current_status = status_data.get('status')
                        
                        if current_status == 'complete':
                            # Download files
                            session_id = status_data.get('session_id')
                            download_dir = 'trellis_api_downloads'
                            os.makedirs(download_dir, exist_ok=True)
                            
                            glb_path = os.path.join(download_dir, f"{session_id}_output.glb")
                            video_path = os.path.join(download_dir, f"{session_id}_output.mp4")
                            
                            # Download GLB file
                            async with session.get(f"{api_url}/download/{session_id}/glb") as glb_response:
                                if glb_response.status == 200:
                                    with open(glb_path, 'wb') as f:
                                        f.write(await glb_response.read())
                                else:
                                    glb_path = None
                            
                            # Download video file
                            async with session.get(f"{api_url}/download/{session_id}/video") as video_response:
                                if video_response.status == 200:
                                    with open(video_path, 'wb') as f:
                                        f.write(await video_response.read())
                                else:
                                    video_path = None
                            
                            return glb_path, video_path
                            
                        elif current_status == 'failed' or current_status == 'error':
                            logger.error(f"Processing failed: {status_data.get('message')}")
                            return None, None

    def process(self, image, api_url, seed, sparse_steps, sparse_cfg_strength, 
                slat_steps, slat_cfg_strength, simplify, texture_size):
        # Create event loop and run async process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            glb_path, video_path = loop.run_until_complete(
                self._process_api_async(image, api_url, seed, sparse_steps, sparse_cfg_strength, 
                                     slat_steps, slat_cfg_strength, simplify, texture_size)
            )
            return (glb_path or "", video_path or "")
        finally:
            loop.close()


# Node Definitions
NODE_CLASS_MAPPINGS = {
    "TrellisProcessWebSocket": TrellisProcessNode,
    "TrellisProcessREST": TrellisRESTNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisProcessWebSocket": "Trellis Process (WebSocket)",
    "TrellisProcessREST": "Trellis Process (REST API)"
}
