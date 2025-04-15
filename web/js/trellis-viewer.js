// Enhanced trellis-viewer.js with detailed debugging

import { app } from "/scripts/app.js";

const DEBUG = true;
function debug(...args) {
    if (DEBUG) {
        console.log("[Trellis Debug]", ...args);
        // Send to backend for logging
        logToBackend("JavaScript", args);
    }
}

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

// Function to extract ID from path with detailed logging
function extractId(path, type = "model") {
    debug(`Extracting ID from path: ${path} for type: ${type}`);
    
    if (!path) {
        debug("Path is empty or null");
        return null;
    }
    
    // Handle array input
    if (Array.isArray(path)) {
        debug("Path is an array, joining...");
        path = path.join('');
    }
    
    // Extract UUID
    const uuidPattern = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/i;
    const match = path.match(uuidPattern);
    
    if (match) {
        debug(`UUID pattern matched: ${match[1]}`);
        return match[1];
    }
    
    // Extract from filename pattern
    const extensions = type === "model" ? "glb|gltf" : "mp4|webm|mov";
    const filenamePattern = new RegExp(`([^\/]+)_output\.(${extensions})$`);
    const filenameMatch = path.match(filenamePattern);
    
    if (filenameMatch) {
        debug(`Filename pattern matched: ${filenameMatch[1]}`);
        return filenameMatch[1];
    }
    
    // Fall back to original path
    debug(`No patterns matched, using original: ${path}`);
    return path;
}

// Function to get proper media URL
function getMediaUrl(id, type = "model") {
    const url = `/trellis/simple-viewer/${type}/${id}`;
    debug(`Generated media URL: ${url}`);
    return url;
}

