// The correct way to import app and api in ComfyUI
import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

// Load Three.js from CDN directly
const script = document.createElement('script');
script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
document.head.appendChild(script);

console.log("Trellis viewer script loading...");

script.onload = () => {
    console.log("Three.js loaded successfully");
    // Load GLTFLoader after Three.js is loaded
    const gltfScript = document.createElement('script');
    gltfScript.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js';
    document.head.appendChild(gltfScript);

    // Load OrbitControls after GLTFLoader
    gltfScript.onload = () => {
        const orbitScript = document.createElement('script');
        orbitScript.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js';
        document.head.appendChild(orbitScript);
    };
};

// At the top of the file
const DEBUG = true;
function debug(...args) {
    if (DEBUG) {
        console.log("[Trellis]", ...args);
        // Send to backend for logging
        logToBackend("JavaScript", args);
    }
}

// Function to send logs to backend
async function logToBackend(source, data) {
    try {
        await api.fetchApi('/trellis/debug', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source: source,
                timestamp: new Date().toISOString(),
                data: data
            })
        });
    } catch (error) {
        console.error("Failed to send log to backend:", error);
    }
}

// Register Trellis viewer extension
app.registerExtension({
    name: "Trellis.MediaViewer",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        debug("beforeRegisterNodeDef called for", nodeData.name);
        
        // Handle both old and new model viewer nodes
        if (nodeData.name === "TrellisModelViewerNode" || nodeData.name === "TrellisModelViewer") {
            debug("Registering model viewer UI for", nodeData.name);
            
            // Override the node's prototype
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                
                // Make the node bigger
                this.size[1] = 300;
            };

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                console.log("Creating TrellisModelViewerNode");
                const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                // Create 3D viewer container
                const container = document.createElement("div");
                container.style.width = "100%";
                container.style.height = "280px";
                container.style.backgroundColor = "#222";
                container.style.borderRadius = "8px";
                container.style.overflow = "hidden";
                container.style.marginTop = "10px";
                
                // Initialize Three.js
                if (window.THREE) {
                    console.log("Three.js is available");
                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0x222222);
                    
                    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
                    camera.position.z = 5;
                    
                    const renderer = new THREE.WebGLRenderer({ antialias: true });
                    renderer.setSize(container.clientWidth, container.clientHeight);
                    container.appendChild(renderer.domElement);
                    
                    if (window.OrbitControls) {
                        console.log("OrbitControls is available");
                        const controls = new OrbitControls(camera, renderer.domElement);
                        controls.enableDamping = true;
                        this.threeControls = controls;
                    }
                    
                    // Add lighting
                    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
                    scene.add(ambientLight);
                    
                    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
                    directionalLight.position.set(5, 5, 5);
                    scene.add(directionalLight);
                    
                    // Animation loop
                    const animate = () => {
                        requestAnimationFrame(animate);
                        if (this.threeControls) this.threeControls.update();
                        renderer.render(scene, camera);
                    };
                    animate();
                    
                    // Store references
                    this.threeContainer = container;
                    this.threeScene = scene;
                    this.threeCamera = camera;
                    this.threeRenderer = renderer;
                } else {
                    console.error("Three.js not loaded!");
                    container.innerHTML = "Error: Three.js not loaded";
                }
                
                // Add widget
                this.addWidget("preview", "model_preview", "", () => {}, {
                    element: container,
                    serialize: false
                });
                
                return result;
            };

            // Handle model updates
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                debug("Model viewer executed with message:", message);
                
                try {
                    if (message?.ui?.model_path && window.THREE && window.GLTFLoader) {
                        const modelPath = message.ui.model_path;
                        debug("Raw model path:", modelPath);
                        
                        if (modelPath && this.threeScene) {
                            // Try loading directly first
                            const loader = new GLTFLoader();
                            loader.load(modelPath, 
                                (gltf) => {
                                    debug("Model loaded successfully");
                                    loadModelIntoScene(gltf, this);
                                },
                                (progress) => {
                                    const percent = (progress.loaded / progress.total * 100).toFixed(2);
                                    debug(`Loading progress: ${percent}%`);
                                },
                                (error) => {
                                    debug("Error loading directly, trying media path");
                                    const mediaPath = api.getMediaPath(modelPath);
                                    loader.load(mediaPath,
                                        (gltf) => {
                                            debug("Model loaded successfully (media path)");
                                            loadModelIntoScene(gltf, this);
                                        },
                                        undefined,
                                        (error) => {
                                            debug("Error loading from media path, trying viewer path");
                                            // Try the viewer path as last resort
                                            const modelId = getFileId(modelPath);
                                            if (modelId) {
                                                const viewerPath = `/trellis/view-model/${modelId}`;
                                                loader.load(viewerPath,
                                                    (gltf) => {
                                                        debug("Model loaded successfully (viewer path)");
                                                        loadModelIntoScene(gltf, this);
                                                    },
                                                    undefined,
                                                    (finalError) => {
                                                        console.error("All loading attempts failed:", {
                                                            direct: error,
                                                            media: error,
                                                            viewer: finalError
                                                        });
                                                    }
                                                );
                                            }
                                        }
                                    );
                                }
                            );
                        } else {
                            debug("Invalid model path or scene not initialized:", {
                                path: modelPath,
                                hasScene: !!this.threeScene
                            });
                        }
                    }
                    
                    if (onExecuted) {
                        return onExecuted.apply(this, arguments);
                    }
                } catch (error) {
                    console.error("Error in model viewer execution:", error);
                }
            };
        }

        // Handle both old and new video player nodes
        if (nodeData.name === "TrellisVideoPlayerNode") {
            debug("Registering video player UI");
            
            // Override the node's prototype
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                
                // Make the node bigger
                this.size[1] = 300;
            };

            const originalNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                debug("TrellisVideoPlayerNode: onNodeCreated called");
                try {
                    const result = originalNodeCreated ? originalNodeCreated.apply(this, arguments) : undefined;
                    
                    // Create video element
                    const videoContainer = document.createElement("div");
                    videoContainer.style.width = "100%";
                    videoContainer.style.height = "280px";
                    videoContainer.style.backgroundColor = "#222";
                    videoContainer.style.borderRadius = "8px";
                    videoContainer.style.overflow = "hidden";
                    videoContainer.style.marginTop = "10px";
                    
                    const video = document.createElement("video");
                    video.style.width = "100%";
                    video.style.height = "100%";
                    video.controls = true;
                    video.style.objectFit = "contain";
                    
                    videoContainer.appendChild(video);
                    this.videoElement = video;
                    
                    // Add widget
                    this.addWidget("preview", "video_preview", "", () => {}, {
                        element: videoContainer,
                        serialize: false
                    });
                    
                    return result;
                } catch (error) {
                    console.error("Error in TrellisVideoPlayerNode creation:", error);
                }
            };

            // Handle video updates
            const originalExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                debug("TrellisVideoPlayerNode executed with message:", message);
                try {
                    if (message?.ui?.video_path) {
                        const videoPath = message.ui.video_path;
                        debug("Raw video path:", videoPath);
                        
                        const videoId = getFileId(videoPath);
                        if (videoId && this.videoElement) {
                            const viewerPath = `/trellis/view-video/${videoId}`;
                            debug("Loading video from:", viewerPath);
                            
                            this.videoElement.src = viewerPath;
                            this.videoElement.load();
                            
                            this.videoElement.onerror = () => {
                                debug("Error loading video, trying media path fallback");
                                const mediaPath = api.getMediaPath(videoPath);
                                this.videoElement.src = mediaPath;
                                this.videoElement.load();
                            };
                        } else {
                            debug("Could not extract video ID from path:", videoPath);
                        }
                    }
                    
                    if (originalExecuted) {
                        return originalExecuted.apply(this, arguments);
                    }
                } catch (error) {
                    console.error("Error in video node execution:", error);
                }
            };
        }
    }
});

