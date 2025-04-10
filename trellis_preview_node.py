import os
import base64
import json
from server import PromptServer

class TrellisPreviewNode:
    """Node that previews Trellis 3D models and videos directly in the ComfyUI interface"""
    
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
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "preview_file"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def preview_file(self, file_path, file_type="auto", display_width=800, display_height=600):
        if not file_path or not os.path.exists(file_path):
            return {"ui": {"error": f"File not found: {file_path}"}}
        
        # Auto-detect file type if needed
        if file_type == "auto":
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.glb', '.gltf']:
                file_type = "model"
            elif ext in ['.mp4', '.webm', '.mov']:
                file_type = "video"
            else:
                return {"ui": {"error": f"Unsupported file type: {ext}"}}
        
        # Register file for preview
        preview_id = self._register_preview_file(file_path, file_type)
        
        # Return data for custom UI
        return {
            "ui": {
                "preview": {
                    "type": file_type,
                    "id": preview_id,
                    "width": display_width,
                    "height": display_height
                }
            }
        }
    
    def _register_preview_file(self, file_path, file_type):
        """Register file for preview and return a unique ID"""
        # Create a unique ID
        preview_id = f"preview_{base64.urlsafe_b64encode(os.path.abspath(file_path).encode()).decode()}"
        
        # Store mapping in server instance
        if not hasattr(PromptServer.instance, 'trellis_previews'):
            PromptServer.instance.trellis_previews = {}
        
        PromptServer.instance.trellis_previews[preview_id] = {
            "path": os.path.abspath(file_path),
            "type": file_type
        }
        
        return preview_id


# Add custom web routes
@PromptServer.instance.routes.get("/trellis/preview/{preview_id}")
async def get_preview_info(request):
    """Get preview information"""
    preview_id = request.match_info["preview_id"]
    
    if not hasattr(PromptServer.instance, 'trellis_previews'):
        return web.json_response({"error": "Preview registry not found"}, status=404)
    
    preview_data = PromptServer.instance.trellis_previews.get(preview_id)
    if not preview_data:
        return web.json_response({"error": "Preview not found"}, status=404)
    
    return web.json_response({
        "type": preview_data["type"],
        "url": f"/trellis/file/{preview_id}"
    })

@PromptServer.instance.routes.get("/trellis/file/{preview_id}")
async def get_preview_file(request):
    """Get the actual file"""
    preview_id = request.match_info["preview_id"]
    
    if not hasattr(PromptServer.instance, 'trellis_previews'):
        return web.Response(status=404, text="Preview registry not found")
    
    preview_data = PromptServer.instance.trellis_previews.get(preview_id)
    if not preview_data:
        return web.Response(status=404, text="Preview not found")
    
    file_path = preview_data["path"]
    
    # Determine content type
    content_type = "application/octet-stream"
    if preview_data["type"] == "model":
        content_type = "model/gltf-binary"
    elif preview_data["type"] == "video":
        content_type = "video/mp4"
    
    return web.FileResponse(file_path, headers={"Content-Type": content_type})

