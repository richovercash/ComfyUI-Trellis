import { app } from "../../scripts/app.js";

// Load Three.js dynamically
async function loadScript(url) {
    return new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${url}"]`)) {
            return resolve();
        }
        const script = document.createElement('script');
        script.src = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Register extension
app.registerExtension({
    name: "Trellis.Preview3D",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "TrellisPreview3D") return;
        
        // Load Three.js if needed
        try {
            await loadScript('https://cdn.jsdelivr.net/npm/three@0.150.1/build/three.min.js');
            await loadScript('https://cdn.jsdelivr.net/npm/three@0.150.1/examples/js/controls/OrbitControls.js'); 
            await loadScript('https://cdn.jsdelivr.net/npm/three@0.150.1/examples/js/loaders/GLTFLoader.js');
        } catch (error) {
            console.error("Failed to load Three.js libraries:", error);
        }
        
        // Add custom widget
        const onDrawBackground = nodeType.prototype.onDrawBackground;
        nodeType.prototype.onDrawBackground = function(ctx) {
            if (onDrawBackground) {
                onDrawBackground.apply(this, arguments);
            }
            
            // Create status display
            if (!this.statusEl) {
                this.statusEl = document.createElement("div");
                this.statusEl.style.position = "absolute";
                this.statusEl.style.top = "0";
                this.statusEl.style.left = "0";
                this.statusEl.style.width = "100%";
                this.statusEl.style.padding = "10px";
                this.statusEl.style.boxSizing = "border-box";
                this.statusEl.style.background = "rgba(0,0,0,0.5)";
                this.statusEl.style.color = "#ccc";
                this.statusEl.style.fontSize = "12px";
                this.statusEl.style.zIndex = "10";
                this.statusEl.textContent = "Waiting for model...";
                
                // Attach to DOM
                document.body.appendChild(this.statusEl);
                this.statusEl.style.display = "none";
            }
            
            // Position status element
            const [x, y] = this.pos;
            this.statusEl.style.left = (x + 10) + "px";
            this.statusEl.style.top = (y + 60) + "px";
        };
        
        // Handle node execution
        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function(message) {
            if (onExecuted) {
                onExecuted.apply(this, arguments);
            }
            
            // Show status
            if (this.statusEl) {
                this.statusEl.style.display = "block";
                
                if (!message.ui) {
                    this.statusEl.textContent = "No data received";
                    return;
                }
                
                if (message.ui.status === "error") {
                    this.statusEl.textContent = message.ui.message || "Error loading file";
                    this.statusEl.style.color = "#ff5555";
                } 
                else if (message.ui.status === "waiting") {
                    this.statusEl.textContent = "Waiting for file path...";
                    this.statusEl.style.color = "#ccc";
                }
                else if (message.ui.preview) {
                    const preview = message.ui.preview;
                    this.statusEl.textContent = `File ready: ${preview.file_type} (ID: ${preview.file_id})`;
                    this.statusEl.style.color = "#55ff55";
                    
                    // Add view button if not already present
                    if (!this.viewBtn) {
                        this.viewBtn = document.createElement("button");
                        this.viewBtn.textContent = "View in Browser";
                        this.viewBtn.style.marginLeft = "10px";
                        this.viewBtn.style.padding = "2px 8px";
                        this.viewBtn.style.background = "#335";
                        this.viewBtn.style.border = "1px solid #557";
                        this.viewBtn.style.borderRadius = "4px";
                        this.viewBtn.style.color = "#fff";
                        this.viewBtn.style.cursor = "pointer";
                        
                        this.statusEl.appendChild(this.viewBtn);
                    }
                    
                    // Update button action
                    this.viewBtn.onclick = () => {
                        const url = `/trellis/preview/files/${preview.file_id}`;
                        window.open(url, '_blank');
                    };
                }
            }
        };
    }
});