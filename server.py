# api/server.py

# 1. All imports first
from fastapi import BackgroundTasks, FastAPI, UploadFile, HTTPException
import asyncio
from fastapi.responses import FileResponse
import os
from typing import List
import base64
from pydantic import BaseModel
from .trellis_client import TrellisClient
import json
from pathlib import Path
from fastapi import File, Form
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime  # Add this if missing
# Add to server.py after the existing imports
from pydantic import BaseModel, Field, validator
from typing import Optional


class ProcessingParameters(BaseModel):
    seed: int = Field(default=1, ge=1, le=2147483647)
    sparse_steps: int = Field(default=12, ge=1, le=50)
    sparse_cfg_strength: float = Field(default=7.5, ge=0, le=10)
    slat_steps: int = Field(default=12, ge=1, le=50)
    slat_cfg_strength: float = Field(default=3, ge=0, le=10)
    simplify: float = Field(default=0.95, ge=0.9, le=0.98)
    texture_size: int = Field(default=1024, ge=512, le=2048)

    @validator('texture_size')
    def validate_texture_size(cls, v):
        valid_sizes = [512, 1024, 1536, 2048]
        if v not in valid_sizes:
            raise ValueError(f'Texture size must be one of {valid_sizes}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "seed": 1,
                "sparse_steps": 12,
                "sparse_cfg_strength": 7.5,
                "slat_steps": 12,
                "slat_cfg_strength": 3,
                "simplify": 0.95,
                "texture_size": 1024
            }
        }

# 2. Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 3. Initialize variables
active_clients = {}
processing_status = {}
PROJECT_ROOT = Path(__file__).parent.parent
DOWNLOAD_PATH = PROJECT_ROOT / 'frontend' / 'public' / 'downloads'
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# 4. Define models
class ProcessingStatus(BaseModel):
    status: str
    message: str = ""
    session_id: str = None
    task_id: str = None
    progress: float = 0
    download_progress: dict = {"glb": 0, "video": 0}

# 5. Define Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up server and connecting to WebSocket...")
    server_url = os.getenv('TRELLIS_SERVER_URL', 'ws://18.199.134.45:46173')
    client = TrellisClient(server_url=server_url)
    
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            connected = await client.connect()
            if connected:
                active_clients["default"] = client
                print("Successfully connected to WebSocket server")
                break
            else:
                raise Exception("Connection failed")
        except Exception as e:
            retry_count += 1
            print(f"Connection attempt {retry_count} failed: {str(e)}")
            if retry_count < max_retries:
                await asyncio.sleep(2)  # Wait before retrying
    
    if retry_count >= max_retries:
        print("Failed to connect to WebSocket server after multiple attempts")
    
    yield
    
    # Shutdown
    if "default" in active_clients:
        client = active_clients["default"]
        await client.disconnect()
        print("Disconnected from WebSocket server")

# 6. Create FastAPI instance
# Update FastAPI app initialization
app = FastAPI(lifespan=lifespan)




# Add a health check endpoint that includes WebSocket status
@app.get("/health")
async def health_check():
    client = active_clients.get("default")
    is_connected = client and client.connected and client.websocket and not client.websocket.closed
    
    return {
        "status": "healthy" if is_connected else "unhealthy",
        "websocket_connected": is_connected,
        "timestamp": datetime.now().isoformat()
    }
# app = FastAPI()






@app.on_event("startup")
async def startup_event():
    # Initialize the TrellisClient on startup
    server_url = os.getenv('TRELLIS_SERVER_URL', 'ws://18.199.134.45:46173')
    client = TrellisClient(server_url=server_url)
    active_clients["default"] = client
    await client.connect()


    

