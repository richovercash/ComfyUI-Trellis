import os
import json
import logging
import base64
import mimetypes
from aiohttp import web
from server import PromptServer

logger = logging.getLogger('TrellisInlineViewer')

class TrellisInlineViewerNode:
    """Node that displays Trellis 3D models and videos directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": ""}),
                "file_type": (["auto", "model", "video"], {"default": "auto"}),
            },
            "optional": {
                "display_width": ("INT", {"default": 800, "min": 400, "max": 1920}),
                "display_height": ("INT", {"default": 600, "min": 300, "max": 1080}),
                "background_color": (["#000000", "#222222", "#444444", "#FFFFFF"], {"default": "#222222"}),
                "auto_rotate": (["enabled", "disabled"], {"default": "enabled"}),
                "autoplay": (["enabled", "disabled"], {"default": "enabled"}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "display_content"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def display_content(self, file_path, file_type="auto", display_width=800, display_height=600, 
                     background_color="#222222", auto_rotate="enabled", autoplay="enabled"):
        try:
            if not file_path or not os.path.exists(file_path):
                return {"ui": {"error": f"File not found: {file_path}"}}
            
            # Determine file type if set to auto
            if file_type == "auto":
                extension = os.path.splitext(file_path)[1].lower()
                if extension in ['.glb', '.gltf']:
                    file_type = "model"
                elif extension in ['.mp4', '.webm', '.mov']:
                    file_type = "video"
                else:
                    return {"ui": {"error": f"Unsupported file type: {extension}"}}
            
            # Register the file with our file server
            relative_path = self._register_file(file_path)
            
            # Create a payload for the frontend
            payload = {
                "file_type": file_type,
                "file_path": relative_path,
                "display_width": display_width,
                "display_height": display_height,
                "background_color": background_color,
                "auto_rotate": auto_rotate == "enabled",
                "autoplay": autoplay == "enabled",
                "viewer_id": f"trellis_viewer_{hash(file_path) % 10000}"
            }
            
            # Return data to be displayed in ComfyUI
            return {"ui": {"trellis_viewer": payload}}
            
        except Exception as e:
            logger.error(f"Error in TrellisInlineViewerNode: {e}")
            return {"ui": {"error": str(e)}}
    
    def _register_file(self, file_path):
        """Register a file to be served by the ComfyUI server"""
        # Generate a unique ID for this file
        file_id = base64.urlsafe_b64encode(os.path.abspath(file_path).encode()).decode()
        
        # Store the mapping of ID to actual file path
        if not hasattr(PromptServer.instance, 'trellis_files'):
            PromptServer.instance.trellis_files = {}
        
        PromptServer.instance.trellis_files[file_id] = os.path.abspath(file_path)
        
        # Return the relative path that the frontend will use
        return f"/trellis/file/{file_id}"

# Add routes to the server
@PromptServer.instance.routes.get("/trellis/file/{file_id}")
async def get_trellis_file(request):
    file_id = request.match_info["file_id"]
    
    # Get the actual file path
    if not hasattr(PromptServer.instance, 'trellis_files'):
        return web.Response(status=404, text="File registry not found")
    
    file_path = PromptServer.instance.trellis_files.get(file_id)
    if not file_path:
        return web.Response(status=404, text="File not found")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        if file_path.endswith('.glb'):
            content_type = 'model/gltf-binary'
    
    # Serve the file
    return web.FileResponse(file_path, headers={"Content-Type": content_type})

# Add custom JavaScript file to ComfyUI
WEB_DIRECTORY = "./web/extensions/trellis-viewer"
os.makedirs(WEB_DIRECTORY, exist_ok=True)

# Create the JavaScript file for the frontend component
with open(os.path.join(WEB_DIRECTORY, "trellis-viewer.js"), "w") as f:
    f.write("""
