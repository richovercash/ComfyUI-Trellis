// The correct way to import app and api in ComfyUI
import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";


// Register Trellis viewer extension
app.registerExtension({
    name: "Trellis.Viewer",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "TrellisModelViewerNode") {
            // Add custom preview and UI elements to the TrellisModelViewerNode
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                // Create viewer container
                const viewer = document.createElement("div");
                viewer.style.width = "100%";
                viewer.style.height = "300px";
                viewer.style.backgroundColor = "#222";
                viewer.style.borderRadius = "8px";
                viewer.style.overflow = "hidden";
                viewer.innerHTML = `<div style="padding: 10px; color: white;">Load a model to view</div>`;
                this.viewerElement = viewer;
                
                this.widgets.push({
                    element: viewer,
                    type: "trellis_viewer",
                    computeSize: () => [this.size[0], 300],
                });
                
                return result;
            };
            
            // Override process method to update viewer with new model
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = async function(message) {
                const result = onExecuted ? onExecuted.apply(this, arguments) : undefined;
                
                if (message.glb_path) {
                    // Extract session ID from path
                    const pathParts = message.glb_path.split("/");
                    const filename = pathParts[pathParts.length - 1];
                    const sessionId = filename.split("_")[0];
                    
                    if (sessionId) {
                        // Load the 3D viewer
                        this.viewerElement.innerHTML = `
                            <iframe 
                                src="/trellis-viewer/model-viewer.html?model_id=${sessionId}" 
                                style="width: 100%; height: 100%; border: none;"
                            ></iframe>
                        `;
                    }
                }
                
                return result;
            };
        }
        
        if (nodeData.name === "TrellisVideoPlayerNode") {
            // Add custom preview and UI elements to the TrellisVideoPlayerNode
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                // Create video container
                const videoContainer = document.createElement("div");
                videoContainer.style.width = "100%";
                videoContainer.style.height = "300px";
                videoContainer.style.backgroundColor = "#222";
                videoContainer.style.borderRadius = "8px";
                videoContainer.style.overflow = "hidden";
                videoContainer.innerHTML = `<div style="padding: 10px; color: white;">Load a video to view</div>`;
                this.videoElement = videoContainer;
                
                this.widgets.push({
                    element: videoContainer,
                    type: "trellis_video_viewer",
                    computeSize: () => [this.size[0], 300],
                });
                
                return result;
            };
            
            // Override process method to update viewer with new video
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = async function(message) {
                const result = onExecuted ? onExecuted.apply(this, arguments) : undefined;
                
                if (message.video_path) {
                    // Extract session ID from path
                    const pathParts = message.video_path.split("/");
                    const filename = pathParts[pathParts.length - 1];
                    const sessionId = filename.split("_")[0];
                    
                    if (sessionId) {
                        // Load the video player
                        this.videoElement.innerHTML = `
                            <iframe 
                                src="/trellis-viewer/video-player.html?video_id=${sessionId}" 
                                style="width: 100%; height: 100%; border: none;"
                            ></iframe>
                        `;
                    }
                }
                
                return result;
            };
        }
    }
});