// Register extension with detailed logging
app.registerExtension({
    name: "Trellis.MediaViewer",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        debug(`Processing node: ${nodeData.name}`);
        
        // Model Viewer Node
        if (nodeData.name === "TrellisModelViewerNode" || nodeData.name === "TrellisModelViewer") {
            debug(`Setting up model viewer node: ${nodeData.name}`);
            
            // Resize node
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                this.size[1] = 300;
                debug(`Resized model viewer node to height: ${this.size[1]}`);
            };
            
            // Node creation
            nodeType.prototype.onNodeCreated = function() {
                debug("Creating TrellisModelViewerNode");
                
                try {
                    // Create container
                    const container = document.createElement("div");
                    container.style.width = "380px";
                    container.style.height = "280px";
                    container.style.backgroundColor = "#222";
                    container.style.borderRadius = "8px";
                    container.style.overflow = "hidden";
                    container.style.position = "relative";
                    
                    debug("Created container element");
                    
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
                    status.textContent = "Model Viewer Ready";
                    container.appendChild(status);
                    this.statusText = status;
                    
                    debug("Added status text to container");
                    
                    // Create iframe (initially with a test page)
                    const iframe = document.createElement("iframe");
                    iframe.style.width = "100%";
                    iframe.style.height = "100%";
                    iframe.style.border = "none";
                    
                    // Set a test source to verify iframe works
                    iframe.src = "data:text/html;charset=utf-8," + encodeURIComponent(
                        "<html><body style='background:#333; color:white; font-family:Arial; padding:10px;'>" +
                        "<h2>Model Viewer Ready</h2>" +
                        "<p>Waiting for model data...</p>" +
                        "</body></html>"
                    );
                    
                    container.appendChild(iframe);
                    this.iframe = iframe;
                    
                    debug("Added iframe to container with test content");
                    
                    // Add widget
                    this.addWidget("preview", "model_preview", "", () => {}, {
                        element: container,
                        serialize: false
                    });
                    
                    debug("Added widget to node");
                    
                    // Try to see if widget is added correctly
                    setTimeout(() => {
                        debug(`Widget count: ${this.widgets?.length}`);
                        debug(`Container in DOM: ${container.isConnected}`);
                    }, 500);
                    
                    // Add refresh button
                    this.addWidget("button", "refresh", "Refresh", () => {
                        debug("Refresh button clicked");
                        if (this.lastModelId) {
                            this.loadModel(this.lastModelId);
                        } else {
                            debug("No model ID to refresh");
                        }
                    });
                    
                } catch (error) {
                    console.error("Error creating model viewer:", error);
                    debug(`Error in model viewer creation: ${error.message}`);
                    debug(error.stack);
                }
            };
            
            // Add method to load models
            nodeType.prototype.loadModel = function(modelId) {
                debug(`loadModel called with ID: ${modelId}`);
                
                if (!modelId) {
                    debug("Model ID is empty, can't load");
                    return;
                }
                
                if (!this.iframe) {
                    debug("Iframe not available");
                    return;
                }
                
                this.lastModelId = modelId;
                
                // Update status
                if (this.statusText) {
                    this.statusText.textContent = "Loading model...";
                    this.statusText.style.opacity = "1";
                    debug("Updated status text to loading");
                }
                
                // Get URL for model viewer
                const viewerUrl = getMediaUrl(modelId, "model");
                
                debug(`Setting iframe src to: ${viewerUrl}`);
                this.iframe.src = viewerUrl;
            };
            
            // Override onExecuted
            const originalOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                debug("Model viewer onExecuted called with:", message);
                
                // Call original if it exists
                if (originalOnExecuted) {
                    debug("Calling original onExecuted");
                    originalOnExecuted.apply(this, arguments);
                }
                
                try {
                    // Extract model path with detailed logging
                    let modelPath = null;
                    
                    if (Array.isArray(message)) {
                        debug("Message is an array, using first element");
                        modelPath = message[0];
                    } else if (message?.model_path) {
                        debug("Found model_path in message");
                        modelPath = message.model_path;
                    } else if (message?.ui?.model_path) {
                        debug("Found ui.model_path in message");
                        modelPath = message.ui.model_path;
                    } else if (message?.result) {
                        debug("Found result in message");
                        modelPath = Array.isArray(message.result) ? message.result[0] : message.result;
                    } else {
                        debug("Could not find model path in message:", message);
                    }
                    
                    debug(`Extracted model path: ${modelPath}`);
                    
                    if (!modelPath) {
                        debug("No model path found, can't continue");
                        return;
                    }
                    
                    // Get model ID
                    const modelId = extractId(modelPath, "model");
                    debug(`Extracted model ID: ${modelId}`);
                    
                    if (!modelId) {
                        debug("Failed to extract model ID");
                        return;
                    }
                    
                    // Load the model
                    this.loadModel(modelId);
                    
                } catch (error) {
                    console.error("Error in model viewer execution:", error);
                    debug(`Error in model viewer execution: ${error.message}`);
                    debug(error.stack);
                    
                    if (this.statusText) {
                        this.statusText.textContent = `Error: ${error.message}`;
                        this.statusText.style.color = "red";
                    }
                }
            };
        }
        
        // Video Player Node - Similar approach with detailed logging
        if (nodeData.name === "TrellisVideoPlayerNode") {
            debug(`Setting up video player node: ${nodeData.name}`);
            
            // Resize node
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                this.size[1] = 300;
                debug(`Resized video player node to height: ${this.size[1]}`);
            };
            
            // Node creation
            nodeType.prototype.onNodeCreated = function() {
                debug("TrellisVideoPlayerNode: onNodeCreated called");
                
                try {
                    // Create container
                    const container = document.createElement("div");
                    container.style.width = "380px";
                    container.style.height = "280px";
                    container.style.backgroundColor = "#222";
                    container.style.borderRadius = "8px";
                    container.style.overflow = "hidden";
                    container.style.position = "relative";
                    
                    debug("Created container element for video player");
                    
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
                    status.textContent = "Video Player Ready";
                    container.appendChild(status);
                    this.statusText = status;
                    
                    debug("Added status text to video player container");
                    
                    // Create iframe (initially with a test page)
                    const iframe = document.createElement("iframe");
                    iframe.style.width = "100%";
                    iframe.style.height = "100%";
                    iframe.style.border = "none";
                    
                    // Set a test source to verify iframe works
                    iframe.src = "data:text/html;charset=utf-8," + encodeURIComponent(
                        "<html><body style='background:#333; color:white; font-family:Arial; padding:10px;'>" +
                        "<h2>Video Player Ready</h2>" +
                        "<p>Waiting for video data...</p>" +
                        "</body></html>"
                    );
                    
                    container.appendChild(iframe);
                    this.iframe = iframe;
                    
                    debug("Added iframe to video player container with test content");
                    
                    // Add widget
                    this.addWidget("preview", "video_preview", "", () => {}, {
                        element: container,
                        serialize: false
                    });
                    
                    debug("Added widget to video player node");
                    
                    // Try to see if widget is added correctly
                    setTimeout(() => {
                        debug(`Video widget count: ${this.widgets?.length}`);
                        debug(`Video container in DOM: ${container.isConnected}`);
                    }, 500);
                    
                    // Add refresh button
                    this.addWidget("button", "refresh", "Refresh", () => {
                        debug("Video refresh button clicked");
                        if (this.lastVideoId) {
                            this.loadVideo(this.lastVideoId);
                        } else {
                            debug("No video ID to refresh");
                        }
                    });
                    
                } catch (error) {
                    console.error("Error in TrellisVideoPlayerNode creation:", error);
                    debug(`Error in video player creation: ${error.message}`);
                    debug(error.stack);
                }
            };
            
            // Add method to load videos
            nodeType.prototype.loadVideo = function(videoId) {
                debug(`loadVideo called with ID: ${videoId}`);
                
                if (!videoId) {
                    debug("Video ID is empty, can't load");
                    return;
                }
                
                if (!this.iframe) {
                    debug("Video iframe not available");
                    return;
                }
                
                this.lastVideoId = videoId;
                
                // Update status
                if (this.statusText) {
                    this.statusText.textContent = "Loading video...";
                    this.statusText.style.opacity = "1";
                    debug("Updated video status text to loading");
                }
                
                // Get URL for video viewer
                const viewerUrl = getMediaUrl(videoId, "video");
                
                debug(`Setting video iframe src to: ${viewerUrl}`);
                this.iframe.src = viewerUrl;
            };
            
            // Override onExecuted
            const originalOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                debug("Video player onExecuted called with:", message);
                
                // Call original if it exists
                if (originalOnExecuted) {
                    debug("Calling original video onExecuted");
                    originalOnExecuted.apply(this, arguments);
                }
                
                try {
                    // Extract video path with detailed logging
                    let videoPath = null;
                    
                    if (Array.isArray(message)) {
                        debug("Video message is an array, using first element");
                        videoPath = message[0];
                    } else if (message?.video_path) {
                        debug("Found video_path in message");
                        videoPath = message.video_path;
                    } else if (message?.ui?.video_path) {
                        debug("Found ui.video_path in message");
                        videoPath = message.ui.video_path;
                    } else if (message?.result) {
                        debug("Found result in video message");
                        videoPath = Array.isArray(message.result) ? message.result[0] : message.result;
                    } else {
                        debug("Could not find video path in message:", message);
                    }
                    
                    debug(`Extracted video path: ${videoPath}`);
                    
                    if (!videoPath) {
                        debug("No video path found, can't continue");
                        return;
                    }
                    
                    // Get video ID
                    const videoId = extractId(videoPath, "video");
                    debug(`Extracted video ID: ${videoId}`);
                    
                    if (!videoId) {
                        debug("Failed to extract video ID");
                        return;
                    }
                    
                    // Load the video
                    this.loadVideo(videoId);
                    
                } catch (error) {
                    console.error("Error in video player execution:", error);
                    debug(`Error in video player execution: ${error.message}`);
                    debug(error.stack);
                    
                    if (this.statusText) {
                        this.statusText.textContent = `Error: ${error.message}`;
                        this.statusText.style.color = "red";
                    }
                }
            };
        }
    }
});