// Helper function for model loading
function loadModelIntoScene(gltf, node) {
    const model = gltf.scene;
    
    // Clear existing model
    while(node.threeScene.children.length > 0){ 
        node.threeScene.remove(node.threeScene.children[0]); 
    }
    
    // Center and scale model
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    
    const maxDim = Math.max(size.x, size.y, size.z);
    const scale = 2 / maxDim;
    model.scale.setScalar(scale);
    
    model.position.sub(center.multiplyScalar(scale));
    
    node.threeScene.add(model);
}

// Helper function to ensure we have a string path
function ensurePath(pathData) {
    if (!pathData) return null;
    
    // If it's a string, use it directly
    if (typeof pathData === 'string') return pathData;
    
    // If it's an array, join it
    if (Array.isArray(pathData)) {
        const joined = pathData.join('');
        debug("Joined array path:", joined);
        return joined;
    }
    
    // If it's an object with a path property
    if (typeof pathData === 'object') {
        if (pathData.path) return pathData.path;
        if (pathData.filepath) return pathData.filepath;
        if (pathData.file) return pathData.file;
    }
    
    // Last resort, convert to string
    return String(pathData);
}

// Add this helper function to check file accessibility
async function checkMediaPath(path) {
    const mediaPath = api.getMediaPath(path);
    debug("Checking media path:", {
        original: path,
        mediaPath: mediaPath,
        fullUrl: new URL(mediaPath, window.location.origin).href
    });
    
    try {
        const response = await fetch(mediaPath, { method: 'HEAD' });
        debug("Media path check result:", {
            status: response.status,
            ok: response.ok,
            contentType: response.headers.get('content-type')
        });
        return response.ok;
    } catch (error) {
        debug("Error checking media path:", error);
        return false;
    }
}

// Helper function to get file ID from path
function getFileId(path) {
    // Extract ID from paths like "trellis_downloads/f5348b34-02fc-41d3-b46c-dab8ce3517b7_output.mp4"
    const match = path.match(/([a-f0-9-]+)_output\.[^.]+$/);
    return match ? match[1] : null;
}

console.log("Trellis extension registered");