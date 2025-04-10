import os
import folder_paths
from aiohttp import web
import server

# Get the directory where this file is located (ComfyUI-Trellis folder)
base_path = os.path.dirname(os.path.realpath(__file__))

# Path where trellis files are stored
trellis_downloads_dir = os.path.join(os.getcwd(), "trellis_downloads")
trellis_files_dir = os.path.join(os.getcwd(), "trellis_files")

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

# Add HTML page for model viewer
@server.PromptServer.instance.routes.get("/trellis/view-model/{model_id}")
async def view_trellis_model(request):
    model_id = request.match_info["model_id"]
    model_url = f"/trellis/model/{model_id}"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trellis 3D Model Viewer</title>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/build/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/GLTFLoader.js"></script>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #222; }}
            #viewer {{ width: 100%; height: 100vh; }}
        </style>
    </head>
    <body>
        <div id="viewer"></div>
        <script>
            const modelUrl = "{model_url}";
            
            // Setup Three.js scene
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById('viewer').appendChild(renderer.domElement);
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);
            
            // Add controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            
            // Load model
            const loader = new THREE.GLTFLoader();
            loader.load(modelUrl, (gltf) => {{
                const model = gltf.scene;
                scene.add(model);
                
                // Center camera on model
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                
                camera.position.set(
                    center.x + maxDim * 2, 
                    center.y + maxDim * 0.5, 
                    center.z + maxDim * 2
                );
                controls.target.copy(center);
            }});
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")

# Add HTML page for video player
@server.PromptServer.instance.routes.get("/trellis/view-video/{video_id}")
async def view_trellis_video(request):
    video_id = request.match_info["video_id"]
    video_url = f"/trellis/video/{video_id}"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trellis Video Player</title>
        <style>
            body {{ margin: 0; padding: 0; background-color: #222; }}
            .container {{ 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                width: 100%;
            }}
            video {{ 
                max-width: 100%; 
                max-height: 100vh; 
                box-shadow: 0 0 20px rgba(0,0,0,0.5);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <video controls autoplay loop>
                <source src="{video_url}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")