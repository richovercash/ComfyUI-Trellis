import os
import sys
import asyncio
import argparse
from PIL import Image
import numpy as np

# Add ComfyUI to path to import modules
comfy_path = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(comfy_path)

# Import Trellis modules
from trellis_client import TrellisClient
from trellis_config import config
from trellis_utils import TrellisImageUtils, TrellisFileManager, TrellisMetadataManager

async def process_image_with_trellis(image_path, preset_name="balanced"):
    """Process an image with Trellis using the specified preset"""
    print(f"Processing image: {image_path}")
    print(f"Using preset: {preset_name}")
    
    # Get parameters from preset
    params = config.get_processing_preset(preset_name)
    print(f"Parameters: {params}")
    
    # Create Trellis client
    client = TrellisClient(server_url=config.websocket_url)
    
    try:
        # Connect to server
        connected = await client.connect()
        if not connected:
            print("Failed to connect to Trellis server")
            return None
            
        print("Connected to Trellis server")
        
        # Process image
        result = await client.process_image(image_path, params)
        
        if not result:
            print("Processing failed")
            return None
            
        print(f"Processing successful, session_id: {result['session_id']}")
        
        # Create metadata manager
        metadata_manager = TrellisMetadataManager()
        
        # Save session metadata
        metadata_manager.save_session_metadata(
            result['session_id'], 
            result['task_id'], 
            params=params,
            image_info={"source_image": image_path}
        )
        
        # Download files
        print("Downloading GLB file...")
        glb_path = await client.download_file(result['session_id'], result['task_id'], 'glb')
        
        print("Downloading video file...")
        video_path = await client.download_file(result['session_id'], result['task_id'], 'video')
        
        # Save model metadata
        if glb_path:
            metadata_manager.save_model_metadata(
                glb_path, 
                session_id=result['session_id'],
                parameters=params
            )
        
        # Organize files
        file_manager = TrellisFileManager()
        
        if glb_path:
            organized_glb = file_manager.organize_model(glb_path)
            print(f"Organized GLB file: {organized_glb}")
            
        if video_path:
            organized_video = file_manager.organize_video(video_path)
            print(f"Organized video file: {organized_video}")
        
        # Return results
        return {
            "session_id": result['session_id'],
            "task_id": result['task_id'],
            "glb_path": glb_path,
            "video_path": video_path
        }
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return None
    finally:
        # Disconnect
        await client.disconnect()
        print("Disconnected from Trellis server")


async def process_comfy_image(comfy_image, preset_name="balanced"):
    """Process a ComfyUI image tensor with Trellis"""
    # Convert ComfyUI image to bytes
    image_bytes = TrellisImageUtils.comfy_to_bytes(comfy_image)
    
    if not image_bytes:
        print("Failed to convert image")
        return None
    
    # Save to temporary file
    file_manager = TrellisFileManager()
    temp_image_path = file_manager.save_temp_image(image_bytes)
    
    if not temp_image_path:
        print("Failed to save temporary image")
        return None
    
    # Process with Trellis
    result = await process_image_with_trellis(temp_image_path, preset_name)
    
    # Clean up temp files older than 1 hour
    file_manager.clean_temp_files(max_age_hours=1)
    
    return result


async def batch_process_images(image_paths, preset_name="balanced"):
    """Process multiple images with Trellis"""
    results = []
    
    for image_path in image_paths:
        print(f"\nProcessing {image_path}...")
        result = await process_image_with_trellis(image_path, preset_name)
        if result:
            results.append(result)
    
    return results


def load_image_to_comfy_format(image_path):
    """Load an image file to ComfyUI tensor format"""
    try:
        # Open image with PIL
        pil_img = Image.open(image_path)
        
        # Convert to numpy array
        img_np = np.array(pil_img).astype(np.float32) / 255.0
        
        # Return as list (batch of 1)
        return [img_np]
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


async def run_example_workflow(image_path):
    """Run a complete example workflow"""
    print("=== ComfyUI-Trellis Example Workflow ===")
    
    # 1. Load image in ComfyUI format
    print("1. Loading image...")
    comfy_image = load_image_to_comfy_format(image_path)
    
    if not comfy_image:
        print("Failed to load image")
        return
    
    # 2. Process with Trellis
    print("\n2. Processing with Trellis...")
    
    # Try different presets
    presets = ["fast", "balanced", "quality"]
    preset_choice = presets[1]  # Use balanced preset
    
    result = await process_comfy_image(comfy_image, preset_choice)
    
    if not result:
        print("Processing failed")
        return
    
    # 3. Display results
    print("\n3. Results:")
    print(f"Session ID: {result['session_id']}")
    print(f"Task ID: {result['task_id']}")
    print(f"GLB Model: {result['glb_path']}")
    print(f"Video Preview: {result['video_path']}")
    
    # 4. Load metadata
    print("\n4. Loading session metadata...")
    metadata_manager = TrellisMetadataManager()
    session_data = metadata_manager.load_session_metadata(result['session_id'])
    
    if session_data:
        print(f"Processing date: {session_data.get('date')}")
        print(f"Parameters used: {session_data.get('parameters')}")
    
    print("\n=== Workflow Complete ===")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ComfyUI-Trellis Example Workflow")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("--preset", choices=["fast", "balanced", "quality"], 
                        default="balanced", help="Processing preset to use")
    parser.add_argument("--batch", action="store_true", 
                        help="Process all images in the same directory")
    
    args = parser.parse_args()
    
    # Check if the image path exists
    if not os.path.exists(args.image_path):
        print(f"Error: Image not found at {args.image_path}")
        sys.exit(1)
    
    # Run workflow
    if args.batch:
        # Get all images in the directory
        image_dir = os.path.dirname(args.image_path)
        image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print(f"No images found in {image_dir}")
            sys.exit(1)
            
        print(f"Found {len(image_files)} images to process")
        asyncio.run(batch_process_images(image_files, args.preset))
    else:
        # Process single image
        asyncio.run(run_example_workflow(args.image_path))
