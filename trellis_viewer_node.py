import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('TrellisViewer')

class TrellisModelViewerNode:
    """Node that generates an HTML viewer for Trellis 3D models"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "glb_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "background_color": (["#000000", "#222222", "#444444", "#FFFFFF", "gradient"], {"default": "#222222"}),
                "display_width": ("INT", {"default": 800, "min": 400, "max": 1920}),
                "display_height": ("INT", {"default": 600, "min": 300, "max": 1080}),
                "auto_rotate": (["enabled", "disabled"], {"default": "enabled"}),
                "camera_distance": ("FLOAT", {"default": 2.0, "min": 0.5, "max": 10.0, "step": 0.1}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("glb_path", "viewer_url", "viewer_path")
    FUNCTION = "create_viewer"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def create_viewer(self, glb_path, background_color="#222222", display_width=800, 
                     display_height=600, auto_rotate="enabled", camera_distance=2.0):
        """Create an HTML viewer for the 3D model"""
        try:
            # Make sure the path is absolute
            glb_path = os.path.abspath(glb_path)

            if not glb_path or not os.path.exists(glb_path):
                logger.error(f"GLB file not found: {glb_path}")
                return glb_path, "", ""
            
            # Extract model ID from path
            filename = os.path.basename(glb_path)
            model_id = filename.split("_")[0]
            viewer_url = f"/trellis/view-model/{model_id}"
            
            # Create a unique viewer filename
            viewer_dir = os.path.join("trellis_files", "viewers")
            os.makedirs(viewer_dir, exist_ok=True)
            
            viewer_filename = f"view_{os.path.basename(glb_path).replace('.glb', '')}.html"
            viewer_path = os.path.join(viewer_dir, viewer_filename)
            
            # For debugging
            logger.info(f"GLB Path: {glb_path}")
            logger.info(f"Model ID: {model_id}")
            logger.info(f"Viewer URL: {viewer_url}")
            
            return glb_path, viewer_url, viewer_path
            
        except Exception as e:
            logger.error(f"Error creating viewer: {e}")
            return glb_path, "", ""
    
    # Add to TrellisVideoPlayerNode class
    def ui(self, glb_path, viewer_html, viewer_path):
        # Extract model ID from path
        import os
        filename = os.path.basename(glb_path)
        model_id = filename.split("_")[0]
        
        # Return the direct URL to the viewer
        view_url = f"/trellis/view-model/{model_id}"
        
        return {"ui": {"viewer": {"type": "iframe", "url": view_url}}}

    def generate_three_js_viewer(self, model_path, background_color, width, height, 
                               auto_rotate, camera_distance):
        
        #     # Convert to file:// URL for local access
        # model_url_path = f"file://{os.path.abspath(model_path).replace('\\', '/')}"
        #         # Convert to absolute URL path (if running on a web server)
        # model_url_path = model_path.replace('\\', '/')
        

        """Generate HTML content for a Three.js viewer"""
        
        # Handle gradient background
        if background_color == "gradient":
            bg_style = "background: linear-gradient(to bottom, #1a2a6c, #b21f1f, #fdbb2d);"
            bg_color = "#000000"  # Fallback
        else:
            bg_style = f"background-color: {background_color};"
            bg_color = background_color
        


        html = f"""<!DOCTYPE html>

<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trellis 3D Model Viewer</title>
    <style>
        body {{ margin: 0; overflow: hidden; {bg_style} }}
        #viewer-container {{ width: 100%; height: 100%; position: absolute; }}
        #model-info {{ 
            position: absolute; 
            bottom: 10px; 
            left: 10px; 
            color: white; 
            background-color: rgba(0,0,0,0.5); 
            padding: 5px 10px; 
            border-radius: 5px;
            font-family: Arial, sans-serif;
        }}
        #loading {{ 
            position: absolute; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%);
            color: white;
            font-family: Arial, sans-serif;
            font-size: 18px;
            background-color: rgba(0,0,0,0.7);
            padding: 20px;
            border-radius: 10px;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r132/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dat-gui/0.7.7/dat.gui.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/GLTFLoader.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/DRACOLoader.min.js"></script>