# Update in server.py
# Update the process endpoint
@app.post("/process")
async def process_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    parameters: Optional[str] = Form(None)
):
    logger.info(f"→ Process endpoint hit with image: {image.filename}")
    
    # Parse and validate parameters
    try:
        params_dict = json.loads(parameters) if parameters else {}
        processing_params = ProcessingParameters(**params_dict)
        logger.info(f"→ Validated parameters: {processing_params.dict()}")
    except json.JSONDecodeError as e:
        logger.error(f"✗ Invalid JSON in parameters: {e}")
        raise HTTPException(status_code=400, detail="Invalid parameters format")
    except ValueError as e:
        logger.error(f"✗ Parameter validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    client = active_clients.get("default")
    logger.info(f"→ Client connected: {client and client.connected}")
    
    if not client or not client.connected:
        logger.error("✗ Server not connected")
        raise HTTPException(status_code=503, detail="Server not connected")
    
    try:
        # Save file temporarily
        temp_path = f"temp_{image.filename}"
        content = await image.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Initialize status
        processing_status[image.filename] = {
            "status": "processing",
            "message": "Starting image processing",
            "progress": 0.0
        }
        
        # Process in background with parameters
        background_tasks.add_task(
            process_images_task,
            temp_path,
            image.filename,
            [],  # No additional paths for single image
            [temp_path],  # Temp files to clean up
            processing_params.dict()  # Pass validated parameters
        )
        
        return {
            "status": "accepted",
            "filename": image.filename,
            "message": "Processing started"
        }
        
    except Exception as e:
        logger.error(f"Error in process_image: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

async def process_images_task(
    main_image_path: str,
    filename: str,
    additional_paths: List[str],
    temp_files: List[str],
    parameters: dict = None
):
    """Single function to handle image processing with parameters"""
    client = active_clients.get("default")
    logger.info(f"Starting process_images_task for {filename}")
    if parameters:
        logger.info(f"Using parameters: {parameters}")
    
    try:
        # Process images based on whether it's multi or single
        is_multi = len(additional_paths) > 0
        if is_multi:
            logger.info(f"Processing multiple images: {[main_image_path] + additional_paths}")
            result = await client.process_multiple_images(
                [main_image_path] + additional_paths,
                parameters
            )
        else:
            logger.info(f"Processing single image: {main_image_path}")
            result = await client.process_image(main_image_path, parameters)
            
        logger.info(f"Process result: {result}")
        
        if not result:
            logger.error("No result from process_image")
            processing_status[filename] = {
                "status": "failed",
                "message": "Processing failed"
            }
            return
            
        logger.info(f"Got session_id: {result['session_id']}")
        
        # Update status to downloading
        processing_status[filename] = {
            "status": "downloading",
            "message": "Downloading GLB file...",
            "session_id": result['session_id'],
            "task_id": result['task_id'],
            "download_progress": {"glb": 0, "video": 0}
        }

        # Define status update callback
        async def update_download_progress(file_type: str, progress: float):
            if filename in processing_status:
                processing_status[filename]["download_progress"][file_type] = progress
                processing_status[filename]["message"] = f"Downloading {file_type.upper()} file: {int(progress)}%"
                logger.info(f"{file_type.upper()} download progress: {progress:.1f}%")
        
        # Download files with progress tracking
        await client.download_file(
            result['session_id'], 
            result['task_id'], 
            'glb',
            update_download_progress
        )
        logger.info("GLB download complete")
        
        processing_status[filename]["message"] = "Downloading video file..."
        await client.download_file(
            result['session_id'], 
            result['task_id'], 
            'video',
            update_download_progress
        )
        logger.info("Video download complete")
        
        # Update final status
        processing_status[filename] = {
            "status": "complete",
            "message": "All files downloaded",
            "session_id": result['session_id'],
            "download_progress": {"glb": 100, "video": 100}
        }
        
    except Exception as e:
        logger.error(f"Error in process_images_task: {e}")
        processing_status[filename] = {
            "status": "failed",
            "message": str(e)
        }
    finally:
        # Cleanup temporary files
        for path in temp_files:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Cleaned up temp file: {path}")
@app.get("/status/{filename}")
async def get_status(filename: str):
    logger.debug(f"Status request received for {filename}")
    
    if filename not in processing_status:
        logger.debug(f"File {filename} not found in processing_status")
        raise HTTPException(status_code=404, detail="File not found")
    
    current_status = processing_status[filename]
    logger.debug(f"Returning status for {filename}: {current_status}")
    return current_status

async def process_and_track_status(image: UploadFile, additional_images: List[UploadFile] = []):
    filename = image.filename
    logger.debug(f"Starting process_and_track_status for {filename}")
    
    try:
        # Read and save image temporarily
        content = await image.read()
        temp_path = f"temp_{filename}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Process additional images if present
        additional_paths = []
        for idx, add_image in enumerate(additional_images):
            add_content = await add_image.read()
            add_path = f"temp_additional_{idx}_{add_image.filename}"
            with open(add_path, "wb") as f:
                f.write(add_content)
            additional_paths.append(add_path)
        
        client = active_clients.get("default")
        is_multi = len(additional_images) > 0
        
        # Update status to processing
        processing_status[filename] = ProcessingStatus(
            status="processing",
            message="Processing image",
            progress=0.2
        ).dict()
        
        # Process the image(s)
        if is_multi:
            result = await client.process_multiple_images([temp_path] + additional_paths)
        else:
            result = await client.process_image(temp_path)
        
        if not result:
            raise Exception("Processing failed - no result received")
        
        # Update status with session_id
        processing_status[filename] = ProcessingStatus(
            status="downloading",
            message="Processing complete, downloading files",
            session_id=result['session_id'],
            task_id=result['task_id'],
            progress=0.8
        ).dict()
        
        # Download files
        await client.download_file(result['session_id'], result['task_id'], 'glb')
        await client.download_file(result['session_id'], result['task_id'], 'video')
        
        # Update final status
        processing_status[filename] = ProcessingStatus(
            status="complete",
            message="All files downloaded",
            session_id=result['session_id'],
            progress=1.0
        ).dict()
        
    except Exception as e:
        logger.error(f"Error in process_and_track_status: {str(e)}")
        processing_status[filename] = ProcessingStatus(
            status="error",
            message=str(e)
        ).dict()
        
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_path):
            os.remove(temp_path)
        for path in additional_paths:
            if os.path.exists(path):
                os.remove(path)


@app.get("/download/{session_id}/{file_type}")
async def download_file(session_id: str, file_type: str):
    if file_type not in ['glb', 'video']:
        raise HTTPException(status_code=400, detail="Invalid file type")
        
    file_extension = 'mp4' if file_type == 'video' else 'glb'
    file_path = DOWNLOAD_PATH / f"{session_id}_output.{file_extension}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=f"output.{file_extension}"
    )
