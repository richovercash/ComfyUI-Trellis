import os
import folder_paths
from aiohttp import web
import server

# Get the directory where ComfyUI-Trellis is installed
base_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Register web directory for serving static files
server.PromptServer.instance.app.router.add_static("/trellis-viewer/", 
    os.path.join(base_path, "web"))

# Path where trellis files are stored
trellis_downloads_dir = os.path.join(os.path.dirname(folder_paths.get_output_directory()), "trellis_downloads")
trellis_files_dir = os.path.join(os.path.dirname(folder_paths.get_output_directory()), "trellis_files")

# Register routes to serve 3D models and videos
@server.PromptServer.instance.routes.get("/trellis/model/{model_id}")
async def get_trellis_model(request):
    model_id = request.match_info["model_id"]
    model_path = os.path.join(trellis_downloads_dir, f"{model_id}_output.glb")
    
    if not os.path.exists(model_path):
        return web.Response(status=404, text=f"Model {model_id} not found")
    
    return web.FileResponse(model_path)

@server.PromptServer.instance.routes.get("/trellis/video/{video_id}")
async def get_trellis_video(request):
    video_id = request.match_info["video_id"]
    video_path = os.path.join(trellis_downloads_dir, f"{video_id}_output.mp4")
    
    if not os.path.exists(video_path):
        return web.Response(status=404, text=f"Video {video_id} not found")
    
    return web.FileResponse(video_path)

# Get information about a model
@server.PromptServer.instance.routes.get("/trellis/info/{model_id}")
async def get_trellis_info(request):
    model_id = request.match_info["model_id"]
    model_path = os.path.join(trellis_downloads_dir, f"{model_id}_output.glb")
    video_path = os.path.join(trellis_downloads_dir, f"{model_id}_output.mp4")
    
    if not os.path.exists(model_path) and not os.path.exists(video_path):
        return web.json_response({"error": "Model not found"}, status=404)
    
    return web.json_response({
        "model_id": model_id,
        "model_path": os.path.exists(model_path),
        "video_path": os.path.exists(video_path),
        "model_url": f"/trellis/model/{model_id}",
        "video_url": f"/trellis/video/{model_id}",
    })