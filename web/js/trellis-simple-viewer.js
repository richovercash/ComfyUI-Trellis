// trellis-simple-viewer.js - Modified for output node compatibility

import { app } from "/scripts/app.js";

app.registerExtension({
    name: "Trellis.SimpleMediaViewer",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        // Handle model viewer
        if (nodeData.name === "TrellisModelViewerNode") {
            console.log("Registering Trellis Model Viewer Node");
            
            // Make node taller to fit content
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                this.size[1] = 280; // Set fixed height
            };
            
            // Create node UI
            nodeType.prototype.onNodeCreated = function() {
                console.log("Creating Trellis Model Viewer Node");
                
                // Create iframe container
                const container = document.createElement("div");
                container.style.width = "100%";
                container.style.height = "250px";
                container.style.position = "relative";
                container.style.backgroundColor = "#333";
                container.style.borderRadius = "8px";
                container.style.overflow = "hidden";
                
                // Add status display
                const status = document.createElement("div");
                status.style.position = "absolute";
                status.style.top = "10px";
                status.style.left = "10px";
                status.style.color = "white";
                status.style.background = "rgba(0,0,0,0.5)";
                status.style.padding = "5px";
                status.style.borderRadius = "4px";
                status.style.zIndex = "10";
                status.textContent = "No model loaded";
                container.appendChild(status);
                this.statusElement = status;
                
                // Create iframe (initially empty)
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.display = "block";
                container.appendChild(iframe);
                this.iframe = iframe;
                
                // Add widget to node
                this.addWidget("preview", "model_preview", "", null, {
                    element: container
                });
                
                // Add a button to refresh the view
                this.addWidget("button", "refresh", "Refresh", () => {
                    if (this.lastModelId) {
                        this.loadModel(this.lastModelId);
                    }
                });
            };
            
            // Add method to load models
            nodeType.prototype.loadModel = function(modelId) {
                if (!modelId || !this.iframe) return;
                
                this.lastModelId = modelId;
                
                // Update status
                if (this.statusElement) {
                    this.statusElement.textContent = "Loading model...";
                    this.statusElement.style.opacity = "1";
                }
                
                // Set iframe to our simplified viewer
                this.iframe.src = `/trellis/simple-viewer/model/${modelId}`;
            };
            
            // Handle execution
            const originalOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                // Call original handler if exists
                if (originalOnExecuted) {
                    originalOnExecuted.apply(this, arguments);
                }
                
                console.log("Model viewer executed:", message);
                
                try {
                    // Get model path from the inputs (first item of message)
                    let modelPath = "";
                    if (message && message.length > 0) {
                        modelPath = message[0];
                    }
                    
                    if (!modelPath) return;
                    
                    // Extract ID from path
                    const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
                    const match = modelPath.match(uuidPattern);
                    
                    let modelId;
                    if (match) {
                        modelId = match[1];
                    } else {
                        const filenameMatch = modelPath.match(/([^\/]+)_output\.(glb|gltf)$/);
                        if (filenameMatch) {
                            modelId = filenameMatch[1];
                        } else {
                            modelId = modelPath;
                        }
                    }
                    
                    this.loadModel(modelId);
                    
                } catch (error) {
                    console.error("Error loading model:", error);
                    if (this.statusElement) {
                        this.statusElement.textContent = `Error: ${error.message}`;
                    }
                }
            };
        }
        
        // Handle video player
        if (nodeData.name === "TrellisVideoPlayerNode") {
            console.log("Registering Trellis Video Player Node");
            
            // Make node taller
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                this.size[1] = 280; // Set fixed height
            };
            
            // Create node UI
            nodeType.prototype.onNodeCreated = function() {
                console.log("Creating Trellis Video Player Node");
                
                // Create iframe container
                const container = document.createElement("div");
                container.style.width = "100%";
                container.style.height = "250px";
                container.style.position = "relative";
                container.style.backgroundColor = "#333";
                container.style.borderRadius = "8px";
                container.style.overflow = "hidden";
                
                // Add status display
                const status = document.createElement("div");
                status.style.position = "absolute";
                status.style.top = "10px";
                status.style.left = "10px";
                status.style.color = "white";
                status.style.background = "rgba(0,0,0,0.5)";
                status.style.padding = "5px";
                status.style.borderRadius = "4px";
                status.style.zIndex = "10";
                status.textContent = "No video loaded";
                container.appendChild(status);
                this.statusElement = status;
                
                // Create iframe (initially empty)
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.display = "block";
                container.appendChild(iframe);
                this.iframe = iframe;
                
                // Add widget to node
                this.addWidget("preview", "video_preview", "", null, {
                    element: container
                });
                
                // Add a button to refresh the view
                this.addWidget("button", "refresh", "Refresh", () => {
                    if (this.lastVideoId) {
                        this.loadVideo(this.lastVideoId);
                    }
                });
            };
            
            // Add method to load videos
            nodeType.prototype.loadVideo = function(videoId) {
                if (!videoId || !this.iframe) return;
                
                this.lastVideoId = videoId;
                
                // Update status
                if (this.statusElement) {
                    this.statusElement.textContent = "Loading video...";
                    this.statusElement.style.opacity = "1";
                }
                
                // Set iframe to our simplified viewer
                this.iframe.src = `/trellis/simple-viewer/video/${videoId}`;
            };
            
            // Handle execution
            const originalOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                // Call original handler if exists
                if (originalOnExecuted) {
                    originalOnExecuted.apply(this, arguments);
                }
                
                console.log("Video player executed:", message);
                
                try {
                    // Get video path from the inputs (first item of message)
                    let videoPath = "";
                    if (message && message.length > 0) {
                        videoPath = message[0];
                    }
                    
                    if (!videoPath) return;
                    
                    // Extract ID from path
                    const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
                    const match = videoPath.match(uuidPattern);
                    
                    let videoId;
                    if (match) {
                        videoId = match[1];
                    } else {
                        const filenameMatch = videoPath.match(/([^\/]+)_output\.(mp4|webm|mov)$/);
                        if (filenameMatch) {
                            videoId = filenameMatch[1];
                        } else {
                            videoId = videoPath;
                        }
                    }
                    
                    this.loadVideo(videoId);
                    
                } catch (error) {
                    console.error("Error loading video:", error);
                    if (this.statusElement) {
                        this.statusElement.textContent = `Error: ${error.message}`;
                    }
                }
            };
        }
    }
});

console.log("Trellis Simple Media Viewer loaded");