</head>
<body>
    <div id="viewer-container"></div>
    <div id="model-info">Model: {os.path.basename(model_path)}</div>
    <div id="loading">Loading 3D model...</div>
    
    <script>
        // Configuration
        const config = {{
            modelPath: '{model_path}',
            backgroundColor: '{bg_color}',
            autoRotate: {auto_rotate},
            cameraDistance: {camera_distance},
            width: {width},
            height: {height}
        }};
        
        // Main viewer code
        let scene, camera, renderer, controls, model, mixer;
        let clock = new THREE.Clock();
        
        // Initialize the viewer
        function init() {{
            // Create scene
            scene = new THREE.Scene();
            if(config.backgroundColor.startsWith('#')) {{
                scene.background = new THREE.Color(config.backgroundColor);
            }}
            
            // Setup camera
            camera = new THREE.PerspectiveCamera(45, config.width / config.height, 0.1, 1000);
            camera.position.set(0, 1, config.cameraDistance);
            
            // Setup renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(config.width, config.height);
            renderer.outputEncoding = THREE.sRGBEncoding;
            renderer.physicallyCorrectLights = true;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.0;
            
            // Add renderer to DOM
            document.getElementById('viewer-container').appendChild(renderer.domElement);
            
            // Setup controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.autoRotate = config.autoRotate;
            controls.autoRotateSpeed = 0.5;
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(1, 2, 3);
            scene.add(directionalLight);
            
            const backLight = new THREE.DirectionalLight(0xffffff, 0.5);
            backLight.position.set(-1, 2, -3);
            scene.add(backLight);
            
            // Load the model
            loadModel();
            
            // Handle window resize
            window.addEventListener('resize', onWindowResize);
            
            // Setup GUI
            setupGUI();
        }}
        
        // Load the GLB model
        function loadModel() {{
            const loader = new THREE.GLTFLoader();
            const dracoLoader = new THREE.DRACOLoader();
            dracoLoader.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/libs/draco/');
            loader.setDRACOLoader(dracoLoader);
            
            loader.load(
                config.modelPath,
                function(gltf) {{
                    model = gltf.scene;
                    
                    // Center and scale the model
                    const box = new THREE.Box3().setFromObject(model);
                    const center = box.getCenter(new THREE.Vector3());
                    const size = box.getSize(new THREE.Vector3());
                    
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 1.0 / maxDim;
                    
                    model.position.x = -center.x * scale;
                    model.position.y = -center.y * scale;
                    model.position.z = -center.z * scale;
                    model.scale.set(scale, scale, scale);
                    
                    scene.add(model);
                    
                    // Handle animations if any
                    if (gltf.animations && gltf.animations.length) {{
                        mixer = new THREE.AnimationMixer(model);
                        const action = mixer.clipAction(gltf.animations[0]);
                        action.play();
                    }}
                    
                    // Hide loading message
                    document.getElementById('loading').style.display = 'none';
                }},
                function(xhr) {{
                    const percent = Math.round((xhr.loaded / xhr.total) * 100);
                    document.getElementById('loading').innerText = `Loading: ${{percent}}%`;
                }},
                function(error) {{
                    console.error('Error loading model:', error);
                    document.getElementById('loading').innerText = 'Error loading model';
                }}
            );
        }}
        
        // Handle window resize
        function onWindowResize() {{
            const container = document.getElementById('viewer-container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }}
        
        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            
            const delta = clock.getDelta();
            if (mixer) mixer.update(delta);
            
            controls.update();
            renderer.render(scene, camera);
        }}
        
        // Setup GUI for controls
        function setupGUI() {{
            const gui = new dat.GUI();
            gui.width = 250;
            
            const viewFolder = gui.addFolder('View Settings');
            viewFolder.add(controls, 'autoRotate').name('Auto Rotate');
            viewFolder.add(controls, 'autoRotateSpeed', 0, 5).name('Rotation Speed');
            
            const lightFolder = gui.addFolder('Lighting');
            const lightSettings = {{
                exposure: renderer.toneMappingExposure,
                ambientIntensity: 0.5,
                directionalIntensity: 1.0
            }};
            
            lightFolder.add(lightSettings, 'exposure', 0, 2).onChange(function(value) {{
                renderer.toneMappingExposure = value;
            }});
            
            // Open folders
            viewFolder.open();
            
            // Position GUI
            gui.domElement.style.position = 'absolute';
            gui.domElement.style.top = '10px';
            gui.domElement.style.right = '10px';
        }}
        
        // Initialize the viewer
        init();
        
        // Start animation loop
        animate();
        
        // Resize viewer to container
        function resizeToContainer() {{
            const container = document.getElementById('viewer-container');
            container.style.width = config.width + 'px';
            container.style.height = config.height + 'px';
            
            onWindowResize();
        }}
        
        // Call resize function
        resizeToContainer();
    </script>
</body>
</html>
"""
        return html
    
    def create_error_html(self, error_message):
        """Create an HTML error page"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Error Loading Model</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f0f0f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .error-container {{ background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 600px; }}
        h1 {{ color: #d32f2f; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow: auto; }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>Error Loading 3D Model</h1>
        <p>An error occurred while trying to load or display the model:</p>
        <pre>{error_message}</pre>
        <p>Please check that the model file exists and is a valid GLB format.</p>
    </div>
</body>
</html>
"""


class TrellisVideoPlayerNode:
    """Node that creates an HTML video player for Trellis video previews"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "display_width": ("INT", {"default": 800, "min": 320, "max": 1920}),
                "autoplay": (["enabled", "disabled"], {"default": "enabled"}),
                "loop": (["enabled", "disabled"], {"default": "enabled"}),
                "controls": (["enabled", "disabled"], {"default": "enabled"}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("video_path", "viewer_url", "viewer_path")
    FUNCTION = "create_player"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def create_player(self, video_path, display_width=800, autoplay="enabled", 
                    loop="enabled", controls="enabled"):
        """Create an HTML video player"""
        try:
            # Make sure the path is absolute
            video_path = os.path.abspath(video_path)

            if not video_path or not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return video_path, "", ""
                
            # Extract video ID from path
            filename = os.path.basename(video_path)
            video_id = filename.split("_")[0]
            viewer_url = f"/trellis/view-video/{video_id}"
            
            # Create a unique player filename
            player_dir = os.path.join("trellis_files", "players")
            os.makedirs(player_dir, exist_ok=True)
            
            player_filename = f"play_{os.path.basename(video_path).replace('.mp4', '')}.html"
            player_path = os.path.join(player_dir, player_filename)
            
            # For debugging
            logger.info(f"Video Path: {video_path}")
            logger.info(f"Video ID: {video_id}")
            logger.info(f"Viewer URL: {viewer_url}")
            
            return video_path, viewer_url, player_path
            
        except Exception as e:
            logger.error(f"Error creating video player: {e}")
            return video_path, "", ""
    
    def ui(self, video_path, viewer_url, viewer_path):
        """UI integration for the node"""
        return {"ui": {"viewer": {"type": "iframe", "url": viewer_url}}}
    
    def create_error_html(self, error_message):
        """Create an HTML error page"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Error Loading Video</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #1e1e1e; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
        .error-container {{ background-color: #2a2a2a; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.3); max-width: 600px; }}
        h1 {{ color: #ff5252; }}
        pre {{ background-color: #333; padding: 10px; border-radius: 3px; overflow: auto; }}
    </style>
</head>
<body>
    <div class="error-container">
        <h1>Error Loading Video</h1>
        <p>An error occurred while trying to load or display the video:</p>
        <pre>{error_message}</pre>
        <p>Please check that the video file exists and is a valid MP4 format.</p>
    </div>
</body>
</html>
"""


class TrellisViewNode:
    """Node that displays 3D models directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": ""}),
                "file_type": (["auto", "model", "video"], {"default": "auto"}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "preview_file"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def preview_file(self, file_path, file_type="auto"):
        if not file_path or not os.path.exists(file_path):
            return {"ui": {"status": "waiting"}}
        
        # Auto-detect file type if needed
        if file_type == "auto":
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.glb', '.gltf']:
                file_type = "model"
            elif ext in ['.mp4', '.webm', '.mov']:
                file_type = "video"
            else:
                return {"ui": {"status": "error", "message": f"Unsupported file type: {ext}"}}
        
        # Generate a unique file ID based on file path
        import hashlib
        file_hash = hashlib.md5(os.path.abspath(file_path).encode()).hexdigest()
        file_id = f"preview_{file_hash}"
        
        # Register file for serving
        from server import PromptServer
        if not hasattr(PromptServer.instance, 'trellis_files'):
            PromptServer.instance.trellis_files = {}
        
        PromptServer.instance.trellis_files[file_id] = {
            "path": os.path.abspath(file_path),
            "type": file_type,
            "mtime": os.path.getmtime(file_path)
        }
        
        # Return data for UI
        return {
            "ui": {
                "status": "ready",
                "preview": {
                    "file_id": file_id,
                    "file_type": file_type
                }
            }
        }



    


# Add these new node classes to the mappings
NODE_CLASS_MAPPINGS = {
    "TrellisModelViewerNode": TrellisModelViewerNode,
    "TrellisVideoPlayerNode": TrellisVideoPlayerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisModelViewerNode": "Trellis 3D Model Viewer",
    "TrellisVideoPlayerNode": "Trellis Video Player"
}
