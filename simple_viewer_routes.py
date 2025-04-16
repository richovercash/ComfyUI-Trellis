import os
import server
from aiohttp import web
import logging
import json
import time

# Setup logging
logger = logging.getLogger("trellis.viewer")

# Get the directory where this file is located
base_path = os.path.dirname(os.path.realpath(__file__))

# Multiple download directories to search in
download_dirs = [
    os.path.join(os.getcwd(), "trellis_downloads"),
    os.path.join(base_path, "trellis_downloads"),
    os.path.join(os.path.dirname(os.getcwd()), "trellis_downloads"),  # One level up
]

# Ensure directories exist
for dir_path in download_dirs:
    os.makedirs(dir_path, exist_ok=True)

# Dictionary to cache file locations (reduced file system searches)
file_cache = {
    'video': {},  # video_id -> (path, timestamp)
    'model': {}   # model_id -> (path, timestamp)
}

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300

def find_file(file_id, patterns, extensions, cache_type):
    """Find a file in multiple directories with caching"""
    # Check if in cache and still valid
    if file_id in file_cache[cache_type]:
        path, timestamp = file_cache[cache_type][file_id]
        if os.path.exists(path) and time.time() - timestamp < CACHE_TTL:
            return path
    
    # Search all combinations of directories, patterns and extensions
    for directory in download_dirs:
        for pattern in patterns:
            for ext in extensions:
                path = os.path.join(directory, pattern.format(ext))
                if os.path.exists(path):
                    # Update cache
                    file_cache[cache_type][file_id] = (path, time.time())
                    return path
    
    # Not found
    return None