@app.post("/status/{filename}")
async def update_status(filename: str, status_update: ProcessingStatus):
    """Update the status for a given filename"""
    try:
        # Update the status in the processing_status dictionary
        processing_status[filename] = status_update
        return {"message": "Status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Update the process_multi endpoint
@app.post("/process_multi")
async def process_multi_images(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    parameters: Optional[str] = Form(None)
):
    logger.info(f"→ Process multi endpoint hit with {len(files)} files")
    
    # Parse and validate parameters
    try:
        params_dict = json.loads(parameters) if parameters else {}
        processing_params = ProcessingParameters(**params_dict)
        logger.info(f"→ Validated parameters: {processing_params.dict()}")
    except json.JSONDecodeError as e:
        logger.error(f"✗ Invalid JSON in parameters: {e}")
        raise HTTPException(status_code=400, detail="Invalid parameters format")
    except ValueError as e:
        logger.error(f"✗ Parameter validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    client = active_clients.get("default")
    logger.info(f"→ Client connected: {client and client.connected}")
    
    if not client or not client.connected:
        logger.error("✗ Server not connected")
        raise HTTPException(status_code=503, detail="Server not connected")
    
    try:
        # Save files temporarily
        temp_files = []
        temp_paths = []
        
        # Save all files temporarily
        for idx, file in enumerate(files):
            temp_path = f"temp_{idx}_{file.filename}"
            logger.info(f"Saving file to {temp_path}")
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)
            temp_files.append(temp_path)
            temp_paths.append(temp_path)
        
        # Use first filename as reference
        reference_filename = files[0].filename
        processing_status[reference_filename] = {
            "status": "processing",
            "message": f"Starting processing of {len(files)} images",
            "progress": 0.0
        }
        
        # Process in background with parameters
        background_tasks.add_task(
            process_images_task,
            temp_paths[0],  # main image path
            reference_filename,
            temp_paths[1:],  # additional image paths
            temp_files,  # all temp files to clean up
            processing_params.dict()  # Pass validated parameters
        )
        
        return {
            "status": "accepted",
            "filename": reference_filename,
            "message": f"Processing started for {len(files)} images"
        }
        
    except Exception as e:
        logger.error(f"Error in process_multi_images: {str(e)}")
        # Clean up any temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        raise HTTPException(status_code=500, detail=str(e))