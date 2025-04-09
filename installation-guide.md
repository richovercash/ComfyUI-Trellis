# ComfyUI-Trellis Integration

This custom node package allows you to use ComfyUI output images as input to your Trellis 3D model generation system, enabling a seamless workflow between image generation and 3D model creation.

## Installation

1. Ensure you have ComfyUI installed and working properly
2. Navigate to your ComfyUI custom nodes directory:
   ```
   cd ComfyUI/custom_nodes/
   ```
3. Clone or download this repository:
   ```
   git clone https://github.com/yourusername/ComfyUI-Trellis
   ```
   (Or simply copy the Python file into a new directory)
4. Install required dependencies:
   ```
   pip install websockets aiohttp pillow
   ```
5. Restart ComfyUI

## Node Types

This package provides two different nodes for interacting with the Trellis system:

1. **Trellis Process (WebSocket)** - Connects directly to the Trellis WebSocket server for processing images
2. **Trellis Process (REST API)** - Uses the REST API provided by the server.py to process images

## Usage

### WebSocket Node

1. In your ComfyUI workflow, add a "Trellis Process (WebSocket)" node
2. Connect an image output from another node to the "image" input
3. Configure the parameters:
   - **server_url**: WebSocket URL of your Trellis server (default: ws://18.199.134.45:46173)
   - **seed**: Random seed for generation (1-2147483647)
   - **sparse_steps**: Number of sparse steps (1-50)
   - **sparse_cfg_strength**: Sparse CFG strength (0-10)
   - **slat_steps**: SLAT steps (1-50)
   - **slat_cfg_strength**: SLAT CFG strength (0-10)
   - **simplify**: Mesh simplification factor (0.9-0.98)
   - **texture_size**: Texture size in pixels (512, 1024, 1536, or 2048)
4. Run the workflow
5. The node will output two file paths:
   - **glb_path**: Path to the downloaded GLB 3D model file
   - **video_path**: Path to the downloaded video preview file

### REST API Node

1. Add a "Trellis Process (REST API)" node to your workflow
2. Connect an image output from another node to the "image" input
3. Configure the **api_url** parameter to point to your server.py API (e.g., http://localhost:8000)
4. Configure the other parameters as with the WebSocket node
5. Run the workflow
6. The node will output the same two file paths as the WebSocket node

## Example Workflow

Here's an example of how to use the Trellis node in a workflow:

1. **KSampler** -> Generates image from a prompt
2. **TrellisProcessWebSocket** -> Processes the image to create a 3D model
3. **SaveImage** -> Optional, to save the original image

## Troubleshooting

- Ensure your Trellis server is running and accessible
- Check the ComfyUI console for error messages
- For WebSocket connection issues, verify your server URL and network configuration
- For REST API issues, make sure your FastAPI server (server.py) is running correctly

## File Output Locations

- WebSocket Node: Files are saved to the `trellis_downloads` directory
- REST API Node: Files are saved to the `trellis_api_downloads` directory

Both directories are created automatically in your ComfyUI working directory if they don't exist.

## Advanced Usage

### Using the Output Files

You can use the output file paths in other nodes, for example:

1. Connect the "glb_path" output to a custom "GLB Viewer" node
2. Use the file paths with a custom Python script node for further processing

### Batch Processing

When processing multiple images from a batch:

1. Set up a workflow with batch processing
2. Add the Trellis node after your batch generation
3. Note that each image will be processed individually, which may take some time
