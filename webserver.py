import os
import server
from aiohttp import web
import logging

# Setup logging
logger = logging.getLogger("trellis.webserver")

# Get the directory where this file is located
base_path = os.path.dirname(os.path.realpath(__file__))

# Multiple directories to search for media files
trellis_download_dirs = [
    os.path.join(os.getcwd(), "trellis_downloads"),
    os.path.join(base_path, "trellis_downloads"),
    os.path.join(os.path.dirname(os.getcwd()), "trellis_downloads"),  # One level up
]

# Ensure directories exist
for dir_path in trellis_download_dirs:
    try:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Trellis downloads directory: {dir_path}")
    except Exception as e:
        logger.warning(f"Could not create directory {dir_path}: {e}")


def find_file(file_id, possible_extensions, patterns=None):
    """
    Find a file across multiple directories with multiple possible naming patterns
    
    Args:
        file_id (str): File ID to search for
        possible_extensions (list): List of possible file extensions
        patterns (list, optional): List of filename patterns to try
    
    Returns:
        str: Full path to the file if found, None otherwise
    """
    if not file_id:
        return None
        
    # Default patterns if none provided
    if not patterns:
        patterns = [
            "{}_output{}", 
            "{}{}"
        ]
    
    # Search in all directories with all patterns
    for directory in trellis_download_dirs:
        if not os.path.exists(directory):
            continue
            
        for pattern in patterns:
            for ext in possible_extensions:
                path = os.path.join(directory, pattern.format(file_id, ext))
                if os.path.exists(path):
                    logger.info(f"Found file: {path}")
                    return path
                    
    return None


@server.PromptServer.instance.routes.get("/trellis/video/{video_id}")
async def get_trellis_video(request):
    """Serve video file by ID with proper CORS headers"""
    video_id = request.match_info["video_id"]
    logger.info(f"Video request for ID: {video_id}")
    
    # Get cache busting parameter if provided
    cache = request.query.get('cache', '')
    
    # Possible video extensions
    video_extensions = ['.mp4', '.webm', '.mov']
    
    # Find the video file
    video_path = find_file(video_id, video_extensions)
    
    if video_path:
        # Determine content type based on extension
        ext = os.path.splitext(video_path)[1].lower()
        content_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mov": "video/quicktime"
        }
        content_type = content_types.get(ext, "application/octet-stream")
        
        # Return with proper CORS headers
        return web.FileResponse(
            video_path,
            headers={
                "Content-Type": content_type,
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    
    # If video not found, return 404 with helpful error message
    search_paths = []
    for directory in trellis_download_dirs:
        for ext in video_extensions:
            search_paths.append(f"{directory}/{video_id}_output{ext}")
            search_paths.append(f"{directory}/{video_id}{ext}")
    
    logger.warning(f"Video {video_id} not found. Searched in: {', '.join(search_paths)}")
    
    return web.Response(
        status=404, 
        text=f"Video {video_id} not found. Please ensure the file exists in one of the search directories.",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
        }
    )

@server.PromptServer.instance.routes.get("/trellis/model/{model_id}")
async def get_trellis_model(request):
    """Serve 3D model file by ID with proper CORS headers"""
    model_id = request.match_info["model_id"]
    logger.info(f"Model request for ID: {model_id}")
    
    # Get cache busting parameter if provided
    cache = request.query.get('cache', '')
    
    # Possible model extensions
    model_extensions = ['.glb', '.gltf']
    
    # Find the model file
    model_path = find_file(model_id, model_extensions)
    
    if model_path:
        # Determine content type based on extension
        ext = os.path.splitext(model_path)[1].lower()
        content_type = "model/gltf-binary" if ext == ".glb" else "model/gltf+json"
        
        # Return with proper CORS headers
        return web.FileResponse(
            model_path,
            headers={
                "Content-Type": content_type,
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
    
    # If model not found, return 404 with helpful error message
    search_paths = []
    for directory in trellis_download_dirs:
        for ext in model_extensions:
            search_paths.append(f"{directory}/{model_id}_output{ext}")
            search_paths.append(f"{directory}/{model_id}{ext}")
    
    logger.warning(f"Model {model_id} not found. Searched in: {', '.join(search_paths)}")
    
    return web.Response(
        status=404, 
        text=f"Model {model_id} not found. Please ensure the file exists in one of the search directories.",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
        }
    )

# OPTIONS handlers for CORS preflight requests
@server.PromptServer.instance.routes.options("/trellis/video/{video_id}")
async def options_trellis_video(request):
    return web.Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
            "Access-Control-Max-Age": "86400"  # 24 hours
        }
    )

