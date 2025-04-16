import os
import server
from aiohttp import web

# Get the directory where this file is located
base_path = os.path.dirname(os.path.realpath(__file__))
trellis_downloads_dir = os.path.join(os.getcwd(), "trellis_downloads")


@server.PromptServer.instance.routes.get("/trellis/video/{video_id}")
async def get_trellis_video(request):
    video_id = request.match_info["video_id"]
    
    # Search for the video in multiple possible directories
    search_paths = [
        os.path.join(trellis_downloads_dir, f"{video_id}_output.mp4"),
        os.path.join(trellis_downloads_dir, f"{video_id}_output.webm"),
        os.path.join(trellis_downloads_dir, f"{video_id}_output.mov"),
        # Add other possible directories if needed
    ]
    
    for video_path in search_paths:
        if os.path.exists(video_path):
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
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )
    
    # If video not found
    return web.Response(status=404, text=f"Video {video_id} not found")
    
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
    ext = os.path.splitext(model_path)[1].lower() if model_path else ".glb"
    content_type = "model/gltf-binary" if ext == ".glb" else "model/gltf+json"
    
    return web.Response(text=html, content_type="text/html", eaders={
                    "Content-Type": content_type,
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "Content-Type"
                })

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

@server.PromptServer.instance.routes.get("/test-video/{video_id}")
async def test_video(request):
    video_id = request.match_info["video_id"]
    html = f"""<!DOCTYPE html>
    <html><body style="margin:0; background:#000;">
        <video controls autoplay style="width:100%; height:100vh;">
            <source src="/trellis/video/{video_id}" type="video/mp4">
        </video>
    </body></html>
    """
    return web.Response(text=html, content_type="text/html")

@server.PromptServer.instance.routes.get("/trellis/debug-viewer")
async def debug_viewer(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trellis Model Debugger</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body { margin: 0; }
            canvas { display: block; }
            #info {
                position: absolute;
                top: 10px;
                left: 10px;
                color: white;
                background: rgba(0,0,0,0.5);
                padding: 5px;
            }
        </style>
    </head>
    <body>
        <div id="info">Loading...</div>
        <script>
            // Create scene, camera, renderer
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x222222);
            
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
            camera.position.z = 5;
            
            const renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // Add lights
            const light = new THREE.AmbientLight(0xffffff, 10);
            scene.add(light);
            
            const dirLight = new THREE.DirectionalLight(0xffffff, 10);
            dirLight.position.set(1, 1, 1);
            scene.add(dirLight);
            
            // Add controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            
            // Load model - change this to your model ID
            const modelId = '840c973e-f31e-4335-8bfe-4c58d41cecd8';
            const loader = new THREE.GLTFLoader();
            
            document.getElementById('info').textContent = 'Loading model...';
            
            loader.load(
                `/trellis/view-model/${modelId}`,
                (gltf) => {
                    // Model loaded successfully
                    scene.add(gltf.scene);
                    
                    // Scale and center
                    const box = new THREE.Box3().setFromObject(gltf.scene);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    
                    // Center model
                    gltf.scene.position.x = -center.x;
                    gltf.scene.position.y = -center.y;
                    gltf.scene.position.z = -center.z;
                    
                    // Scale model
                    const maxDim = Math.max(size.x, size.y, size.z);
                    if (maxDim > 0) {
                        const scale = 2 / maxDim;
                        gltf.scene.scale.set(scale, scale, scale);
                    }
                    
                    document.getElementById('info').textContent = 'Model loaded successfully';
                    setTimeout(() => {
                        document.getElementById('info').style.opacity = 0;
                        document.getElementById('info').style.transition = 'opacity 1s';
                    }, 2000);
                },
                (progress) => {
                    const percent = (progress.loaded / progress.total * 100).toFixed(2);
                    document.getElementById('info').textContent = `Loading: ${percent}%`;
                },
                (error) => {
                    document.getElementById('info').textContent = `Error loading model: ${error.message}`;
                    document.getElementById('info').style.color = 'red';
                }
            );
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                renderer.render(scene, camera);
            }
            animate();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')


# Add these routes to webserver.py

