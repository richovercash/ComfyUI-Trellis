import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Trellis.Viewer",
    async setup() {
        console.log("Trellis Viewer extension loaded");
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "TrellisModelViewerNode" || 
            nodeData.name === "Trellis3DModelViewer" || 
            nodeData.name === "TrellisSimpleGLBViewer") {
            
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                const r = onExecuted ? onExecuted.apply(this, arguments) : undefined;
                if (message.glb_path) {
                    const pathParts = message.glb_path.split("/");
                    const filename = pathParts[pathParts.length - 1];
                    const modelId = filename.split("_")[0];
                    
                    // Create viewer UI
                    if (!this.viewer) {
                        this.viewer = document.createElement("div");
                        this.viewer.style.width = "100%";
                        this.viewer.style.height = "300px";
                        this.element.appendChild(this.viewer);
                    }
                    
                    this.viewer.innerHTML = `
                        <iframe 
                            src="/trellis/view-model/${modelId}" 
                            style="width: 100%; height: 100%; border: none;"
                        ></iframe>
                    `;
                }
                return r;
            };
        }
        
        if (nodeData.name === "TrellisVideoPlayerNode" || 
            nodeData.name === "TrellisVideoPlayer") {
            
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                const r = onExecuted ? onExecuted.apply(this, arguments) : undefined;
                if (message.video_path) {
                    const pathParts = message.video_path.split("/");
                    const filename = pathParts[pathParts.length - 1];
                    const videoId = filename.split("_")[0];
                    
                    // Create viewer UI
                    if (!this.viewer) {
                        this.viewer = document.createElement("div");
                        this.viewer.style.width = "100%";
                        this.viewer.style.height = "300px";
                        this.element.appendChild(this.viewer);
                    }
                    
                    this.viewer.innerHTML = `
                        <iframe 
                            src="/trellis/view-video/${videoId}" 
                            style="width: 100%; height: 100%; border: none;"
                        ></iframe>
                    `;
                }
                return r;
            };
        }
    }
});