@server.PromptServer.instance.routes.options("/trellis/model/{model_id}")
async def options_trellis_model(request):
    return web.Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
            "Access-Control-Max-Age": "86400"  # 24 hours
        }
    )

@server.PromptServer.instance.routes.get("/trellis/simple-viewer/{type}/{id}")
async def simple_media_viewer(request):
    """Simple but functional media viewer that handles both video and 3D models"""
    media_type = request.match_info["type"]  # "model" or "video"
    media_id = request.match_info["id"]
    
    # Get cache busting parameter if provided
    cache = request.query.get('cache', '')
    
    logger.info(f"Simple viewer request: type={media_type}, id={media_id}")
    
    if media_type == "model":
        # HTML for model viewer with properly escaped braces for CSS
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>3D Model Viewer</title>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background: #222; }}
                #status {{ position: absolute; top: 10px; left: 10px; right: 10px; text-align: center; color: white; background: rgba(0,0,0,0.7); padding: 8px; border-radius: 4px; z-index: 100; transition: opacity 0.5s ease; }}
            </style>
        </head>
        <body>
            <div id="status">Loading model...</div>
            
            <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/build/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/GLTFLoader.js"></script>
            
            <script>
                console.log("Simple model viewer initializing...");
                
                // Basic Three.js setup
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x222222);
                
                const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
                camera.position.z = 3;
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.body.appendChild(renderer.domElement);
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
                scene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(1, 1, 1);
                scene.add(directionalLight);
                
                // Controls with damping for smoother feeling
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.1;
                
                // Load model with error handling
                const timestamp = Date.now(); // Cache busting
                const modelUrl = "/trellis/model/{id}?cache=" + timestamp;
                console.log("Loading model from:", modelUrl);
                
                // Add a fallback cube to show if model loading fails
                const geometry = new THREE.BoxGeometry(1, 1, 1);
                const material = new THREE.MeshStandardMaterial({{ 
                    color: 0x00a0ff,
                    metalness: 0.3,
                    roughness: 0.4
                }});
                const fallbackCube = new THREE.Mesh(geometry, material);
                fallbackCube.visible = false;
                scene.add(fallbackCube);
                
                const loader = new THREE.GLTFLoader();
                loader.load(
                    modelUrl,
                    (gltf) => {{
                        console.log("Model loaded successfully");
                        
                        scene.add(gltf.scene);
                        
                        // Center and scale the model
                        const box = new THREE.Box3().setFromObject(gltf.scene);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        
                        const maxDim = Math.max(size.x, size.y, size.z);
                        if (maxDim > 0) {{
                            const scale = 2.0 / maxDim;
                            gltf.scene.scale.set(scale, scale, scale);
                            gltf.scene.position.x = -center.x * scale;
                            gltf.scene.position.y = -center.y * scale;
                            gltf.scene.position.z = -center.z * scale;
                        }}
                        
                        document.getElementById('status').style.opacity = 0;
                    }},
                    (xhr) => {{
                        if (xhr.lengthComputable) {{
                            const percent = Math.round((xhr.loaded / xhr.total) * 100);
                            document.getElementById('status').textContent = `Loading: ${{percent}}%`;
                        }}
                    }},
                    (error) => {{
                        console.error('Error loading model:', error);
                        document.getElementById('status').textContent = `Error: ${{error.message || 'Failed to load model'}}`;
                        document.getElementById('status').style.color = 'red';
                        
                        // Show a fallback cube if model loading fails
                        fallbackCube.visible = true;
                        
                        // Animate the fallback cube
                        function animateCube() {{
                            fallbackCube.rotation.x += 0.01;
                            fallbackCube.rotation.y += 0.01;
                        }}
                        
                        // Override the animate function
                        const originalAnimate = animate;
                        animate = function() {{
                            requestAnimationFrame(animate);
                            animateCube();
                            controls.update();
                            renderer.render(scene, camera);
                        }};
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
                
                // Handle errors
                window.addEventListener('error', (e) => {{
                    console.error('Error in viewer:', e);
                    document.getElementById('status').textContent = `Error: ${{e.message}}`;
                    document.getElementById('status').style.color = 'red';
                }});
            </script>
        </body>
        </html>
        """.format(id=media_id)
        
    else:  # video
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Video Player</title>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background: #222; display: flex; justify-content: center; align-items: center; height: 100vh; }}
                #container {{ position: relative; max-width: 100%; max-height: 100vh; }}
                video {{ max-width: 100%; max-height: 85vh; }}
                #status {{ position: absolute; top: 10px; left: 10px; right: 10px; text-align: center; color: white; background: rgba(0,0,0,0.7); padding: 8px; border-radius: 4px; z-index: 100; transition: opacity 0.5s ease; }}
            </style>
        </head>
        <body>
            <div id="container">
                <div id="status">Loading video...</div>
                <video id="player" controls autoplay loop>
                    <source src="/trellis/video/{id}?cache={timestamp}" type="video/mp4">
                    <source src="/trellis/video/{id}?cache={timestamp}" type="video/webm">
                    Your browser does not support the video tag.
                </video>
            </div>
            <script>
                console.log("Simple video player initializing...");
                
                const status = document.getElementById('status');
                const video = document.getElementById('player');
                
                // Video event handlers
                video.addEventListener('loadeddata', () => {{
                    console.log("Video loaded successfully");
                    status.style.opacity = 0;
                }});
                
                video.addEventListener('error', (e) => {{
                    const errorMessage = video.error ? getVideoErrorMessage(video.error.code) : 'Unknown video error';
                    
                    console.error("Video loading error:", errorMessage);
                    status.textContent = `Error: ${{errorMessage}}`;
                    status.style.color = 'red';
                }});
                
                // Helper for error messages
                function getVideoErrorMessage(code) {{
                    switch(code) {{
                        case 1: return 'Video loading aborted';
                        case 2: return 'Network error while loading video';
                        case 3: return 'Video decoding failed';
                        case 4: return 'Video format not supported';
                        default: return 'Unknown error';
                    }}
                }}
                
                // Add buffering indicator
                video.addEventListener('waiting', () => {{
                    status.textContent = 'Buffering...';
                    status.style.opacity = 1;
                }});
                
                video.addEventListener('canplaythrough', () => {{
                    status.style.opacity = 0;
                }});
            </script>
        </body>
        </html>
        """.format(id=media_id, timestamp=cache)
    
    # Return with necessary CORS headers
    return web.Response(
        text=html, 
        content_type="text/html",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
            "Cache-Control": "no-cache"
        }
    )

@server.PromptServer.instance.routes.options("/trellis/simple-viewer/{type}/{id}")
async def options_simple_viewer(request):
    return web.Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
            "Access-Control-Max-Age": "86400"  # 24 hours
        }
    )

