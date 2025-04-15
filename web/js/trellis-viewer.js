// The correct way to import app and api in ComfyUI
import { app } from "/scripts/app.js";

// // Load Three.js from CDN directly
// const script = document.createElement('script');
// script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
// document.head.appendChild(script);

// console.log("Trellis viewer script loading...");
// // At the top of the file
// const DEBUG = true;
// function debug(...args) {
//     if (DEBUG) {
//         console.log("[Trellis Debug]", ...args);
//         // Send to backend for logging
//         logToBackend("JavaScript", args);
//     }
// }

// script.onload = () => {
//     console.log("Three.js loaded successfully");
//     // Load GLTFLoader after Three.js is loaded
//     const gltfScript = document.createElement('script');
//     gltfScript.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js';
//     document.head.appendChild(gltfScript);

//     gltfScript.onload = () => {
//         console.log("GLTFLoader loaded successfully");
//         // Load OrbitControls after GLTFLoader
//         const orbitScript = document.createElement('script');
//         orbitScript.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js';
//         document.head.appendChild(orbitScript);
        
//         orbitScript.onload = () => {
//             console.log("OrbitControls loaded successfully");
//         };
//     };
// };

// Add this near the beginning
const DEBUG = true;
function debug(...args) {
    if (DEBUG) {
        console.log("[Trellis Debug]", ...args);
        // Send to backend for logging
        logToBackend("JavaScript", args);
    }
}

function getMediaPath(path) {
    if (!path) return null;
    console.log("[Trellis Debug] getMediaPath called with:", path);
    
    // If it's already a complete URL
    if (path.startsWith('http://') || path.startsWith('https://')) {
        return path;
    }
    
    // Handle the case where path is an array
    if (Array.isArray(path)) {
        path = path.join('');
    }
    
    // Extract just the UUID part from the path
    let modelId;
    
    // Match a UUID pattern (8-4-4-4-12 format)
    const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
    const match = path.match(uuidPattern);
    
    if (match) {
        modelId = match[1];
        console.log("[Trellis Debug] Extracted model ID:", modelId);
    } else {
        // Fall back to the original path if no UUID found
        modelId = path;
        console.log("[Trellis Debug] No UUID found, using original path");
    }
    
    // Format the URL to match the server route
    return `/trellis/model/${modelId}`;
}


// At the top of your file, define a function to load scripts sequentially
function loadScript(url, callback) {
    const script = document.createElement('script');
    script.src = url;
    script.onload = callback;
    script.onerror = (error) => {
        console.error(`Error loading script ${url}:`, error);
    };
    document.head.appendChild(script);
}


