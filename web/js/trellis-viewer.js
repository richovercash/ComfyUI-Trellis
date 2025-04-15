// The correct way to import app and api in ComfyUI
import { app } from "/scripts/app.js";

// Add this near the beginning
const DEBUG = true;
function debug(...args) {
    if (DEBUG) {
        console.log("[Trellis Debug]", ...args);
        // Send to backend for logging
        logToBackend("JavaScript", args);
    }
}

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

function getMediaPath(path, type = "model") {
    if (!path) return null;
    debug(`getMediaPath called with: ${path}, type: ${type}`);
    
    // If it's already a complete URL
    if (path.startsWith('http://') || path.startsWith('https://')) {
        return path;
    }
    
    // Handle the case where path is an array
    if (Array.isArray(path)) {
        path = path.join('');
    }
    
    // Extract just the UUID part from the path
    let id;
    
    // Match a UUID pattern (8-4-4-4-12 format)
    const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
    const match = path.match(uuidPattern);
    
    if (match) {
        id = match[1];
        debug(`Extracted ID: ${id}`);
    } else {
        // If no UUID found, try extracting from filename pattern
        const filenameMatch = path.match(/([^\/]+)_output\.(glb|mp4|webm|mov)$/);
        if (filenameMatch) {
            id = filenameMatch[1];
            debug(`Extracted ID from filename: ${id}`);
        } else {
            // Fall back to the original path if no pattern matched
            id = path;
            debug(`No ID pattern found, using original path`);
        }
    }
    
    // Format the URL to match the server route
    return type === "model" ? `/trellis/model/${id}` : `/trellis/video/${id}`;
}

// Function to load scripts sequentially
function loadScript(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.onload = resolve;
        script.onerror = (error) => {
            console.error(`Error loading script ${url}:`, error);
            reject(error);
        };
        document.head.appendChild(script);
    });
}