// TrellisViewer extension for ComfyUI
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Register the custom node component
app.registerExtension({
    name: "Trellis.InlineViewer",
    async init() {
        // Register a custom node component that will render the viewer
        app.registerNodeDef({
            name: "TrellisInlineViewer",
            category: "Trellis",
            uiComponent: {
                init(node, inputsData) {
                    // Create main container
                    const container = document.createElement("div");
                    container.style.width = "100%";
                    container.style.height = "100%";
                    container.style.overflow = "hidden";
                    container.style.backgroundColor = "#222";
                    container.style.display = "flex";
                    container.style.justifyContent = "center";
                    container.style.alignItems = "center";
                    
                    // Display placeholder text initially
                    container.innerHTML = "<div style='color:white;text-align:center;'>Waiting for file...</div>";
                    
                    // Store the container element for later updates
                    node.viewerContainer = container;
                    
                    return { element: container };
                },
                
                update(node, inputsData, outputsData) {
                    // Process the output from the node's execution
                    if (outputsData && outputsData.ui) {
                        const uiData = outputsData.ui;
                        
                        if (uiData.error) {
                            // Display error message
                            node.viewerContainer.innerHTML = `<div style='color:red;text-align:center;'>${uiData.error}</div>`;
                            return;
                        }
                        
                        if (uiData.trellis_viewer) {
                            const data = uiData.trellis_viewer;
                            
                            // Create the appropriate viewer based on file type
                            if (data.file_type === "model") {
                                this.createModelViewer(node.viewerContainer, data);
                            } else if (data.file_type === "video") {
                                this.createVideoPlayer(node.viewerContainer, data);
                            }
                        }
                    }
                },
                
                createModelViewer(container, data) {
                    // Load Three.js for model viewing
                    this.loadScripts(["https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"], () => {
                        this.loadScripts([
                            "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js",
                            "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"
                        ], () => {
                            // Clear the container
                            container.innerHTML = "";
                            
                            // Create the viewer ID and viewer element
                            const viewerId = data.viewer_id || "model_viewer";
                            const viewerElement = document.createElement("div");
                            viewerElement.id = viewerId;
                            viewerElement.style.width = "100%";
                            viewerElement.style.height = "100%";
                            
                            container.appendChild(viewerElement);
                            
                            // Initialize Three.js scene
                            const width = data.display_width || 800;
                            const height = data.display_height || 600;
                            
                            const scene = new THREE.Scene();
                            scene.background = new THREE.Color(data.background_color || "#222222");
                            
                            const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
                            camera.position.set(0, 0, 5);
                            
                            const renderer = new THREE.WebGLRenderer({ antialias: true });
                            renderer.setSize(width, height);
                            renderer.outputEncoding = THREE.sRGBEncoding;
                            
                            viewerElement.appendChild(renderer.domElement);
                            
                            // Add lights
                            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
                            scene.add(ambientLight);
                            
                            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
                            directionalLight.position.set(1, 2, 3);
                            scene.add(directionalLight);
                            
                            // Add orbit controls
                            const controls = new THREE.OrbitControls(camera, renderer.domElement);
                            controls.enableDamping = true;
                            controls.dampingFactor = 0.05;
                            controls.autoRotate = data.auto_rotate;
                            
                            // Load the model
                            const loader = new THREE.GLTFLoader();
                            loader.load(
                                data.file_path,
                                (gltf) => {
                                    const model = gltf.scene;
                                    
                                    // Auto-center and scale the model
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
                                },
                                (xhr) => {
                                    const percent = Math.round((xhr.loaded / xhr.total) * 100);
                                    viewerElement.innerHTML = `<div style='color:white;position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'>Loading: ${percent}%</div>`;
                                },
                                (error) => {
                                    viewerElement.innerHTML = `<div style='color:red;text-align:center;'>Error: ${error.message}</div>`;
                                }
                            );
                            
                            // Animation loop
                            function animate() {
                                requestAnimationFrame(animate);
                                controls.update();
                                renderer.render(scene, camera);
                            }
                            
                            animate();
                            
                            // Handle resize
                            const resizeObserver = new ResizeObserver(() => {
                                const width = viewerElement.clientWidth;
                                const height = viewerElement.clientHeight;
                                
                                camera.aspect = width / height;
                                camera.updateProjectionMatrix();
                                renderer.setSize(width, height);
                            });
                            
                            resizeObserver.observe(viewerElement);
                        });
                    });
                },
                
                createVideoPlayer(container, data) {
                    // Clear the container
                    container.innerHTML = "";
                    
                    // Create video element
                    const video = document.createElement("video");
                    video.style.width = "100%";
                    video.style.height = "100%";
                    video.style.objectFit = "contain";
                    video.controls = true;
                    video.autoplay = data.autoplay;
                    video.loop = true;
                    
                    // Add source
                    const source = document.createElement("source");
                    source.src = data.file_path;
                    source.type = "video/mp4";
                    
                    video.appendChild(source);
                    container.appendChild(video);
                    
                    // Error handling
                    video.addEventListener("error", () => {
                        container.innerHTML = `<div style='color:red;text-align:center;'>Error loading video</div>`;
                    });
                },
                
                loadScripts(urls, callback) {
                    let loaded = 0;
                    
                    urls.forEach(url => {
                        // Check if script is already loaded
                        if (document.querySelector(`script[src="${url}"]`)) {
                            loaded++;
                            if (loaded === urls.length) callback();
                            return;
                        }
                        
                        // Create script element
                        const script = document.createElement("script");
                        script.src = url;
                        script.async = true;
                        
                        script.onload = () => {
                            loaded++;
                            if (loaded === urls.length) callback();
                        };
                        
                        document.head.appendChild(script);
                    });
                    
                    // If no scripts to load, call callback immediately
                    if (urls.length === 0) callback();
                }
            }
        });
    }
});
""")

# Add node mappings
NODE_CLASS_MAPPINGS = {
    "TrellisInlineViewer": TrellisInlineViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisInlineViewer": "Trellis Inline Viewer"
}