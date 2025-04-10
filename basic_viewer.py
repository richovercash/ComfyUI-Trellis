import os
import logging
import shutil
import time

logger = logging.getLogger('TrellisBasicViewer')

class TrellisSimpleViewerNode:
    """Basic viewer node for Trellis 3D models"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "glb_path": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("viewer_path",)
    FUNCTION = "process"  # This needs to match your actual method name
    CATEGORY = "Trellis"
    OUTPUT_NODE = True

    # Simple viewer    
    # def process(self, glb_path):  # Method name must match FUNCTION value
    #     """Create a basic viewer for the 3D model"""
    #     try:
    #         logger.info(f"Processing GLB path: {glb_path}")
            
    #         if not glb_path or not os.path.exists(glb_path):
    #             logger.error(f"GLB file not found: {glb_path}")
    #             return "File not found"
            
    #         # Create a web-accessible copy
    #         web_dir = os.path.join("output", "trellis_models")
    #         os.makedirs(web_dir, exist_ok=True)
            
    #         # Create a unique filename
    #         filename = f"model_{int(time.time())}.glb"
    #         web_path = os.path.join(web_dir, filename)
            
    #         # Copy the file
    #         shutil.copy2(glb_path, web_path)
    #         logger.info(f"Copied model to web-accessible path: {web_path}")
            
    #         # Return the web path
    #         return web_path
    #     except Exception as e:
    #         logger.error(f"Error creating viewer: {e}")
    #         return str(e)


    def process(self, glb_path):
        try:
            logger.info(f"Processing GLB path: {glb_path}")
            
            if not glb_path or not os.path.exists(glb_path):
                logger.error(f"GLB file not found: {glb_path}")
                return "File not found"
            
            # Create a web-accessible copy
            web_dir = os.path.join("output", "trellis_models")
            os.makedirs(web_dir, exist_ok=True)
            
            # Create a unique filename
            filename = f"model_{int(time.time())}.glb"
            web_path = os.path.join(web_dir, filename)
            
            # Copy the file
            shutil.copy2(glb_path, web_path)
            logger.info(f"Copied model to web-accessible path: {web_path}")
            
            # Also create a special HTML viewer that can be opened directly
            viewer_dir = os.path.join("output", "trellis_viewers")
            os.makedirs(viewer_dir, exist_ok=True)
            
            viewer_filename = f"viewer_{int(time.time())}.html"
            viewer_path = os.path.join(viewer_dir, viewer_filename)
            
            # Get the relative path from viewer to model
            rel_path = os.path.relpath(web_path, os.path.dirname(viewer_path))
            rel_path = rel_path.replace('\\', '/')
            
            # Create a minimal viewer HTML
            html_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <title>Trellis Model Viewer</title>
                <style>body {{ margin: 0; }}</style>
                <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/build/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/GLTFLoader.js"></script>
            </head>
            <body>
                <div id="info" style="position:absolute;top:10px;left:10px;color:white;background:rgba(0,0,0,0.5);padding:5px;">
                    Model path: {rel_path}<br>
                    <a href="{rel_path}" download style="color:cyan;">Download Model</a>
                </div>
                <script>
                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0x222222);
                    
                    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                    camera.position.z = 5;
                    
                    const renderer = new THREE.WebGLRenderer();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    document.body.appendChild(renderer.domElement);
                    
                    const controls = new THREE.OrbitControls(camera, renderer.domElement);
                    controls.enableDamping = true;
                    
                    const light = new THREE.AmbientLight(0xffffff, 0.5);
                    scene.add(light);
                    
                    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
                    dirLight.position.set(1, 1, 1);
                    scene.add(dirLight);
                    
                    const loader = new THREE.GLTFLoader();
                    loader.load('{rel_path}', function(gltf) {{
                        const model = gltf.scene;
                        
                        // Center and scale model
                        const box = new THREE.Box3().setFromObject(model);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const scale = 2.0 / maxDim;
                        
                        model.position.x = -center.x * scale;
                        model.position.y = -center.y * scale;
                        model.position.z = -center.z * scale;
                        model.scale.set(scale, scale, scale);
                        
                        scene.add(model);
                        console.log('Model loaded successfully');
                    }}, 
                    function(xhr) {{
                        console.log((xhr.loaded / xhr.total * 100) + '% loaded');
                    }},
                    function(error) {{
                        console.error('Error loading model:', error);
                        document.getElementById('info').innerHTML += '<br><span style="color:red;">Error loading model: ' + error.message + '</span>';
                    }});
                    
                    function animate() {{
                        requestAnimationFrame(animate);
                        controls.update();
                        renderer.render(scene, camera);
                    }}
                    
                    animate();
                    
                    window.addEventListener('resize', function() {{
                        camera.aspect = window.innerWidth / window.innerHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(window.innerWidth, window.innerHeight);
                    }});
                </script>
            </body>
            </html>
            """
            
            # Write the viewer HTML
            with open(viewer_path, 'w') as f:
                f.write(html_content)
                
            logger.info(f"Created viewer HTML at: {viewer_path}")
            
            # Return the web path to the model
            return web_path
        except Exception as e:
            logger.error(f"Error creating viewer: {e}")
            return str(e)

# Export node definitions
NODE_CLASS_MAPPINGS = {
    "TrellisSimpleViewerNode": TrellisSimpleViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisSimpleViewerNode": "Trellis Simple GLB Viewer"
}