@server.PromptServer.instance.routes.get("/trellis/video/{video_id}")
async def get_trellis_video(request):
    """Serve video file by ID with proper CORS and caching headers"""
    video_id = request.match_info["video_id"]
    logger.info(f"Video request for ID: {video_id}")
    
    # Get optional query parameters
    try:
        # Get cache busting and cross-origin parameters
        cache_bust = request.query.get('cache_bust', '')
        allow_origin = request.headers.get('Origin', '*')
    except Exception as e:
        logger.warning(f"Error parsing query parameters: {e}")
        cache_bust = ''
        allow_origin = '*'
    
    # List of possible extensions to check
    extensions = ['.mp4', '.webm', '.mov']
    
    # List of possible naming patterns
    patterns = [
        f"{video_id}_output{{}}", 
        f"{video_id}{{}}"
    ]
    
    # Search for the video with caching
    video_path = find_file(video_id, patterns, extensions, 'video')
    
    if video_path:
        # Determine content type based on extension
        ext = os.path.splitext(video_path)[1].lower()
        content_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mov": "video/quicktime"
        }
        content_type = content_types.get(ext, "application/octet-stream")
        
        # Return with proper CORS and caching headers
        return web.FileResponse(
            video_path,
            headers={
                "Content-Type": content_type,
                "Access-Control-Allow-Origin": allow_origin,
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
                "Cache-Control": "max-age=3600",  # 1 hour cache
                "X-File-Path": video_path  # For debugging
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
    """Enhanced interactive media viewer that handles both video and 3D models"""
    media_type = request.match_info["type"]  # "model" or "video"
    media_id = request.match_info["id"]
    
    # Get optional query parameters
    autoplay = request.query.get('autoplay', 'true').lower() == 'true'
    loop = request.query.get('loop', 'true').lower() == 'true'
    autorotate = request.query.get('autoRotate', 'false').lower() == 'true'
    
    logger.info(f"Trellis simple viewer request: type={media_type}, id={media_id}, autoplay={autoplay}, loop={loop}, autorotate={autorotate}")
    
    if media_type == "model":
        # HTML for enhanced model viewer with properly escaped braces for CSS
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Enhanced 3D Model Viewer</title>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background: #222; }}
                #status {{ position: absolute; top: 10px; left: 10px; right: 10px; text-align: center; color: white; background: rgba(0,0,0,0.7); padding: 8px; border-radius: 4px; z-index: 100; transition: opacity 0.5s ease; }}
                #controls {{ position: absolute; bottom: 10px; left: 10px; right: 10px; text-align: center; background: rgba(0,0,0,0.5); padding: 10px; border-radius: 4px; z-index: 100; display: flex; justify-content: center; gap: 15px; }}
                .control-btn {{ background: rgba(255,255,255,0.2); color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; }}
                .control-btn:hover {{ background: rgba(255,255,255,0.3); }}
                canvas {{ width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <div id="status">Loading model...</div>
            <div id="controls" style="display: none;">
                <button id="reset-btn" class="control-btn">Reset View</button>
                <button id="rotate-btn" class="control-btn">Auto-Rotate</button>
                <button id="wireframe-btn" class="control-btn">Wireframe</button>
                <button id="lighting-btn" class="control-btn">Toggle Lighting</button>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/three@0.152.2/build/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.152.2/examples/js/controls/OrbitControls.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.152.2/examples/js/loaders/GLTFLoader.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.152.2/examples/js/loaders/DRACOLoader.js"></script>
            
            <script>
                console.log("Enhanced model viewer initializing...");
                
                // Setup messaging to parent
                function notifyParent(type, data) {{
                    try {{
                        window.parent.postMessage({{ type, id: "{id}", ...data }}, '*');
                    }} catch (e) {{
                        console.warn("Could not send message to parent", e);
                    }}
                }}
                
                // Basic Three.js setup
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x222222);
                
                const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
                camera.position.z = 5;
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.physicallyCorrectLights = true;
                renderer.outputEncoding = THREE.sRGBEncoding;
                renderer.shadowMap.enabled = true;
                document.body.appendChild(renderer.domElement);
                
                // Setup lights - default configuration
                let lighting = {{
                    ambient: new THREE.AmbientLight(0xffffff, 0.4),
                    directional: new THREE.DirectionalLight(0xffffff, 1.0),
                    point: new THREE.PointLight(0xffffff, 1.0)
                }};
                
                // Configure lights
                lighting.directional.position.set(1, 1, 1);
                lighting.point.position.set(0, 5, 0);
                
                // Add lights to scene
                scene.add(lighting.ambient);
                scene.add(lighting.directional);
                scene.add(lighting.point);
                
                // Controls with damping (smoother feeling)
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.1;
                controls.autoRotate = {autorotate};
                controls.autoRotateSpeed = 2.0;
                
                // State variables
                let loadedModel = null;
                let showingWireframe = false;
                let isRotating = {autorotate};
                let zoomFactor = 1.5; // Adjust as needed
                
                // Load model with error handling and compression support
                const modelUrl = "/trellis/model/{id}";
                console.log("Loading model from:", modelUrl);
                
                // Setup loaders (including DRACO compression support)
                const dracoLoader = new THREE.DRACOLoader();
                dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.152.2/examples/js/libs/draco/');
                
                const loader = new THREE.GLTFLoader();
                loader.setDRACOLoader(dracoLoader);
                
                loader.load(
                    modelUrl,
                    (gltf) => {{
                        console.log("Model loaded successfully");
                        loadedModel = gltf.scene;
                        
                        const status = document.getElementById('status');
                        
                        // Check if model has any meshes
                        let hasMeshes = false;
                        gltf.scene.traverse(function(child) {{
                            if (child.isMesh) {{
                                hasMeshes = true;
                                
                                // Enable shadows
                                child.castShadow = true;
                                child.receiveShadow = true;
                                
                                // Store original materials for wireframe toggle
                                child.userData.originalMaterial = child.material.clone();
                            }}
                        }});
                        
                        if (!hasMeshes) {{
                            status.textContent = 'Model loaded but contains no meshes';
                            status.style.color = 'orange';
                            notifyParent('modelWarning', {{ message: 'Model contains no meshes' }});
                            return;
                        }}
                        
                        scene.add(gltf.scene);
                        
                        // Center and scale
                        fitCameraToObject(gltf.scene, zoomFactor);
                        
                        status.style.opacity = 0;
                        document.getElementById('controls').style.display = 'flex';
                        
                        notifyParent('modelLoaded', {{ success: true }});
                    }},
                    (xhr) => {{
                        if (xhr.lengthComputable) {{
                            const percent = Math.round((xhr.loaded / xhr.total) * 100);
                            document.getElementById('status').textContent = `Loading: ${{percent}}%`;
                            notifyParent('modelLoadProgress', {{ percent }});
                        }}
                    }},
                    (error) => {{
                        console.error('Error loading model:', error);
                        document.getElementById('status').textContent = `Error: ${{error.message || 'Failed to load model'}}`;
                        document.getElementById('status').style.color = 'red';
                        
                        notifyParent('modelLoadError', {{ error: error.message || 'Failed to load model' }});
                        
                        // Add fallback content - a simple cube
                        createFallbackGeometry();
                    }}
                );
                
                // Create a fallback geometry if model fails to load
                function createFallbackGeometry() {{
                    const geometry = new THREE.BoxGeometry(1, 1, 1);
                    const material = new THREE.MeshStandardMaterial({{ 
                        color: 0x00a0ff,
                        metalness: 0.3,
                        roughness: 0.4
                    }});
                    const cube = new THREE.Mesh(geometry, material);
                    scene.add(cube);
                    
                    function animateCube() {{
                        if (cube) {{
                            cube.rotation.x += 0.01;
                            cube.rotation.y += 0.01;
                        }}
                    }}
                    
                    // Override the animate function
                    const originalAnimate = animate;
                    animate = function() {{
                        requestAnimationFrame(animate);
                        animateCube();
                        if (originalAnimate && typeof originalAnimate === 'function') {{
                            originalAnimate();
                        }}
                    }};
                }}
                
                // Fit camera to model
                function fitCameraToObject(object, fitOffset = 1.2) {{
                    const box = new THREE.Box3().setFromObject(object);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    
                    // Find largest dimension to determine optimal distance
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const fov = camera.fov * (Math.PI / 180);
                    let cameraZ = (maxDim / 2) / Math.tan(fov / 2);
                    cameraZ *= fitOffset;
                    
                    // Update camera and controls
                    camera.position.set(center.x, center.y, center.z + cameraZ);
                    const minZ = box.min.z;
                    const cameraToFarEdge = (minZ < 0) ? -minZ + cameraZ : cameraZ - minZ;
                    camera.far = Math.max(1000, cameraToFarEdge * 3);
                    camera.updateProjectionMatrix();
                    
                    if (controls) {{
                        // Set controls target to center of the object
                        controls.target.copy(center);
                        controls.maxDistance = cameraToFarEdge * 2;
                        controls.update();
                    }}
                }}
                
                // Setup UI controls
                const resetBtn = document.getElementById('reset-btn');
                const rotateBtn = document.getElementById('rotate-btn');
                const wireframeBtn = document.getElementById('wireframe-btn');
                const lightingBtn = document.getElementById('lighting-btn');
                
                resetBtn.addEventListener('click', () => {{
                    if (loadedModel) {{
                        fitCameraToObject(loadedModel, zoomFactor);
                    }}
                }});
                
                rotateBtn.addEventListener('click', () => {{
                    isRotating = !isRotating;
                    controls.autoRotate = isRotating;
                    rotateBtn.textContent = isRotating ? 'Stop Rotation' : 'Auto-Rotate';
                }});
                
                wireframeBtn.addEventListener('click', () => {{
                    showingWireframe = !showingWireframe;
                    wireframeBtn.textContent = showingWireframe ? 'Surface View' : 'Wireframe';
                    
                    if (loadedModel) {{
                        loadedModel.traverse(child => {{
                            if (child.isMesh) {{
                                if (showingWireframe) {{
                                    // Switch to wireframe
                                    const wireframeMaterial = new THREE.MeshBasicMaterial({{
                                        color: 0xffffff,
                                        wireframe: true
                                    }});
                                    child.userData.originalMaterial = child.material;
                                    child.material = wireframeMaterial;
                                }} else {{
                                    // Switch back to original material
                                    if (child.userData.originalMaterial) {{
                                        child.material = child.userData.originalMaterial;
                                    }}
                                }}
                            }}
                        }});
                    }}
                }});
                
                let brightLighting = true;
                lightingBtn.addEventListener('click', () => {{
                    brightLighting = !brightLighting;
                    
                    if (brightLighting) {{
                        lighting.ambient.intensity = 0.4;
                        lighting.directional.intensity = 1.0;
                        lighting.point.intensity = 1.0;
                        lightingBtn.textContent = 'Dim Lighting';
                    }} else {{
                        lighting.ambient.intensity = 0.1;
                        lighting.directional.intensity = 0.3;
                        lighting.point.intensity = 0.3;
                        lightingBtn.textContent = 'Bright Lighting';
                    }}
                }});
                
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
                    notifyParent('viewerError', {{ error: e.message }});
                }});
                
                // Notify parent that we're initialized
                notifyParent('viewerInitialized', {{ type: 'model' }});
            </script>
        </body>
        </html>
        """.format(id=media_id, autorotate=str(autorotate).lower())
        
    else:  # video
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Enhanced Video Player</title>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background: #222; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; }}
                #container {{ position: relative; max-width: 100%; max-height: 100vh; }}
                video {{ max-width: 100%; max-height: 85vh; }}
                #status {{ position: absolute; top: 10px; left: 10px; right: 10px; text-align: center; color: white; background: rgba(0,0,0,0.7); padding: 8px; border-radius: 4px; z-index: 100; transition: opacity 0.5s ease; }}
                #controls {{ width: 100%; display: flex; justify-content: center; gap: 15px; margin-top: 10px; }}
                .control-btn {{ background: rgba(255,255,255,0.2); color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; }}
                .control-btn:hover {{ background: rgba(255,255,255,0.3); }}
            </style>
        </head>
        <body>
            <div id="container">
                <div id="status">Loading video...</div>
                <video id="player" {autoplay} {loop} controls>
                    <source src="/trellis/video/{id}?cache_bust={time}" type="video/mp4">
                    <source src="/trellis/video/{id}?cache_bust={time}" type="video/webm">
                    Your browser does not support the video tag.
                </video>
                <div id="controls">
                    <button id="play-btn" class="control-btn">Play</button>
                    <button id="pause-btn" class="control-btn">Pause</button>
                    <button id="restart-btn" class="control-btn">Restart</button>
                    <button id="toggle-loop-btn" class="control-btn">{loop_text}</button>
                </div>
            </div>
            <script>
                console.log("Enhanced video player initializing...");
                
                // Setup messaging to parent
                function notifyParent(type, data) {{
                    try {{
                        window.parent.postMessage({{ type, id: "{id}", ...data }}, '*');
                    }} catch (e) {{
                        console.warn("Could not send message to parent", e);
                    }}
                }}
                
                // Setup elements
                const status = document.getElementById('status');
                const video = document.getElementById('player');
                const playBtn = document.getElementById('play-btn');
                const pauseBtn = document.getElementById('pause-btn');
                const restartBtn = document.getElementById('restart-btn');
                const loopBtn = document.getElementById('toggle-loop-btn');
                
                // Set initial state
                let isLooping = {loop};
                
                // Add event listeners
                playBtn.addEventListener('click', () => video.play());
                pauseBtn.addEventListener('click', () => video.pause());
                restartBtn.addEventListener('click', () => {{ video.currentTime = 0; video.play(); }});
                loopBtn.addEventListener('click', () => {{
                    isLooping = !isLooping;
                    video.loop = isLooping;
                    loopBtn.textContent = isLooping ? 'Disable Loop' : 'Enable Loop';
                }});
                
                // Video event handlers
                video.addEventListener('loadeddata', () => {{
                    console.log("Video loaded successfully");
                    status.style.opacity = 0;
                    notifyParent('videoCanPlay', {{ success: true, duration: video.duration }});
                }});
                
                video.addEventListener('error', (e) => {{
                    const errorMessage = video.error ? 
                        `Error: ${{video.error.code}} - ${{getVideoErrorMessage(video.error.code)}}` : 
                        'Unknown video error';
                    
                    console.error("Video loading error:", errorMessage);
                    status.textContent = errorMessage;
                    status.style.color = 'red';
                    
                    notifyParent('videoError', {{ 
                        error: errorMessage,
                        code: video.error ? video.error.code : null
                    }});
                }});
                
                video.addEventListener('playing', () => {{
                    notifyParent('videoPlaying', {{ currentTime: video.currentTime }});
                }});
                
                video.addEventListener('pause', () => {{
                    notifyParent('videoPaused', {{ currentTime: video.currentTime }});
                }});
                
                video.addEventListener('ended', () => {{
                    notifyParent('videoEnded', {{}});
                }});
                
                // Helper for error messages
                function getVideoErrorMessage(code) {{
                    switch(code) {{
                        case 1: return 'MEDIA_ERR_ABORTED - Fetching process aborted by user';
                        case 2: return 'MEDIA_ERR_NETWORK - Error occurred when downloading';
                        case 3: return 'MEDIA_ERR_DECODE - Error occurred when decoding';
                        case 4: return 'MEDIA_ERR_SRC_NOT_SUPPORTED - Format not supported';
                        default: return 'Unknown error';
                    }}
                }}
                
                // Automatic retry logic for network errors
                let retryCount = 0;
                const MAX_RETRIES = 3;
                
                video.addEventListener('stalled', () => {{
                    if (retryCount < MAX_RETRIES) {{
                        retryCount++;
                        status.textContent = `Video stalled, retrying (${{retryCount}}/${{MAX_RETRIES}})...`;
                        status.style.opacity = 1;
                        
                        // Try to reload the video
                        setTimeout(() => {{
                            const currentTime = video.currentTime;
                            const wasPlaying = !video.paused;
                            
                            // Update source with cache busting
                            const sources = video.getElementsByTagName('source');
                            for (let i = 0; i < sources.length; i++) {{
                                const src = sources[i].src.split('?')[0];
                                sources[i].src = `${{src}}?cache_bust=${{Date.now()}}`;
                            }}
                            
                            // Reload and restore state
                            video.load();
                            video.currentTime = currentTime;
                            if (wasPlaying) video.play();
                            
                        }}, 1000);
                    }} else {{
                        status.textContent = `Video stalled after ${{MAX_RETRIES}} retries. Try refreshing the page.`;
                        notifyParent('videoStalled', {{ retries: retryCount }});
                    }}
                }});
                
                // Handle progress and waiting
                video.addEventListener('waiting', () => {{
                    status.textContent = 'Buffering...';
                    status.style.opacity = 1;
                }});
                
                video.addEventListener('canplaythrough', () => {{
                    status.style.opacity = 0;
                }});
                
                // Notify parent that we're initialized
                notifyParent('viewerInitialized', {{ type: 'video' }});
            </script>
        </body>
        </html>
        """.format(
            id=media_id, 
            time=int(time.time()),  # Add timestamp for cache busting
            autoplay='autoplay' if autoplay else '',
            loop='loop' if loop else '',
            loop_text='Disable Loop' if loop else 'Enable Loop'
        )
    
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

