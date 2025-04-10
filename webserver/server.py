from server import PromptServer
from aiohttp import web
import os
import mimetypes

# Register file types for proper MIME type handling
mimetypes.add_type('model/gltf-binary', '.glb')
mimetypes.add_type('video/mp4', '.mp4')

# File serving routes
@PromptServer.instance.routes.get("/trellis/file/{file_id}")
async def serve_model_file(request):
    """Serve model or video file"""
    file_id = request.match_info["file_id"]
    
    # Get file path from registry
    if not hasattr(PromptServer.instance, 'trellis_files'):
        return web.Response(status=404, text="File registry not found")
    
    file_info = PromptServer.instance.trellis_files.get(file_id)
    if not file_info:
        return web.Response(status=404, text="File not found")
    
    file_path = file_info["path"]
    if not os.path.exists(file_path):
        return web.Response(status=404, text="File no longer exists")
    
    # Determine content type
    content_type = mimetypes.guess_type(file_path)[0]
    if not content_type:
        if file_path.endswith('.glb'):
            content_type = "model/gltf-binary"
        elif file_path.endswith('.mp4'):
            content_type = "video/mp4"
        else:
            content_type = "application/octet-stream"
    
    # Allow CORS for external model viewers
    headers = {
        "Content-Type": content_type,
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "Content-Type"
    }
    
    # Serve the file
    return web.FileResponse(file_path, headers=headers)

# Model viewer route
@PromptServer.instance.routes.get("/trellis/view/{file_id}")
async def view_model(request):
    """Serve model viewer HTML"""
    file_id = request.match_info["file_id"]
    
    # Get file info
    if not hasattr(PromptServer.instance, 'trellis_files'):
        return web.Response(status=404, text="File registry not found")
    
    file_info = PromptServer.instance.trellis_files.get(file_id)
    if not file_info:
        return web.Response(status=404, text="File not found")
    
    file_path = file_info["path"]
    if not os.path.exists(file_path):
        return web.Response(status=404, text="File no longer exists")
    
    # Generate HTML for model viewer 
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trellis 3D Model Viewer</title>
    <style>
        body {{ margin: 0; overflow: hidden; background-color: #1a1a1a; }}
        #viewer-container {{ width: 100%; height: 100%; position: absolute; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/examples/js/loaders/GLTFLoader.js"></script>
</head>
<body>
    <div id="viewer-container"></div>
    <script>
        // Initialize Three.js
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a1a);
        
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.z = 5;
        
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById('viewer-container').appendChild(renderer.domElement);
        
        // Add lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 1.5);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 10);
        directionalLight.position.set(5, 5, 5);
        scene.add(directionalLight);
        
        const pointLight = new THREE.PointLight(0xffffff, 25);
        pointLight.position.set(-2.5, 2.5, 0);
        scene.add(pointLight);
        
        // Add grid
        const gridHelper = new THREE.GridHelper(20, 20, 0x6e6e6e, 0x6e6e6e);
        scene.add(gridHelper);
        
        // Add controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        
        // Load model
        const loader = new THREE.GLTFLoader();
        loader.load(
            '/trellis/file/{file_id}',
            (gltf) => {{
                const model = gltf.scene;
                
                // Get bounding box
                const box = new THREE.Box3().setFromObject(model);
                
                // Center on X and Z axes
                const center = box.getCenter(new THREE.Vector3());
                model.position.x -= center.x;
                model.position.z -= center.z;
                
                // Position bottom of model on grid (y=0)
                model.position.y -= box.min.y;
                
                scene.add(model);
            }},
            undefined,
            (error) => {{
                console.error('Error loading model:', error);
            }}
        );
        
        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        
        // Handle resize
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>
    """
    
    return web.Response(text=html, content_type="text/html")
