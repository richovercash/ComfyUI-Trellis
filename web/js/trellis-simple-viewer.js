// trellis-simple-viewer.js - Clean implementation with proper execution handling

import { app } from "/scripts/app.js";

app.registerExtension({
    name: "Trellis.SimpleMediaViewer",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        // Model Viewer Node
        if (nodeData.name === "TrellisModelViewerNode") {
            console.log("Registering Trellis Model Viewer Node");
            
            // Make node taller
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                this.size[1] = 280;
            };
            
            // Function to extract ID from path - DEFINED AT CLASS LEVEL
            nodeType.prototype.extractId = function(path) {
                console.log("Extracting ID from path:", path);
                
                if (!path) {
                    console.log("Path is empty");
                    return null;
                }
                
                // Convert to string if needed
                path = String(path);
                
                // Try UUID pattern
                const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
                const match = path.match(uuidPattern);
                
                if (match) {
                    console.log("Found UUID:", match[1]);
                    return match[1];
                }
                
                // Try filename pattern
                const filenameMatch = path.match(/([^\/]+)_output\.(glb|gltf)$/);
                if (filenameMatch) {
                    console.log("Found filename ID:", filenameMatch[1]);
                    return filenameMatch[1];
                }
                
                // Just return the path
                console.log("Using path as ID:", path);
                return path;
            };
            
            // Function to load model - DEFINED AT CLASS LEVEL
            nodeType.prototype.loadModel = function(modelId) {
                console.log("Loading model:", modelId);
                
                if (!modelId || !this.iframe) {
                    console.log("Cannot load model - missing ID or iframe");
                    return;
                }
                
                this.lastModelId = modelId;
                
                // Update status
                if (this.statusElement) {
                    this.statusElement.textContent = "Loading model...";
                }
                
                // Set iframe source
                const viewerUrl = `/trellis/simple-viewer/model/${modelId}`;
                console.log("Setting model iframe src to:", viewerUrl);
                this.iframe.src = viewerUrl;
            };
            
            // Create node UI elements
            nodeType.prototype.onNodeCreated = function() {
                console.log("Creating Trellis Model Viewer Node");
                
                // Create container
                const container = document.createElement("div");
                container.style.width = "100%";
                container.style.height = "250px";
                container.style.position = "relative";
                container.style.backgroundColor = "#333";
                container.style.borderRadius = "8px";
                container.style.overflow = "hidden";
                
                console.log("Created model container");
                
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
                
                console.log("Added model status element");
                
                // Create iframe
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.display = "block";
                container.appendChild(iframe);
                this.iframe = iframe;
                
                console.log("Added model iframe");
                
                // Add test model viewer
                const testId = "cbecf79b-beee-469e-81fe-0ff63d966d4b";
                iframe.src = `/trellis/simple-viewer/model/${testId}`;
                console.log(`Test model URL: /trellis/simple-viewer/model/${testId}`);
                
                // Add widget to node
                this.addWidget("preview", "model_preview", "", null, {
                    element: container
                });
                
                // Add test button
                const self = this; // Save reference to this
                this.addWidget("button", "test_load", "Test Load", function() {
                    console.log("Model test button clicked");
                    self.loadModel("cbecf79b-beee-469e-81fe-0ff63d966d4b");
                });
                
                // Add refresh button
                this.addWidget("button", "refresh", "Refresh", function() {
                    console.log("Model refresh button clicked");
                    if (self.lastModelId) {
                        self.loadModel(self.lastModelId);
                    }
                });
            };
            
            // Handle execution
            const originalOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                console.log("🔴 Model viewer onExecuted called with:", message);
                
                // Call original if it exists
                if (originalOnExecuted) {
                    originalOnExecuted.apply(this, arguments);
                }
                
                try {
                    // Get model path
                    let modelPath = null;
                    
                    if (Array.isArray(message) && message.length > 0) {
                        modelPath = message[0];
                        console.log("Using array first element as model path:", modelPath);
                    } else if (message?.model_path) {
                        modelPath = message.model_path;
                        console.log("Using message.model_path:", modelPath);
                    } else if (message?.ui?.model_path) {
                        modelPath = message.ui.model_path;
                        console.log("Using message.ui.model_path:", modelPath);
                    } else if (message?.result) {
                        modelPath = Array.isArray(message.result) ? message.result[0] : message.result;
                        console.log("Using message.result as model path:", modelPath);
                    } else if (typeof message === 'string') {
                        modelPath = message;
                        console.log("Using message string directly as model path:", modelPath);
                    } else {
                        console.log("Could not identify model path in message. Full message:", JSON.stringify(message));
                    }
                    
                    if (!modelPath) {
                        console.log("No model path found in execution message");
                        return;
                    }
                    
                    // Extract ID and load model
                    const modelId = this.extractId(modelPath);
                    console.log("Extracted model ID for loading:", modelId);
                    
                    if (modelId) {
                        this.loadModel(modelId);
                    }
                    
                } catch (error) {
                    console.error("Error in model viewer execution:", error);
                    if (this.statusElement) {
                        this.statusElement.textContent = `Error: ${error.message}`;
                        this.statusElement.style.color = "red";
                    }
                }
            };
        }
        
        // Video Player Node - Similar structure to Model Viewer
        if (nodeData.name === "TrellisVideoPlayerNode") {
            console.log("Registering Trellis Video Player Node");
            
            // Make node taller
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                this.size[1] = 280;
            };
            
            // Function to extract ID from path - DEFINED AT CLASS LEVEL
            nodeType.prototype.extractId = function(path) {
                console.log("Extracting ID from video path:", path);
                
                if (!path) {
                    console.log("Video path is empty");
                    return null;
                }
                
                // Convert to string if needed
                path = String(path);
                
                // Try UUID pattern
                const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
                const match = path.match(uuidPattern);
                
                if (match) {
                    console.log("Found video UUID:", match[1]);
                    return match[1];
                }
                
                // Try filename pattern
                const filenameMatch = path.match(/([^\/]+)_output\.(mp4|webm|mov)$/);
                if (filenameMatch) {
                    console.log("Found video filename ID:", filenameMatch[1]);
                    return filenameMatch[1];
                }
                
                // Just return the path
                console.log("Using video path as ID:", path);
                return path;
            };
            
            // Function to load video - DEFINED AT CLASS LEVEL
            nodeType.prototype.loadVideo = function(videoId) {
                console.log("Loading video:", videoId);
                
                if (!videoId || !this.iframe) {
                    console.log("Cannot load video - missing ID or iframe");
                    return;
                }
                
                this.lastVideoId = videoId;
                
                // Update status
                if (this.statusElement) {
                    this.statusElement.textContent = "Loading video...";
                }
                
                // Set iframe source
                const viewerUrl = `/trellis/simple-viewer/video/${videoId}`;
                console.log("Setting video iframe src to:", viewerUrl);
                this.iframe.src = viewerUrl;
            };
            
            // Create node UI elements
            nodeType.prototype.onNodeCreated = function() {
                console.log("Creating Trellis Video Player Node");
                
                // Create container
                const container = document.createElement("div");
                container.style.width = "100%";
                container.style.height = "250px";
                container.style.position = "relative";
                container.style.backgroundColor = "#333";
                container.style.borderRadius = "8px";
                container.style.overflow = "hidden";
                
                console.log("Creating video container");
                
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
                
                // Create iframe
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.display = "block";
                container.appendChild(iframe);
                this.iframe = iframe;
                
                console.log("Creating video iframe");
                
                // Add test video viewer
                const testId = "cbecf79b-beee-469e-81fe-0ff63d966d4b";
                iframe.src = `/trellis/simple-viewer/video/${testId}`;
                console.log(`Testing with hardcoded URL: /trellis/simple-viewer/video/${testId}`);
                
                // Add widget to node
                this.addWidget("preview", "video_preview", "", null, {
                    element: container
                });
                
                // Add test button
                const self = this; // Save reference to this
                this.addWidget("button", "test_load", "Test Load", function() {
                    console.log("Video test button clicked");
                    self.loadVideo("cbecf79b-beee-469e-81fe-0ff63d966d4b");
                });
                
                // Add refresh button
                this.addWidget("button", "refresh", "Refresh", function() {
                    console.log("Video refresh button clicked");
                    if (self.lastVideoId) {
                        self.loadVideo(self.lastVideoId);
                    }
                });
            };
            
            // Handle execution
            const originalOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                console.log("🔴 Video player onExecuted called with:", message);
                
                // Call original if it exists
                if (originalOnExecuted) {
                    originalOnExecuted.apply(this, arguments);
                }
                
                try {
                    // Get video path
                    let videoPath = null;
                    
                    if (Array.isArray(message) && message.length > 0) {
                        videoPath = message[0];
                        console.log("Using array first element as video path:", videoPath);
                    } else if (message?.video_path) {
                        videoPath = message.video_path;
                        console.log("Using message.video_path:", videoPath);
                    } else if (message?.ui?.video_path) {
                        videoPath = message.ui.video_path;
                        console.log("Using message.ui.video_path:", videoPath);
                    } else if (message?.result) {
                        videoPath = Array.isArray(message.result) ? message.result[0] : message.result;
                        console.log("Using message.result as video path:", videoPath);
                    } else if (typeof message === 'string') {
                        videoPath = message;
                        console.log("Using message string directly as video path:", videoPath);
                    } else {
                        console.log("Could not identify video path in message. Full message:", JSON.stringify(message));
                    }
                    
                    if (!videoPath) {
                        console.log("No video path found in execution message");
                        return;
                    }
                    
                    // Extract ID and load video
                    const videoId = this.extractId(videoPath);
                    console.log("Extracted video ID for loading:", videoId);
                    
                    if (videoId) {
                        this.loadVideo(videoId);
                    }
                    
                } catch (error) {
                    console.error("Error in video player execution:", error);
                    if (this.statusElement) {
                        this.statusElement.textContent = `Error: ${error.message}`;
                        this.statusElement.style.color = "red";
                    }
                }
            };
        }
    }
});

console.log("Trellis Simple Media Viewer loaded");