@server.PromptServer.instance.routes.get("/trellis/check-media-exists/{id}")
async def check_media_exists(request):
    """Check if media files exist for a given ID without actually serving them"""
    media_id = request.match_info["id"]
    logger.info(f"Checking media existence for ID: {media_id}")
    
    # Patterns to search for
    patterns = [
        "{}_output{}", 
        "{}{}"
    ]
    
    # Check for model files
    model_extensions = ['.glb', '.gltf']
    model_path = find_file(media_id, patterns, model_extensions, 'model')
    
    # Check for video files
    video_extensions = ['.mp4', '.webm', '.mov']
    video_path = find_file(media_id, patterns, video_extensions, 'video')
    
    # Return results
    return web.json_response({
        "id": media_id,
        "model": {
            "exists": model_path is not None,
            "path": model_path if model_path else None,
            "searchedLocations": [d for d in download_dirs if os.path.exists(d)]
        },
        "video": {
            "exists": video_path is not None,
            "path": video_path if video_path else None,
            "searchedLocations": [d for d in download_dirs if os.path.exists(d)]
        }
    }, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
    })

@server.PromptServer.instance.routes.get("/trellis/debug-viewer")
async def debug_viewer(request):
    """Advanced debug page for testing all viewer functionality"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Trellis Viewer Debugger</title>
        <style>
            body { font-family: system-ui, -apple-system, sans-serif; margin: 20px; background: #f5f5f7; color: #333; }
            h1, h2 { color: #1d1d1f; }
            .container { display: flex; flex-wrap: wrap; gap: 20px; }
            .panel { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); flex: 1; min-width: 400px; }
            .viewer { width: 100%; height: 300px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; margin: 10px 0; }
            input[type="text"] { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #0071e3; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; margin-right: 5px; margin-bottom: 5px; }
            button:hover { background: #0077ed; }
            .log { background: #f0f0f0; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto; font-family: monospace; margin-top: 10px; }
            .error { color: #c41e3a; }
            .success { color: #34c759; }
            .warning { color: #ff9500; }
            .code { font-family: monospace; background: #f8f8f8; padding: 2px 4px; border-radius: 3px; }
            .toggle-btn { background: #8e8e93; }
            .toggle-btn.active { background: #34c759; }
        </style>
    </head>
    <body>
        <h1>Trellis Media Viewer Debugger</h1>
        <p>Use this tool to test media loading, diagnose issues, and verify your setup.</p>
        
        <div class="container">
            <div class="panel">
                <h2>3D Model Testing</h2>
                <div>
                    <input type="text" id="model-id" placeholder="Enter model ID (UUID or filename)">
                    <div>
                        <button id="load-model-btn">Load Model</button>
                        <button id="check-model-btn">Check Existence</button>
                        <button id="toggle-model-rotate" class="toggle-btn">Auto-Rotate</button>
                        <button id="toggle-model-wireframe" class="toggle-btn">Wireframe</button>
                    </div>
                </div>
                <div class="viewer" id="model-viewer-container"></div>
                <h3>Status</h3>
                <div class="log" id="model-log"></div>
            </div>
            
            <div class="panel">
                <h2>Video Testing</h2>
                <div>
                    <input type="text" id="video-id" placeholder="Enter video ID (UUID or filename)">
                    <div>
                        <button id="load-video-btn">Load Video</button>
                        <button id="check-video-btn">Check Existence</button>
                        <button id="toggle-video-autoplay" class="toggle-btn active">Auto-Play</button>
                        <button id="toggle-video-loop" class="toggle-btn active">Loop</button>
                    </div>
                </div>
                <div class="viewer" id="video-viewer-container"></div>
                <h3>Status</h3>
                <div class="log" id="video-log"></div>
            </div>
        </div>
        
        <div class="panel" style="margin-top: 20px;">
            <h2>Troubleshooting</h2>
            <p>If you're experiencing issues:</p>
            <ol>
                <li>Check that media files exist in one of these directories:
                    <ul id="directories"></ul>
                </li>
                <li>Verify file naming follows the pattern: <span class="code">&lt;ID&gt;_output.&lt;extension&gt;</span> or <span class="code">&lt;ID&gt;.&lt;extension&gt;</span></li>
                <li>Check browser console for JavaScript errors</li>
                <li>Verify CORS headers are being properly set</li>
            </ol>
            <button id="test-directories-btn">Test Search Directories</button>
            <button id="test-cors-btn">Test CORS</button>
            <div class="log" id="troubleshoot-log"></div>
        </div>
        
        <script>
            // Utility functions
            function logMessage(containerId, message, type = 'info') {
                const container = document.getElementById(containerId);
                const entry = document.createElement('div');
                entry.className = type;
                entry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
                container.appendChild(entry);
                container.scrollTop = container.scrollHeight;
            }
            
            // Toggle button state
            function setupToggleButton(id) {
                const btn = document.getElementById(id);
                btn.addEventListener('click', () => {
                    btn.classList.toggle('active');
                });
                return btn;
            }
            
            // Model viewer functions
            const modelIdInput = document.getElementById('model-id');
            const loadModelBtn = document.getElementById('load-model-btn');
            const checkModelBtn = document.getElementById('check-model-btn');
            const modelViewerContainer = document.getElementById('model-viewer-container');
            const modelAutoRotateBtn = setupToggleButton('toggle-model-rotate');
            const modelWireframeBtn = setupToggleButton('toggle-model-wireframe');
            
            loadModelBtn.addEventListener('click', () => {
                const modelId = modelIdInput.value.trim();
                if (!modelId) {
                    logMessage('model-log', 'Please enter a model ID', 'error');
                    return;
                }
                
                loadModel(modelId);
            });
            
            function loadModel(modelId) {
                logMessage('model-log', `Loading model: ${modelId}`);
                modelViewerContainer.innerHTML = '';
                
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                
                // Add options based on toggle states
                const params = new URLSearchParams();
                params.append('autoRotate', modelAutoRotateBtn.classList.contains('active'));
                
                iframe.src = `/trellis/simple-viewer/model/${modelId}?${params.toString()}`;
                modelViewerContainer.appendChild(iframe);
                
                // Listen for messages from the iframe
                window.addEventListener('message', function(event) {
                    // Only handle model-related messages
                    if (event.data && event.data.type && event.data.type.startsWith('model')) {
                        const messageType = event.data.type;
                        
                        switch(messageType) {
                            case 'modelLoaded':
                                logMessage('model-log', 'Model loaded successfully', 'success');
                                break;
                            case 'modelLoadProgress':
                                if (event.data.percent) {
                                    logMessage('model-log', `Loading progress: ${event.data.percent}%`);
                                }
                                break;
                            case 'modelLoadError':
                                logMessage('model-log', `Error loading model: ${event.data.error || 'Unknown error'}`, 'error');
                                break;
                            case 'viewerInitialized':
                                logMessage('model-log', 'Model viewer initialized');
                                break;
                            case 'viewerError':
                                logMessage('model-log', `Viewer error: ${event.data.error || 'Unknown error'}`, 'error');
                                break;
                        }
                    }
                });
            }
            
            checkModelBtn.addEventListener('click', () => {
                const modelId = modelIdInput.value.trim();
                if (!modelId) {
                    logMessage('model-log', 'Please enter a model ID', 'error');
                    return;
                }
                
                logMessage('model-log', `Checking if model exists: ${modelId}`);
                
                fetch(`/trellis/check-media-exists/${modelId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.model.exists) {
                            logMessage('model-log', `Model found: ${data.model.path}`, 'success');
                        } else {
                            logMessage('model-log', 'Model not found in any search location', 'error');
                            logMessage('model-log', `Searched in: ${data.model.searchedLocations.join(', ')}`, 'info');
                        }
                    })
                    .catch(error => {
                        logMessage('model-log', `Error checking model: ${error}`, 'error');
                    });
            });
            
            // Video viewer functions
            const videoIdInput = document.getElementById('video-id');
            const loadVideoBtn = document.getElementById('load-video-btn');
            const checkVideoBtn = document.getElementById('check-video-btn');
            const videoViewerContainer = document.getElementById('video-viewer-container');
            const videoAutoplayBtn = setupToggleButton('toggle-video-autoplay');
            const videoLoopBtn = setupToggleButton('toggle-video-loop');
            
            loadVideoBtn.addEventListener('click', () => {
                const videoId = videoIdInput.value.trim();
                if (!videoId) {
                    logMessage('video-log', 'Please enter a video ID', 'error');
                    return;
                }
                
                loadVideo(videoId);
            });
            
            function loadVideo(videoId) {
                logMessage('video-log', `Loading video: ${videoId}`);
                videoViewerContainer.innerHTML = '';
                
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                
                // Add options based on toggle states
                const params = new URLSearchParams();
                params.append('autoplay', videoAutoplayBtn.classList.contains('active'));
                params.append('loop', videoLoopBtn.classList.contains('active'));
                
                iframe.src = `/trellis/simple-viewer/video/${videoId}?${params.toString()}`;
                videoViewerContainer.appendChild(iframe);
                
                // Listen for messages from the iframe
                window.addEventListener('message', function(event) {
                    // Only handle video-related messages
                    if (event.data && event.data.type && event.data.type.startsWith('video')) {
                        const messageType = event.data.type;
                        
                        switch(messageType) {
                            case 'videoCanPlay':
                                logMessage('video-log', 'Video loaded and ready to play', 'success');
                                if (event.data.duration) {
                                    logMessage('video-log', `Video duration: ${event.data.duration.toFixed(2)} seconds`);
                                }
                                break;
                            case 'videoLoadStart':
                                logMessage('video-log', 'Video load started');
                                break;
                            case 'videoError':
                                logMessage('video-log', `Error loading video: ${event.data.error || 'Unknown error'}`, 'error');
                                break;
                            case 'videoPlaying':
                                logMessage('video-log', 'Video playing');
                                break;
                            case 'videoPaused':
                                logMessage('video-log', 'Video paused');
                                break;
                            case 'videoEnded':
                                logMessage('video-log', 'Video playback ended');
                                break;
                            case 'videoStalled':
                                logMessage('video-log', `Video stalled after ${event.data.retries} retries`, 'warning');
                                break;
                            case 'viewerInitialized':
                                logMessage('video-log', 'Video viewer initialized');
                                break;
                        }
                    }
                });
            }
            
            checkVideoBtn.addEventListener('click', () => {
                const videoId = videoIdInput.value.trim();
                if (!videoId) {
                    logMessage('video-log', 'Please enter a video ID', 'error');
                    return;
                }
                
                logMessage('video-log', `Checking if video exists: ${videoId}`);
                
                fetch(`/trellis/check-media-exists/${videoId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.video.exists) {
                            logMessage('video-log', `Video found: ${data.video.path}`, 'success');
                        } else {
                            logMessage('video-log', 'Video not found in any search location', 'error');
                            logMessage('video-log', `Searched in: ${data.video.searchedLocations.join(', ')}`, 'info');
                        }
                    })
                    .catch(error => {
                        logMessage('video-log', `Error checking video: ${error}`, 'error');
                    });
            });
            
            // Troubleshooting
            const testDirBtn = document.getElementById('test-directories-btn');
            const testCorsBtn = document.getElementById('test-cors-btn');
            const directoriesList = document.getElementById('directories');
            
            // Test search directories
            testDirBtn.addEventListener('click', () => {
                logMessage('troubleshoot-log', 'Testing search directories...');
                
                fetch('/trellis/check-media-exists/test')
                    .then(response => response.json())
                    .then(data => {
                        // Get unique directories from both model and video searches
                        const allDirs = [...new Set([
                            ...(data.model.searchedLocations || []),
                            ...(data.video.searchedLocations || [])
                        ])];
                        
                        if (allDirs.length === 0) {
                            logMessage('troubleshoot-log', 'No search directories found or accessible', 'error');
                        } else {
                            logMessage('troubleshoot-log', `Found ${allDirs.length} search directories`, 'success');
                            
                            // Update directories list
                            directoriesList.innerHTML = '';
                            allDirs.forEach(dir => {
                                const item = document.createElement('li');
                                item.textContent = dir;
                                directoriesList.appendChild(item);
                            });
                        }
                    })
                    .catch(error => {
                        logMessage('troubleshoot-log', `Error testing directories: ${error}`, 'error');
                    });
            });
            
            // Test CORS
            testCorsBtn.addEventListener('click', () => {
                logMessage('troubleshoot-log', 'Testing CORS headers...');
                
                // Create a test with preflight
                const testFetch = fetch('/trellis/model/test-cors', {
                    method: 'OPTIONS',
                    headers: {
                        'Origin': window.location.origin,
                        'Access-Control-Request-Method': 'GET'
                    }
                });
                
                testFetch.then(response => {
                    const corsHeaders = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
                    };
                    
                    if (corsHeaders['Access-Control-Allow-Origin']) {
                        logMessage('troubleshoot-log', 'CORS headers are properly set:', 'success');
                        Object.entries(corsHeaders).forEach(([key, value]) => {
                            if (value) {
                                logMessage('troubleshoot-log', `${key}: ${value}`);
                            }
                        });
                    } else {
                        logMessage('troubleshoot-log', 'CORS headers are not properly set', 'error');
                    }
                })
                .catch(error => {
                    logMessage('troubleshoot-log', `Error testing CORS: ${error}`, 'error');
                });
            });
            
            // Run initial tests
            window.addEventListener('load', () => {
                testDirBtn.click();
                
                // Fill with the test ID if provided
                const testId = 'cbecf79b-beee-469e-81fe-0ff63d966d4b';
                modelIdInput.value = testId;
                videoIdInput.value = testId;
                
                logMessage('troubleshoot-log', 'Debug viewer loaded. Use the controls above to test your media files.');
                logMessage('troubleshoot-log', `Test ID populated: ${testId}`);
            });
        </script>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")

    
    # If video not found
    logger.warning(f"Video {video_id} not found, searched in: {download_dirs}")
    return web.Response(
        status=404, 
        text=json.dumps({
            "error": f"Video {video_id} not found", 
            "search_paths": [f"{d}/{p.format(e)}" for d in download_dirs for p in patterns for e in extensions]
        }),
        content_type="application/json",
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
        }
    )

@server.PromptServer.instance.routes.get("/trellis/model/{model_id}")
async def get_trellis_model(request):
    """Serve 3D model file by ID with proper CORS and caching headers"""
    model_id = request.match_info["model_id"]
    logger.info(f"Model request for ID: {model_id}")
    
    # Get optional query parameters
    try:
        # Get cache busting and cross-origin parameters
        cache_bust = request.query.get('cache_bust', '')
        allow_origin = request.headers.get('Origin', '*')
    except Exception as e:
        logger.warning(f"Error parsing query parameters: {e}")
        cache_bust = ''
        allow_origin = '*'
    
    # List of possible extensions to check
    extensions = ['.glb', '.gltf']
    
    # List of possible naming patterns
    patterns = [
        f"{model_id}_output{{}}", 
        f"{model_id}{{}}"
    ]
    
    # Search for the model with caching
    model_path = find_file(model_id, patterns, extensions, 'model')
    
    if model_path:
        # Determine content type based on extension
        ext = os.path.splitext(model_path)[1].lower()
        content_type = "model/gltf-binary" if ext == ".glb" else "model/gltf+json"
        
        # Return with proper CORS and caching headers
        return web.FileResponse(
            model_path,
            headers={
                "Content-Type": content_type,
                "Access-Control-Allow-Origin": allow_origin,
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Requested-With",
                "Cache-Control": "max-age=3600",  # 1 hour cache
                "X-File-Path": model_path  # For debugging
            }
        )
    
    # If model not found
    logger.warning(f"Model {model_id} not found, searched in: {download_dirs}")
    return web.Response(
        status=404, 
        text=json.dumps({
            "error": f"Model {model_id} not found", 
            "search_paths": [f"{d}/{p.format(e)}" for d in download_dirs for p in patterns for e in extensions]
        }),
        content_type="application/json",
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
        }
    )
        for pattern in patterns:
            for ext in extensions:
                path = os.path.join(directory