@server.PromptServer.instance.routes.get("/trellis/embed/model/{model_id}")
async def embed_model_viewer(request):
    model_id = request.match_info["model_id"]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Embedded Model Viewer</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: #222; }}
            #container {{ width: 100%; height: 100vh; }}
        </style>
    </head>
    <body>
        <div id="container"></div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r132/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/GLTFLoader.min.js"></script>
        
        <script>
            // Simplified model viewer specifically for embedding
            const container = document.getElementById('container');
            
            // Create scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x222222);
            
            // Setup camera
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 1, 3);
            
            // Setup renderer
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);
            
            // Setup controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 10);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(1, 2, 3);
            scene.add(directionalLight);
            
            // Load the model
            const loader = new THREE.GLTFLoader();
            loader.load(
                '/trellis/model/{model_id}',
                (gltf) => {{
                    const model = gltf.scene;
                    scene.add(model);
                    
                    // Center and scale the model
                    const box = new THREE.Box3().setFromObject(model);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    
                    const maxDim = Math.max(size.x, size.y, size.z);
                    if (maxDim > 0) {{
                        const scale = 2.0 / maxDim;
                        model.scale.set(scale, scale, scale);
                        model.position.x = -center.x * scale;
                        model.position.y = -center.y * scale;
                        model.position.z = -center.z * scale;
                    }}
                    
                    // Reset camera
                    camera.position.set(0, 1, 3);
                    controls.target.set(0, 0, 0);
                    controls.update();
                    
                    // Tell parent we're ready
                    window.parent.postMessage({{ type: 'modelLoaded', id: '{model_id}' }}, '*');
                }},
                (xhr) => {{
                    const percent = Math.round((xhr.loaded / xhr.total) * 100);
                    window.parent.postMessage({{ type: 'loadProgress', id: '{model_id}', percent: percent }}, '*');
                }},
                (error) => {{
                    console.error('Error loading model:', error);
                    window.parent.postMessage({{ type: 'loadError', id: '{model_id}', error: error.message }}, '*');
                }}
            );
            
            // Handle window resize
            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
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
    ext = os.path.splitext(model_path)[1].lower() if model_path else ".glb"
    content_type = "model/gltf-binary" if ext == ".glb" else "model/gltf+json"
    
    return web.Response(text=html, content_type="text/html", headers={
                    "Content-Type": content_type,
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "Content-Type"
                })

@server.PromptServer.instance.routes.get("/trellis/embed/video/{video_id}")
async def embed_video_viewer(request):
    video_id = request.match_info["video_id"]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Embedded Video Player</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: #222; }}
            #container {{ display: flex; justify-content: center; align-items: center; height: 100vh; }}
            video {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        </style>
    </head>
    <body>
        <div id="container">
            <video id="player" controls>
                <source src="/trellis/video/{video_id}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        
        <script>
            const player = document.getElementById('player');
            
            // Send messages to parent when video events occur
            player.addEventListener('loadstart', () => {{
                window.parent.postMessage({{ type: 'videoLoadStart', id: '{video_id}' }}, '*');
            }});
            
            player.addEventListener('canplay', () => {{
                window.parent.postMessage({{ type: 'videoCanPlay', id: '{video_id}' }}, '*');
            }});
            
            player.addEventListener('error', () => {{
                window.parent.postMessage({{ 
                    type: 'videoError', 
                    id: '{video_id}', 
                    error: player.error ? player.error.message : 'Unknown error'
                }}, '*');
            }});
        </script>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")



@server.PromptServer.instance.routes.get("/trellis/model/{model_id}")
async def get_trellis_model(request):
    model_id = request.match_info["model_id"]
    
    # Search for the model in multiple possible directories
    search_paths = [
        os.path.join(trellis_downloads_dir, f"{model_id}_output.glb"),
        os.path.join(trellis_downloads_dir, f"{model_id}_output.gltf"),
        # Add other possible directories if needed
    ]
    
    for model_path in search_paths:
        if os.path.exists(model_path):
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
                    "Access-Control-Max-Age": "86400"  # 24 hours
                }
            )
    
    # If model not found
    return web.Response(
        status=404, 
        text=f"Model {model_id} not found",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-Requested-With"
        }
    )

