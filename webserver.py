import os
import server
from aiohttp import web

# Get the directory where this file is located
base_path = os.path.dirname(os.path.realpath(__file__))
trellis_downloads_dir = os.path.join(os.getcwd(), "trellis_downloads")

# Add our routes to ComfyUI's server
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

@server.PromptServer.instance.routes.get("/trellis/view-model/{model_id}")
async def view_model(request):
    model_id = request.match_info["model_id"]
    
    # Simple HTML page with Three.js for 3D model viewing
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Trellis 3D Model Viewer</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; }}
            canvas {{ width: 100%; height: 100%; display: block; }}
        </style>
    </head>
    <body>
        <script src="https://cdn.jsdelivr.net/npm/three@0.157.0/build/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.157.0/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.157.0/examples/js/loaders/GLTFLoader.js"></script>
        <script>
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x333333);
            
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 5;
            
            const renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(0, 1, 1);
            scene.add(directionalLight);
            
            // Add controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.25;
            
            // Load the model
            const loader = new THREE.GLTFLoader();
            loader.load('/trellis/model/{model_id}', (gltf) => {{
                const model = gltf.scene;
                scene.add(model);
                
                // Center the model
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                
                // Adjust camera position based on model size
                const maxDim = Math.max(size.x, size.y, size.z);
                camera.position.set(center.x, center.y, center.z + maxDim * 2);
                controls.target.copy(center);
                controls.update();
            }});
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
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

@server.PromptServer.instance.routes.get("/trellis/view-video/{video_id}")
async def view_video(request):
    video_id = request.match_info["video_id"]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Trellis Video Player</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: #222; }}
            .container {{ display: flex; justify-content: center; align-items: center; height: 100vh; }}
            video {{ max-width: 100%; max-height: 100vh; }}
        </style>
    </head>
    <body>
        <div class="container">
            <video controls autoplay loop>
                <source src="/trellis/video/{video_id}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")

# Enable nodes to directly embed viewers in the UI
@server.PromptServer.instance.routes.get("/trellis/node/view-model/{model_id}")
async def node_view_model(request):
    model_id = request.match_info["model_id"]
    
    # Small-sized embedded viewer for nodes
    html = f"""
    <iframe 
        src="/trellis/view-model/{model_id}" 
        style="width: 100%; height: 100%; border: none;"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
    ></iframe>
    """
    
    return web.Response(text=html, content_type="text/html")

@server.PromptServer.instance.routes.get("/trellis/node/view-video/{video_id}")
async def node_view_video(request):
    video_id = request.match_info["video_id"]
    
    # Small-sized embedded viewer for nodes
    html = f"""
    <iframe 
        src="/trellis/view-video/{video_id}" 
        style="width: 100%; height: 100%; border: none;"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen
    ></iframe>
    """
    
    return web.Response(text=html, content_type="text/html")