function initTrellisViewer() {
    console.log("Trellis viewer initialized with Three.js");
    
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
                
                // Simple fixed-size node creation
                nodeType.prototype.onNodeCreated = function() {
                    console.log("Creating TrellisModelViewerNode");
                    try {
                        // Create container with fixed dimensions
                        const container = document.createElement("div");
                        container.style.width = "380px";
                        container.style.height = "280px";
                        container.style.backgroundColor = "#222";
                        container.style.borderRadius = "8px";
                        container.style.overflow = "hidden";
                        container.style.position = "relative";
                        
                        // Status text
                        const status = document.createElement("div");
                        status.style.position = "absolute";
                        status.style.top = "5px";
                        status.style.left = "5px";
                        status.style.color = "white";
                        status.style.background = "rgba(0,0,0,0.5)";
                        status.style.padding = "5px";
                        status.style.borderRadius = "3px";
                        status.textContent = "Initializing...";
                        container.appendChild(status);
                        this.statusText = status;
                        
                        // Add widget
                        this.addWidget("preview", "model_preview", "", () => {}, {
                            element: container,
                            serialize: false
                        });
                        
                        // Store container reference
                        this.viewerContainer = container;

                        // Initialize 3D scene immediately (since Three.js is already loaded)
                        // Create fixed-size renderer
                        const renderer = new THREE.WebGLRenderer({ antialias: true });
                        renderer.setSize(380, 280);
                        container.appendChild(renderer.domElement);

                        // Create scene
                        const scene = new THREE.Scene();
                        scene.background = new THREE.Color(0x222222);

                        // Store reference to scene
                        this.threeScene = scene;

                        // Create camera
                        const camera = new THREE.PerspectiveCamera(75, 380/280, 0.1, 1000);
                        camera.position.z = 5;
                        this.threeCamera = camera;

                        // Add light to the scene (using the property name threeScene)
                        const light = new THREE.AmbientLight(0xffffff, 0.7);
                        this.threeScene.add(light);  // Use threeScene consistently

                        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
                        dirLight.position.set(1, 1, 1);
                        this.threeScene.add(dirLight);  // Use threeScene consistently

                        // Add test cube
                        const geometry = new THREE.BoxGeometry(1, 1, 1);
                        const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
                        const cube = new THREE.Mesh(geometry, material);
                        this.threeScene.add(cube);  // Use threeScene consistently

                        // Store references - only store renderer and testCube since we've already stored scene and camera
                        this.threeRenderer = renderer;
                        this.testCube = cube;

                        // Animation loop
                        const animate = () => {
                            requestAnimationFrame(animate);
                            cube.rotation.x += 0.01;
                            cube.rotation.y += 0.01;
                            renderer.render(scene, camera);  // Using local variables is fine here
                        };
                        animate();

                        // Add orbit controls
                        this.controls = new THREE.OrbitControls(camera, renderer.domElement);

                        // Update status
                        this.statusText.textContent = "Ready";
                        setTimeout(() => {
                            this.statusText.style.opacity = 0;
                            this.statusText.style.transition = "opacity 1s";
                        }, 2000);
                        
                        debug("Three.js scene initialized");
                    } catch (error) {
                        console.error("Error creating model viewer:", error);
                    }
                };
                
            // Simple model loading
            nodeType.prototype.onExecuted = function(message) {
                debug("Model viewer onExecuted called with:", message);
                
                try {
                    // Extract model path
                    let modelPath;
                    if (message?.model_path) {
                        modelPath = Array.isArray(message.model_path) 
                            ? message.model_path.join('') 
                            : message.model_path;
                    } else if (message?.ui?.model_path) {
                        modelPath = Array.isArray(message.ui.model_path)
                            ? message.ui.model_path.join('')
                            : message.ui.model_path;
                    }
                    
                    debug("Raw model path:", modelPath);
                    
                    // Check if scene is ready
                    if (!this.threeScene || !this.threeRenderer) {
                        debug("Scene not ready yet");
                        return;
                    }
                    
                    if (!modelPath) {
                        debug("No model path provided");
                        return;
                    }
                    
                    // Hide test cube
                    if (this.testCube) {
                        this.testCube.visible = false;
                    }
                    
                    // Generate media path
                    const mediaPath = getMediaPath(modelPath);
                    debug("Loading from:", mediaPath);
                    
                    // Show loading status
                    if (this.statusText) {
                        this.statusText.textContent = "Loading model...";
                        this.statusText.style.opacity = 1;
                    }
                    
                    // Check if loader is available
                    if (!window.THREE || !window.THREE.GLTFLoader) {
                        debug("GLTFLoader not available");
                        return;
                    }
                    
                        // Load model
                        const loader = new THREE.GLTFLoader();
                        loader.load(
                            mediaPath, 
                            (gltf) => {
                                debug("Model loaded successfully");
                                debug("Model scene children count:", gltf.scene.children.length);
                                debug("Box size:", new THREE.Box3().setFromObject(gltf.scene).getSize(new THREE.Vector3()));
                                
                                // Remove previous models but keep lights
                                this.threeScene.children = this.threeScene.children.filter(
                                    child => child instanceof THREE.Light || child === this.testCube
                                );
                                
                                // Add model
                                this.threeScene.add(gltf.scene);
                                
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
                                
                                // Update camera
                                this.threeCamera.position.set(0, 1, 5);
                                this.controls.update();  // Make sure to update controls
                                
                                const light = new THREE.AmbientLight(0xffffff, 1.0);  
                                this.threeScene.add(light);
                                
                                const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                                dirLight.position.set(1, 1, 1);
                                this.threeScene.add(dirLight);

                                // Log camera and model positions for debugging
                                debug("Camera position:", this.threeCamera.position);
                                debug("Model position:", gltf.scene.position);

                                // Update status
                                if (this.statusText) {
                                    this.statusText.textContent = "Model displayed";
                                    setTimeout(() => {
                                        this.statusText.style.opacity = 0;
                                    }, 2000);
                                }
                            },
                            // Progress callback
                            (progress) => {
                                const percent = (progress.loaded / progress.total * 100).toFixed(2);
                                debug(`Loading progress: ${percent}%`);
                                
                                if (this.statusText) {
                                    this.statusText.textContent = `Loading: ${percent}%`;
                                }
                            },
                            // Error callback
                            (error) => {
                                debug("Error loading model:", {
                                    error: error.message,
                                    modelPath,
                                    mediaPath
                                });
                                
                                if (this.statusText) {
                                    this.statusText.textContent = "Error loading model";
                                    this.statusText.style.color = "red";
                                }
                                
                                // Show test cube again
                                if (this.testCube) {
                                    this.testCube.visible = true;
                                }
                            }
                        );
                    } catch (error) {
                        debug("Error in model viewer execution:", error);
                    }
                };
                }

                // Handle video player node
                if (nodeData.name === "TrellisVideoPlayerNode") {
                debug("Registering video player UI");

                const onDrawBackground = nodeType.prototype.onDrawBackground;
                nodeType.prototype.onDrawBackground = function(ctx) {
                    if (onDrawBackground) {
                        onDrawBackground.apply(this, arguments);
                    }
                    
                    // Make the node bigger
                    this.size[1] = 300;
                };

                nodeType.prototype.onNodeCreated = function() {
                    debug("TrellisVideoPlayerNode: onNodeCreated called");
                    try {
                        // Create video element
                        const videoContainer = document.createElement("div");
                        videoContainer.style.width = "100%";
                        videoContainer.style.height = "280px";
                        videoContainer.style.backgroundColor = "#222";
                        videoContainer.style.borderRadius = "8px";
                        videoContainer.style.overflow = "hidden";
                        
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
                    } catch (error) {
                        console.error("Error in TrellisVideoPlayerNode creation:", error);
                    }
                };

                // Handle video updates
                nodeType.prototype.onExecuted = function(message) {
                    debug("Video player onExecuted called with:", message);


                    
                    try {
                        // Extract video path
                        let videoPath;
                        if (message?.video_path) {
                            videoPath = Array.isArray(message.video_path) 
                                ? message.video_path.join('') 
                                : message.video_path;
                        } else if (message?.ui?.video_path) {
                            videoPath = Array.isArray(message.ui.video_path)
                                ? message.ui.video_path.join('')
                                : message.ui.video_path;
                        }

                        debug("Raw video path:", videoPath);
                        
                        if (videoPath && this.videoElement) {
                            // Extract video ID
                            let videoId = videoPath;
                            if (videoPath.includes('trellis_downloads/')) {
                                const match = videoPath.match(/trellis_downloads\/([^\/]+)/);
                                if (match) {
                                    videoId = match[1].replace('_output.mp4', '');
                                }
                            } else if (videoPath.includes('_output.mp4')) {
                                videoId = videoPath.split('_output.mp4')[0];
                            }
                            
                            // Use the proper endpoint
                            const mediaPath = `/trellis/video/${videoId}`;
                            debug("Loading video from:", mediaPath);
                            
                            // this.videoElement.src = mediaPath;
                            // this.videoElement.load();
                            // In your video player onExecuted function:
                            this.videoElement.src = mediaPath;
                            this.videoElement.type = "video/mp4";  // Explicitly set the MIME type
                            this.videoElement.load();
                        }
                    } catch (error) {
                        debug("Error in video player execution:", error);
                    }
    };
    }
    }
    });

    console.log("Trellis extension registered");

}

// Then load scripts in sequence
console.log("Trellis viewer script loading...");
// First load Three.js
loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', () => {
    console.log("Three.js loaded successfully");
    // Then load GLTFLoader after Three.js is loaded
    loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js', () => {
        console.log("GLTFLoader loaded successfully");
        // Then load OrbitControls after GLTFLoader
        loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js', () => {
            console.log("OrbitControls loaded successfully");
            // Finally initialize everything
            initTrellisViewer();
        });
    });
});






// Update the logToBackend function to use fetch directly
async function logToBackend(source, data) {
    try {
        await fetch('/trellis/debug', {
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