@server.PromptServer.instance.routes.get("/trellis/test-viewer")
async def test_viewer(request):
    """Simple test page for debugging iframe embedding"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Trellis Viewer Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            .test-container { margin-bottom: 30px; }
            .viewer { width: 400px; height: 300px; border: 1px solid #ccc; border-radius: 8px; overflow: hidden; }
            h2 { margin-top: 0; }
            .controls { margin: 10px 0; }
            input { padding: 5px; width: 300px; }
            button { padding: 5px 10px; }
            .direct-link { margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>Trellis Viewer Test Page</h1>
        
        <div class="test-container">
            <h2>Model Viewer Test</h2>
            <div class="controls">
                <input type="text" id="model-id" placeholder="Enter model ID">
                <button onclick="loadModel()">Load Model</button>
            </div>
            <div class="viewer" id="model-viewer"></div>
            <div class="direct-link" id="model-direct-link"></div>
        </div>
        
        <div class="test-container">
            <h2>Video Viewer Test</h2>
            <div class="controls">
                <input type="text" id="video-id" placeholder="Enter video ID">
                <button onclick="loadVideo()">Load Video</button>
            </div>
            <div class="viewer" id="video-viewer"></div>
            <div class="direct-link" id="video-direct-link"></div>
        </div>
        
        <div class="test-container">
            <h2>Direct Model Test</h2>
            <div class="controls">
                <input type="text" id="direct-model-id" placeholder="Enter model ID">
                <button onclick="testDirectModelAccess()">Test Direct Access</button>
            </div>
            <div id="direct-model-result" style="margin-top: 10px; padding: 10px; background: #eee; border-radius: 5px;"></div>
        </div>
        
        <script>
            // Add a test UUID as default
            const testId = "cbecf79b-beee-469e-81fe-0ff63d966d4b";
            document.getElementById('model-id').value = testId;
            document.getElementById('video-id').value = testId;
            document.getElementById('direct-model-id').value = testId;
            
            function loadModel() {
                const modelId = document.getElementById('model-id').value.trim();
                if (!modelId) {
                    alert('Please enter a model ID');
                    return;
                }
                
                const container = document.getElementById('model-viewer');
                container.innerHTML = ''; // Clear previous content
                
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                iframe.src = `/trellis/simple-viewer/model/${modelId}?cache=${Date.now()}`;
                
                container.appendChild(iframe);
                console.log(`Loaded model viewer iframe: ${modelId}`);
                
                // Show direct link for testing
                const linkElement = document.getElementById('model-direct-link');
                const modelUrl = `/trellis/model/${modelId}`;
                linkElement.innerHTML = `Direct model URL: <a href="${modelUrl}" target="_blank">${modelUrl}</a>`;
            }
            
            function loadVideo() {
                const videoId = document.getElementById('video-id').value.trim();
                if (!videoId) {
                    alert('Please enter a video ID');
                    return;
                }
                
                const container = document.getElementById('video-viewer');
                container.innerHTML = ''; // Clear previous content
                
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                iframe.src = `/trellis/simple-viewer/video/${videoId}?cache=${Date.now()}`;
                
                container.appendChild(iframe);
                console.log(`Loaded video viewer iframe: ${videoId}`);
                
                // Show direct link for testing
                const linkElement = document.getElementById('video-direct-link');
                const videoUrl = `/trellis/video/${videoId}`;
                linkElement.innerHTML = `Direct video URL: <a href="${videoUrl}" target="_blank">${videoUrl}</a>`;
            }
            
            // Test direct model access to check CORS
            function testDirectModelAccess() {
                const modelId = document.getElementById('direct-model-id').value.trim();
                if (!modelId) {
                    alert('Please enter a model ID');
                    return;
                }
                
                const resultDiv = document.getElementById('direct-model-result');
                resultDiv.innerHTML = 'Testing direct model access...';
                
                const modelUrl = `/trellis/model/${modelId}?cache=${Date.now()}`;
                
                // Use fetch to test direct access
                fetch(modelUrl)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return response.blob();
                    })
                    .then(blob => {
                        const size = (blob.size / 1024).toFixed(2);
                        resultDiv.innerHTML = `
                            <div style="color:green;">Success! Model loaded.</div>
                            <div>Size: ${size} KB</div>
                            <div>Type: ${blob.type}</div>
                        `;
                    })
                    .catch(error => {
                        resultDiv.innerHTML = `
                            <div style="color:red;">Error: ${error.message}</div>
                            <div>Please check browser console for more details.</div>
                        `;
                        console.error('Error testing model access:', error);
                    });
            }
            
            // Auto-load test models on page load
            window.onload = function() {
                loadModel();
                loadVideo();
            };
        </script>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")