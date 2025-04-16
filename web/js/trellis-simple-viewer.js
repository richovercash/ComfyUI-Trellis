// trellis-simple-viewer.js - Clean implementation with improved path handling and error feedback

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
            
            // Function to extract ID from path - DEFINED AT CLASS LEVEL with improved regex
            nodeType.prototype.extractId = function(path) {
                console.log("Extracting ID from path:", path);
                
                if (!path) {
                    console.log("Path is empty");
                    return null;
                }
                
                // Convert to string if needed
                path = String(path).trim();
                
                // Try UUID pattern
                const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
                const match = path.match(uuidPattern);
                
                if (match) {
                    console.log("Found UUID:", match[1]);
                    return match[1];
                }
                
                // Try filename pattern with more flexible matching
                const filenameMatch = path.match(/([^\/\\]+?)(?:_output)?(?:\.glb|\.gltf)?$/i);
                if (filenameMatch) {
                    const filename = filenameMatch[1];
                    // Make sure we don't have just a file extension
                    if (filename && !filename.startsWith('.')) {
                        console.log("Found filename ID:", filename);
                        return filename;
                    }
                }
                
                // Just return the path
                console.log("Using path as ID:", path);
                return path;
            };
            
            // Function to load model - DEFINED AT CLASS LEVEL with better error handling
            nodeType.prototype.loadModel = function(modelId) {
                console.log("Loading model:", modelId);
                
                if (!modelId || !this.iframe) {
                    console.log("Cannot load model - missing ID or iframe");
                    if (this.statusElement) {
                        this.statusElement.textContent = "Error: Cannot load model - missing ID or iframe";
                        this.statusElement.style.color = "red";
                    }
                    return;
                }
                
                this.lastModelId = modelId;
                
                // Update status
                if (this.statusElement) {
                    this.statusElement.textContent = "Loading model...";
                    this.statusElement.style.color = "white";
                }
                
                // Set iframe source with cache busting for better reloading
                const timestamp = Date.now();
                const viewerUrl = `/trellis/simple-viewer/model/${modelId}?cache=${timestamp}`;
                console.log("Setting model iframe src to:", viewerUrl);
                this.iframe.src = viewerUrl;
            };
            




                        // Create node UI elements with proper widget reference storage
            nodeType.prototype.onNodeCreated = function() {
                console.log("Creating Trellis Model Viewer Node");
                
                // Create container
                const container = document.createElement("div");
                container.style.width = "100%";
                container.style.height = "250px";
                container.style.position = "relative";
                container.style.backgroundColor = "#222";
                container.style.borderRadius = "8px";
                container.style.overflow = "hidden";
                
                // Add status display
                const status = document.createElement("div");
                status.style.position = "absolute";
                status.style.top = "10px";
                status.style.left = "10px";
                status.style.right = "10px";
                status.style.textAlign = "center";
                status.style.color = "white";
                status.style.background = "rgba(0,0,0,0.7)";
                status.style.padding = "5px";
                status.style.borderRadius = "4px";
                status.style.zIndex = "10";
                status.textContent = "No model loaded";
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
                
                // Store it directly on the node's properties
                this.properties = this.properties || {};
                this.properties.model_id = "";
                
                // Add widget to node
                this.addWidget("preview", "model_preview", "", null, {
                    element: container
                });
                
                // Add text input widget with direct property binding
                this.addWidget("text", "model_id", "Model ID", this.properties.model_id, (value) => {
                    console.log("Model ID changed to:", value);
                    this.properties.model_id = value; // Store in properties
                });
                
                // Add load button
                const node = this; // Store reference to node
                this.addWidget("button", "load_model", "Load Model", function() {
                    console.log("Model load button clicked");
                    // Access value from properties
                    const modelId = node.properties.model_id;
                    console.log("Using model ID:", modelId || "<empty>");
                    
                    if (!modelId || modelId.trim() === "") {
                        if (node.statusElement) {
                            node.statusElement.textContent = "Error: Please enter a model ID";
                            node.statusElement.style.color = "red";
                        }
                        return;
                    }
                    
                    if (typeof node.loadModel === 'function') {
                        node.loadModel(modelId.trim());
                    } else {
                        console.error("loadModel function not available");
                    }
                });
                
                // Similar pattern for the refresh button
                this.addWidget("button", "refresh", "Refresh", function() {
                    console.log("Refresh button clicked");
                    
                    // Access lastModelId or model_id property
                    const modelId = node.lastModelId || node.properties.model_id;
                    console.log("Using cached/property model ID:", modelId || "<empty>");
                    
                    if (!modelId || modelId.trim() === "") {
                        if (node.statusElement) {
                            node.statusElement.textContent = "Error: No model to refresh";
                            node.statusElement.style.color = "red";
                        }
                        return;
                    }
                    
                    if (typeof node.loadModel === 'function') {
                        node.loadModel(modelId.trim());
                    } else {
                        console.error("loadModel function not available");
                    }
                });
            }
            
            // Handle execution with improved path extraction and error handling
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
                        if (this.statusElement) {
                            this.statusElement.textContent = "Error: No model path found in execution message";
                            this.statusElement.style.color = "red";
                        }
                        console.log("No model path found in execution message");
                        return;
                    }
                    
                    // Update the model ID input to match current model
                    if (this.modelIdInput) {
                        this.modelIdInput.value = modelPath;
                    }
                    
                    // Extract ID and load model
                    const modelId = this.extractId(modelPath);
                    console.log("Extracted model ID for loading:", modelId);
                    
                    if (modelId) {
                        this.loadModel(modelId);
                    } else {
                        if (this.statusElement) {
                            this.statusElement.textContent = "Error: Could not extract valid model ID";
                            this.statusElement.style.color = "red";
                        }
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
        
        // Video Player Node - Similar improved structure
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
            
            // Function to extract ID from path - DEFINED AT CLASS LEVEL with improved regex
            nodeType.prototype.extractId = function(path) {
                console.log("Extracting ID from video path:", path);
                
                if (!path) {
                    console.log("Video path is empty");
                    return null;
                }
                
                // Convert to string if needed
                path = String(path).trim();
                
                // Try UUID pattern
                const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
                const match = path.match(uuidPattern);
                
                if (match) {
                    console.log("Found video UUID:", match[1]);
                    return match[1];
                }
                
                // Try filename pattern with more flexible matching
                const filenameMatch = path.match(/([^\/\\]+?)(?:_output)?(?:\.mp4|\.webm|\.mov)?$/i);
                if (filenameMatch) {
                    const filename = filenameMatch[1];
                    // Make sure we don't have just a file extension
                    if (filename && !filename.startsWith('.')) {
                        console.log("Found video filename ID:", filename);
                        return filename;
                    }
                }
                
                // Just return the path
                console.log("Using video path as ID:", path);
                return path;
            };
            
            // Function to load video - DEFINED AT CLASS LEVEL with better error handling
            nodeType.prototype.loadVideo = function(videoId) {
                console.log("Loading video:", videoId);
                
                if (!videoId || !this.iframe) {
                    console.log("Cannot load video - missing ID or iframe");
                    if (this.statusElement) {
                        this.statusElement.textContent = "Error: Cannot load video - missing ID or iframe";
                        this.statusElement.style.color = "red";
                    }
                    return;
                }
                
                this.lastVideoId = videoId;
                
                // Update status
                if (this.statusElement) {
                    this.statusElement.textContent = "Loading video...";
                    this.statusElement.style.color = "white";
                }
                
                // Set iframe source with cache busting for better reloading
                const timestamp = Date.now();
                const viewerUrl = `/trellis/simple-viewer/video/${videoId}?cache=${timestamp}`;
                console.log("Setting video iframe src to:", viewerUrl);
                this.iframe.src = viewerUrl;
            };
            
            // Create node UI elements with better error handling
            nodeType.prototype.onNodeCreated = function() {
                console.log("Creating Trellis Video Player Node");
                
                // Create container with improved styling
                const container = document.createElement("div");
                container.style.width = "100%";
                container.style.height = "250px";
                container.style.position = "relative";
                container.style.backgroundColor = "#222";
                container.style.borderRadius = "8px";
                container.style.overflow = "hidden";
                
                console.log("Creating video container");
                
                // Add status display with better positioning
                const status = document.createElement("div");
                status.style.position = "absolute";
                status.style.top = "10px";
                status.style.left = "10px";
                status.style.right = "10px";
                status.style.textAlign = "center";
                status.style.color = "white";
                status.style.background = "rgba(0,0,0,0.7)";
                status.style.padding = "5px";
                status.style.borderRadius = "4px";
                status.style.zIndex = "10";
                status.style.transition = "opacity 0.5s ease";
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
                
                // Add widget to node
                this.addWidget("preview", "video_preview", "", null, {
                    element: container
                });
                
                // Add video ID input widget
                this.videoIdInput = this.addWidget("text", "video_id", "Video ID", "", {
                    callback: (value) => {
                        console.log("Video ID input changed:", value);
                    }
                });
                
                // Fix for button widgets - needs proper callback assignment
                this.addWidget("button", "load_model", "Load Model", function() {
                    console.log("Model load button clicked");
                    const videoId = self.modelIdInput.value;
                    // Check if the modelId input has a value property or is itself the value
                    const videoValue = typeof videoId === 'object' && videoId !== null ? 
                                    (videoId.value || "") : (videoId || "");
                    
                    if (!videoValue.trim()) {
                        if (self.statusElement) {
                            self.statusElement.textContent = "Error: Please enter a model ID";
                            self.statusElement.style.color = "red";
                        }
                        return;
                    }
                    self.loadVideo(videoValue.trim());
                });


                // Add refresh button
                this.addWidget("button", "refresh", "Refresh", function() {
                    console.log("Video refresh button clicked");
                    if (self.lastVideoId) {
                        self.loadVideo(self.lastVideoId);
                    } else if (self.videoIdInput.value && self.videoIdInput.value.trim() !== "") {
                        self.loadVideo(self.videoIdInput.value.trim());
                    } else {
                        if (self.statusElement) {
                            self.statusElement.textContent = "Error: No video to refresh";
                            self.statusElement.style.color = "red";
                        }
                    }
                });
            };
            
            // Handle execution with improved path extraction and error handling
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
                        if (this.statusElement) {
                            this.statusElement.textContent = "Error: No video path found in execution message";
                            this.statusElement.style.color = "red";
                        }
                        console.log("No video path found in execution message");
                        return;
                    }
                    
                    // Update the video ID input to match current video
                    if (this.videoIdInput) {
                        this.videoIdInput.value = videoPath;
                    }
                    
                    // Extract ID and load video
                    const videoId = this.extractId(videoPath);
                    console.log("Extracted video ID for loading:", videoId);
                    
                    if (videoId) {
                        this.loadVideo(videoId);
                    } else {
                        if (this.statusElement) {
                            this.statusElement.textContent = "Error: Could not extract valid video ID";
                            this.statusElement.style.color = "red";
                        }
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