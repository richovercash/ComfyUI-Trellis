import os
import base64
import tempfile
from PIL import Image
import numpy as np
import json
import logging
import time
import shutil

logger = logging.getLogger('TrellisUtils')

class TrellisImageUtils:
    """Utility functions for handling images between ComfyUI and Trellis"""
    
    @staticmethod
    def comfy_to_base64(comfy_image):
        """Convert ComfyUI image tensor to base64 string"""
        try:
            # Convert tensor to PIL Image
            if isinstance(comfy_image, list) or isinstance(comfy_image, tuple):
                # Handle batched images - take first one
                img = comfy_image[0]
            else:
                img = comfy_image
                
            # Convert to uint8 and create PIL image
            img_np = (img * 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            
            # Create temp file and save image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_filename = tmp.name
                pil_img.save(temp_filename)
            
            # Read file as bytes and encode to base64
            with open(temp_filename, 'rb') as f:
                image_bytes = f.read()
            
            # Remove temp file
            os.unlink(temp_filename)
            
            # Return base64 encoded image
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            return None
    
    @staticmethod
    def comfy_to_bytes(comfy_image):
        """Convert ComfyUI image tensor to bytes"""
        try:
            # Convert tensor to PIL Image
            if isinstance(comfy_image, list) or isinstance(comfy_image, tuple):
                # Handle batched images - take first one
                img = comfy_image[0]
            else:
                img = comfy_image
                
            # Convert to uint8 and create PIL image
            img_np = (img * 255).astype(np.uint8)
            pil_img = Image.fromarray(img_np)
            
            # Save to bytes IO
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_filename = tmp.name
                pil_img.save(temp_filename)
            
            # Read as bytes
            with open(temp_filename, 'rb') as f:
                image_bytes = f.read()
                
            # Clean up
            os.unlink(temp_filename)
            
            return image_bytes
            
        except Exception as e:
            logger.error(f"Error converting image to bytes: {e}")
            return None

    @staticmethod
    def base64_to_comfy(base64_str):
        """Convert base64 string to ComfyUI image tensor"""
        try:
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_str)
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_filename = tmp.name
                tmp.write(image_bytes)
            
            # Load image with PIL
            pil_img = Image.open(temp_filename)
            
            # Convert to numpy array for ComfyUI
            img_np = np.array(pil_img).astype(np.float32) / 255.0
            
            # Clean up
            os.unlink(temp_filename)
            
            # Return as tensor (batch of 1)
            return [img_np]
            
        except Exception as e:
            logger.error(f"Error converting base64 to image: {e}")
            return None


class TrellisFileManager:
    """Utility class for managing files related to Trellis processing"""
    
    def __init__(self, base_dir="trellis_files"):
        self.base_dir = base_dir
        self.temp_dir = os.path.join(base_dir, "temp")
        self.models_dir = os.path.join(base_dir, "models")
        self.videos_dir = os.path.join(base_dir, "videos")
        
        # Create directories
        for directory in [self.base_dir, self.temp_dir, self.models_dir, self.videos_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def clean_temp_files(self, max_age_hours=24):
        """Remove temporary files older than max_age_hours"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Removed old temp file: {filename}")
        
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
    
    def save_temp_image(self, image_data, prefix="image"):
        """Save image data to a temporary file"""
        try:
            timestamp = int(time.time())
            filename = f"{prefix}_{timestamp}.png"
            file_path = os.path.join(self.temp_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(image_data)
                
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving temp image: {e}")
            return None
    
    def organize_model(self, original_path):
        """Copy a model file to the organized models directory"""
        try:
            if not os.path.exists(original_path):
                logger.error(f"Original model file not found: {original_path}")
                return None
                
            # Generate unique filename
            timestamp = int(time.time())
            filename = f"model_{timestamp}.glb"
            dest_path = os.path.join(self.models_dir, filename)
            
            # Copy file
            shutil.copy2(original_path, dest_path)
            logger.info(f"Copied model to: {dest_path}")
            
            return dest_path
            
        except Exception as e:
            logger.error(f"Error organizing model file: {e}")
            return None
    
    def organize_video(self, original_path):
        """Copy a video file to the organized videos directory"""
        try:
            if not os.path.exists(original_path):
                logger.error(f"Original video file not found: {original_path}")
                return None
                
            # Generate unique filename
            timestamp = int(time.time())
            filename = f"video_{timestamp}.mp4"
            dest_path = os.path.join(self.videos_dir, filename)
            
            # Copy file
            shutil.copy2(original_path, dest_path)
            logger.info(f"Copied video to: {dest_path}")
            
            return dest_path
            
        except Exception as e:
            logger.error(f"Error organizing video file: {e}")
            return None


class TrellisMetadataManager:
    """Utility class for managing metadata for Trellis sessions and models"""
    
    def __init__(self, metadata_dir="trellis_metadata"):
        self.metadata_dir = metadata_dir
        os.makedirs(metadata_dir, exist_ok=True)
    
    def save_session_metadata(self, session_id, task_id, params=None, image_info=None):
        """Save metadata for a processing session"""
        try:
            metadata = {
                "session_id": session_id,
                "task_id": task_id,
                "timestamp": time.time(),
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "parameters": params or {},
                "image_info": image_info or {}
            }
            
            filename = os.path.join(self.metadata_dir, f"session_{session_id}.json")
            with open(filename, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Saved session metadata to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving session metadata: {e}")
            return None
    
    def load_session_metadata(self, session_id):
        """Load metadata for a processing session"""
        try:
            filename = os.path.join(self.metadata_dir, f"session_{session_id}.json")
            if not os.path.exists(filename):
                logger.warning(f"Session metadata not found: {session_id}")
                return None
                
            with open(filename, 'r') as f:
                metadata = json.load(f)
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error loading session metadata: {e}")
            return None
    
    def save_model_metadata(self, model_path, session_id=None, parameters=None):
        """Save metadata for a 3D model"""
        try:
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                return None
                
            model_filename = os.path.basename(model_path)
            metadata_filename = os.path.splitext(model_filename)[0] + "_metadata.json"
            
            metadata = {
                "model_path": model_path,
                "model_filename": model_filename,
                "file_size": os.path.getsize(model_path),
                "creation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "session_id": session_id,
                "parameters": parameters or {}
            }
            
            metadata_path = os.path.join(self.metadata_dir, metadata_filename)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Saved model metadata to: {metadata_path}")
            return metadata_path
            
        except Exception as e:
            logger.error(f"Error saving model metadata: {e}")
            return None