# Create the client-side code (this would go in a separate JS file)
js_code = """
import { app } from "../../scripts/app.js";

// Register the custom preview node
app.registerExtension({
    name: "Trellis.Preview",
    async setup() {
        // Register a custom node component
        app.ui.nodeCanvasRecreated.addEventListener(() => {
            document.querySelectorAll(".trellis-preview-container").forEach(container => {
                const previewId = container.dataset.previewId;
                const previewType = container.dataset.previewType;
                
                if (previewType === "model") {
                    setupModelPreview(container, previewId);
                } else if (previewType === "video") {
                    setupVideoPreview(container, previewId);
                }
            });
        });
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "TrellisPreviewNode") {
            // Add custom widget
            nodeType.prototype.onNodeCreated = function() {
                // Create preview container
                this.previewContainer = document.createElement("div");
                this.previewContainer.className = "trellis-preview-container";
                this.previewContainer.style.width = "100%";
                this.previewContainer.style.height = "400px";
                this.previewContainer.style.backgroundColor = "#222";
                this.previewContainer.style.borderRadius = "8px";
                this.previewContainer.style.overflow = "hidden";
                this.previewContainer.style.display = "flex";
                this.previewContainer.style.justifyContent = "center";
                this.previewContainer.style.alignItems = "center";
                this.previewContainer.style.color = "#888";
                this.previewContainer.innerHTML = "No preview available";
                
                // Add to node
                this.widgets.push({
                    type: "preview",
                    name: "preview",
                    container: this.previewContainer,
                    draw: function(ctx, node, widget_width, y, widget_height) {
                        return widget_height;
                    }
                });
                
                // Set a larger size for this node
                this.size = [400, 500];
            };
            
            // Handle widget updates
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                if (onExecuted) {
                    onExecuted.apply(this, arguments);
                }
                
                // Update preview if we have UI data
                if (message.ui && message.ui.preview) {
                    const preview = message.ui.preview;
                    
                    this.previewContainer.dataset.previewId = preview.id;
                    this.previewContainer.dataset.previewType = preview.type;
                    
                    if (preview.type === "model") {
                        setupModelPreview(this.previewContainer, preview.id);
                    } else if (preview.type === "video") {
                        setupVideoPreview(this.previewContainer, preview.id);
                    }
                }
            };
        }
    }
});

// Set up 3D model preview using Three.js
async function setupModelPreview(container, previewId) {
    // Clear container
    container.innerHTML = "Loading 3D model...";
    
    // Get model URL
    const response = await fetch(`/trellis/preview/${previewId}`);
    if (!response.ok) {
        container.innerHTML = "Error loading model preview";
        return;
    }
    
    const data = await response.json();
    const modelUrl = data.url;
    
    // Load Three.js dynamically (would be pre-loaded in a real implementation)
    await loadScript("https://cdnjs.cloudflare.com/ajax/libs/three.js/r132/three.min.js");
    await Promise.all([
        loadScript("https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.min.js"),
        loadScript("https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/GLTFLoader.min.js")
    ]);
    
    // Clear container again
    container.innerHTML = "";
    
    // Create Three.js scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x222222);
    
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 1, 5);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.outputEncoding = THREE.sRGBEncoding;
    container.appendChild(renderer.domElement);
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(1, 2, 3);
    scene.add(directionalLight);
    
    // Add orbit controls
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = true;
    
    // Load the model
    const loader = new THREE.GLTFLoader();
    loader.load(
        modelUrl,
        (gltf) => {
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
        },
        undefined,
        (error) => {
            console.error('Error loading model:', error);
            container.innerHTML = "Error loading model";
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
    const observer = new ResizeObserver(() => {
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height);
    });
    
    observer.observe(container);
}

// Set up video preview
function setupVideoPreview(container, previewId) {
    // Clear container
    container.innerHTML = "Loading video...";
    
    // Get video URL
    fetch(`/trellis/preview/${previewId}`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to get preview info");
            return response.json();
        })
        .then(data => {
            // Create video element
            container.innerHTML = "";
            
            const video = document.createElement("video");
            video.style.width = "100%";
            video.style.height = "100%";
            video.style.objectFit = "contain";
            video.controls = true;
            video.autoplay = true;
            video.loop = true;
            video.src = data.url;
            
            container.appendChild(video);
        })
        .catch(error => {
            console.error("Error setting up video preview:", error);
            container.innerHTML = "Error loading video preview";
        });
}

// Helper to load scripts
function loadScript(url) {
    return new Promise((resolve, reject) => {
        // Check if already loaded
        if (document.querySelector(`script[src="${url}"]`)) {
            resolve();
            return;
        }
        
        const script = document.createElement("script");
        script.src = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}
"""

# Create the extension js file
extension_dir = os.path.join("web", "extensions", "trellis-preview")
os.makedirs(extension_dir, exist_ok=True)

with open(os.path.join(extension_dir, "trellis-preview.js"), "w") as f:
    f.write(js_code)

# Register node
NODE_CLASS_MAPPINGS = {
    "TrellisPreviewNode": TrellisPreviewNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisPreviewNode": "Preview 3D"
}