// Main initialization function
async function initTrellisViewer() {
    debug("Starting Trellis viewer initialization");
    
    try {
        // Load Three.js and dependencies
        await loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js');
        debug("Three.js loaded successfully");
        
        await loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js');
        debug("GLTFLoader loaded successfully");
        
        await loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js');
        debug("OrbitControls loaded successfully");
        
        debug("All Three.js dependencies loaded");
        
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
                    
                    // Node creation
                    nodeType.prototype.onNodeCreated = function() {
                        debug("Creating TrellisModelViewerNode");
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
                            status.style.zIndex = "100";
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

                            // Initialize 3D scene
                            const renderer = new THREE.WebGLRenderer({ antialias: true });
                            renderer.setSize(380, 280);
                            renderer.setClearColor(0x222222);
                            container.appendChild(renderer.domElement);

                            // Create scene
                            const scene = new THREE.Scene();
                            scene.background = new THREE.Color(0x222222);

                            // Create camera
                            const camera = new THREE.PerspectiveCamera(75, 380/280, 0.1, 1000);
                            camera.position.z = 5;
                            
                            // Add lights to the scene
                            const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
                            scene.add(ambientLight);

                            const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
                            dirLight.position.set(1, 1, 1);
                            scene.add(dirLight);

                            // Add test cube to indicate viewer is working
                            const geometry = new THREE.BoxGeometry(1, 1, 1);
                            const material = new THREE.MeshStandardMaterial({ 
                                color: 0x00ffaa,
                                metalness: 0.3,
                                roughness: 0.4
                            });
                            const cube = new THREE.Mesh(geometry, material);
                            scene.add(cube);

                            // Add orbit controls
                            const controls = new THREE.OrbitControls(camera, renderer.domElement);
                            controls.enableDamping = true;
                            controls.dampingFactor = 0.25;
                            
                            // Store everything on the node
                            this.threeRenderer = renderer;
                            this.threeScene = scene;
                            this.threeCamera = camera;
                            this.controls = controls;
                            this.testCube = cube;
                            
                            // Animation loop
                            const animate = () => {
                                if (!this.graph) return; // Node has been deleted
                                
                                requestAnimationFrame(animate);
                                
                                if (this.testCube && this.testCube.visible) {
                                    this.testCube.rotation.x += 0.01;
                                    this.testCube.rotation.y += 0.01;
                                }
                                
                                if (this.controls) this.controls.update();
                                if (this.threeRenderer && this.threeScene && this.threeCamera) {
                                    this.threeRenderer.render(this.threeScene, this.threeCamera);
                                }
                            };
                            animate();

                            // Update status
                            this.statusText.textContent = "Ready";
                            setTimeout(() => {
                                this.statusText.style.opacity = 0;
                                this.statusText.style.transition = "opacity 1s";
                            }, 2000);
                            
                            debug("Three.js scene initialized successfully");
                        } catch (error) {
                            console.error("Error creating model viewer:", error);
                            debug("Error in model viewer creation:", error);
                        }
                    };
                    
                    // Model loading
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
                            } else if (message?.result) {
                                modelPath = Array.isArray(message.result)
                                    ? message.result[0]
                                    : message.result;
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
                            const mediaPath = getMediaPath(modelPath, "model");
                            debug("Loading model from:", mediaPath);
                            
                            // Show loading status
                            if (this.statusText) {
                                this.statusText.textContent = "Loading model...";
                                this.statusText.style.opacity = 1;
                            }
                            
                            // Check if loader is available
                            if (!window.THREE || !window.THREE.GLTFLoader) {
                                debug("GLTFLoader not available");
                                if (this.statusText) {
                                    this.statusText.textContent = "Error: GLTFLoader not available";
                                    this.statusText.style.color = "red";
                                }
                                return;
                            }
                            
                            // Clear any previous models but keep lights
                            const lightsAndCube = [];
                            this.threeScene.traverse(child => {
                                if (child instanceof THREE.Light || child === this.testCube) {
                                    lightsAndCube.push(child);
                                }
                            });
                            
                            this.threeScene.clear();
                            lightsAndCube.forEach(obj => this.threeScene.add(obj));
                            
                            // Load model
                            const loader = new THREE.GLTFLoader();
                            loader.load(
                                mediaPath, 
                                (gltf) => {
                                    debug("Model loaded successfully");
                                    debug("Model scene children count:", gltf.scene.children.length);
                                    
                                    // Add model to scene
                                    this.threeScene.add(gltf.scene);
                                    
                                    // Calculate bounding box for centering and scaling
                                    const box = new THREE.Box3().setFromObject(gltf.scene);
                                    const center = box.getCenter(new THREE.Vector3());
                                    const size = box.getSize(new THREE.Vector3());
                                    
                                    debug("Model bounding box:", {
                                        size: size,
                                        center: center
                                    });
                                    
                                    // Center model
                                    gltf.scene.position.x = -center.x;
                                    gltf.scene.position.y = -center.y;
                                    gltf.scene.position.z = -center.z;
                                    
                                    // Scale model to fit view
                                    const maxDim = Math.max(size.x, size.y, size.z);
                                    if (maxDim > 0) {
                                        const scale = 2 / maxDim;
                                        gltf.scene.scale.set(scale, scale, scale);
                                    }
                                    
                                    // Reset camera position
                                    this.threeCamera.position.set(0, 1, 5);
                                    this.controls.target.set(0, 0, 0);
                                    this.controls.update();
                                    
                                    // Ensure proper lighting
                                    if (!this.threeScene.children.some(child => child instanceof THREE.AmbientLight)) {
                                        const light = new THREE.AmbientLight(0xffffff, 0.7);
                                        this.threeScene.add(light);
                                    }
                                    
                                    if (!this.threeScene.children.some(child => child instanceof THREE.DirectionalLight)) {
                                        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
                                        dirLight.position.set(1, 1, 1);
                                        this.threeScene.add(dirLight);
                                    }
                                    
                                    // Update status
                                    if (this.statusText) {
                                        this.statusText.textContent = "Model loaded";
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
                                        this.statusText.textContent = `Error: ${error.message}`;
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
                            if (this.statusText) {
                                this.statusText.textContent = `Error: ${error.message}`;
                                this.statusText.style.color = "red";
                            }
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
                            videoContainer.style.width = "380px";
                            videoContainer.style.height = "280px";
                            videoContainer.style.backgroundColor = "#222";
                            videoContainer.style.borderRadius = "8px";
                            videoContainer.style.overflow = "hidden";
                            videoContainer.style.display = "flex";
                            videoContainer.style.alignItems = "center";
                            videoContainer.style.justifyContent = "center";
                            
                            const video = document.createElement("video");
                            video.style.width = "100%";
                            video.style.height = "100%";
                            video.controls = true;
                            video.autoplay = false;
                            video.muted = true;
                            video.style.objectFit = "contain";
                            video.style.backgroundColor = "#111";
                            
                            // Status overlay
                            const status = document.createElement("div");
                            status.style.position = "absolute";
                            status.style.top = "5px";
                            status.style.left = "5px";
                            status.style.color = "white";
                            status.style.background = "rgba(0,0,0,0.5)";
                            status.style.padding = "5px";
                            status.style.borderRadius = "3px";
                            status.style.zIndex = "100";
                            status.textContent = "Video Player Ready";
                            
                            videoContainer.appendChild(video);
                            videoContainer.appendChild(status);
                            
                            this.videoElement = video;
                            this.statusText = status;
                            
                            // Add widget
                            this.addWidget("preview", "video_preview", "", () => {}, {
                                element: videoContainer,
                                serialize: false
                            });
                            
                            // Hide status after a short delay
                            setTimeout(() => {
                                status.style.opacity = 0;
                                status.style.transition = "opacity 1s";
                            }, 2000);
                            
                        } catch (error) {
                            console.error("Error in TrellisVideoPlayerNode creation:", error);
                            debug("Error in video player creation:", error);
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
                            } else if (message?.result) {
                                videoPath = Array.isArray(message.result)
                                    ? message.result[0]
                                    : message.result;
                            }

                            debug("Raw video path:", videoPath);
                            
                            if (!videoPath || !this.videoElement) {
                                debug("No video path or video element not available");
                                return;
                            }
                            
                            // Generate proper video URL
                            const mediaPath = getMediaPath(videoPath, "video");
                            debug("Loading video from:", mediaPath);
                            
                            // Show status while loading
                            if (this.statusText) {
                                this.statusText.textContent = "Loading video...";
                                this.statusText.style.opacity = 1;
                            }
                            
                            // Set video source and load
                            const videoElement = this.videoElement;
                            
                            // Clear current video
                            videoElement.pause();
                            videoElement.removeAttribute('src');
                            videoElement.load();
                            
                            // Detect when video is loaded
                            videoElement.oncanplay = () => {
                                debug("Video can play now");
                                if (this.statusText) {
                                    this.statusText.textContent = "Video loaded";
                                    setTimeout(() => {
                                        this.statusText.style.opacity = 0;
                                    }, 2000);
                                }
                            };
                            
                            // Handle errors
                            videoElement.onerror = (e) => {
                                debug("Video error:", videoElement.error);
                                if (this.statusText) {
                                    this.statusText.textContent = `Error: ${videoElement.error?.message || "Video failed to load"}`;
                                    this.statusText.style.color = "red";
                                    this.statusText.style.opacity = 1;
                                }
                            };
                            
                            // Set video source and load
                            videoElement.src = mediaPath;
                            videoElement.type = "video/mp4";
                            videoElement.load();
                            
                        } catch (error) {
                            debug("Error in video player execution:", error);
                            if (this.statusText) {
                                this.statusText.textContent = `Error: ${error.message}`;
                                this.statusText.style.color = "red";
                                this.statusText.style.opacity = 1;
                            }
                        }
                    };
                }
            }
        });

        debug("Trellis extension registered successfully");
    } catch (error) {
        console.error("Error initializing Trellis viewer:", error);
        debug("Error initializing Trellis viewer:", error);
    }
}






// Start initialization
console.log("Trellis viewer script loading...");
initTrellisViewer().catch(error => {
    console.error("Failed to initialize Trellis viewer:", error);
});