# Add OPTIONS handler for the model endpoint to properly support CORS preflight requests
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
    media_type = request.match_info["type"]  # "model" or "video"
    media_id = request.match_info["id"]
    
    # Log the request
    print(f"Trellis simple viewer request: type={media_type}, id={media_id}")
    
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
            </style>
        </head>
        <body>
            <div id="status" style="position:absolute; top:10px; left:10px; color:white; background:rgba(0,0,0,0.5); padding:5px;">Loading...</div>
            
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
                
                const renderer = new THREE.WebGLRenderer();
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.body.appendChild(renderer.domElement);
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0xffffff, 20);
                scene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 10);
                directionalLight.position.set(1, 1, 1);
                scene.add(directionalLight);
                
                // Controls
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                
                // Load model with error handling
                const modelUrl = "/trellis/model/{id}";
                console.log("Loading model from:", modelUrl);
                
                // Add a test cube to show if model loading fails
                const geometry = new THREE.BoxGeometry(1, 1, 1);
                const material = new THREE.MeshStandardMaterial({{ 
                    color: 0x00a0ff,
                    metalness: 0.3,
                    roughness: 0.4
                }});
                const cube = new THREE.Mesh(geometry, material);
                cube.visible = false;
                scene.add(cube);
                
                const loader = new THREE.GLTFLoader();
                loader.load(
                    modelUrl,
                    (gltf) => {{
                        console.log("Model loaded successfully");
                        
                        scene.add(gltf.scene);
                        
                        // Center and scale
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
                        
                        document.getElementById('status').textContent = 'Model loaded';
                        setTimeout(() => {{
                            document.getElementById('status').style.opacity = 0;
                        }}, 2000);
                    }},
                    (xhr) => {{
                        const percent = Math.round((xhr.loaded / xhr.total) * 100);
                        document.getElementById('status').textContent = `Loading: ${{percent}}%`;
                    }},
                    (error) => {{
                        console.error('Error loading model:', error);
                        document.getElementById('status').textContent = `Error: ${{error.message}}`;
                        document.getElementById('status').style.color = 'red';
                        
                        // Show the test cube if model loading fails
                        cube.visible = true;
                        
                        // Animate the cube to indicate something is still working
                        function animateCube() {{
                            cube.rotation.x += 0.01;
                            cube.rotation.y += 0.01;
                        }}
                        
                        // Override the animate function
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
                
                // Handle CORS errors
                window.addEventListener('error', (e) => {{
                    if (e.message.includes('CORS') || e.message.includes('cross-origin')) {{
                        console.error('CORS error detected:', e);
                        document.getElementById('status').textContent = 'CORS error detected - check console';
                        document.getElementById('status').style.color = 'red';
                    }}
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
                video {{ max-width: 100%; max-height: 100%; }}
            </style>
        </head>
        <body>
            <div id="status" style="position:absolute; top:10px; left:10px; color:white; background:rgba(0,0,0,0.5); padding:5px;">Loading video...</div>
            <video controls autoplay>
                <source src="/trellis/video/{id}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            <script>
                console.log("Simple video player initializing...");
                
                const video = document.querySelector('video');
                const status = document.getElementById('status');
                
                video.addEventListener('loadeddata', () => {{
                    console.log("Video loaded successfully");
                    status.textContent = "Video loaded";
                    setTimeout(() => {{
                        status.style.opacity = 0;
                    }}, 2000);
                }});
                
                video.addEventListener('error', (e) => {{
                    console.error("Video loading error:", e);
                    status.textContent = `Error: ${{video.error ? video.error.message : 'Unknown error'}}`;
                    status.style.color = 'red';
                    
                    if (video.error && video.error.message.includes('CORS')) {{
                        console.error('CORS error detected:', video.error);
                        status.textContent = 'CORS error detected - check console';
                    }}
                }});
            </script>
        </body>
        </html>
        """.format(id=media_id)
    
    # Return with necessary CORS headers - this line was likely missing or misplaced
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
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }}
            .test-container {{ margin-bottom: 30px; }}
            .viewer {{ width: 400px; height: 300px; border: 1px solid #ccc; border-radius: 8px; overflow: hidden; }}
            h2 {{ margin-top: 0; }}
            .controls {{ margin: 10px 0; }}
            input {{ padding: 5px; width: 300px; }}
            button {{ padding: 5px 10px; }}
            .direct-link {{ margin-top: 5px; }}
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
                iframe.src = `/trellis/simple-viewer/model/${modelId}`;
                
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
                iframe.src = `/trellis/simple-viewer/video/${videoId}`;
                
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
                
                const modelUrl = `/trellis/model/${modelId}`;
                
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
        </script>
    </body>
    </html>
    """
    
    return web.Response(text=html, content_type="text/html")