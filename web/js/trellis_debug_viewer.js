// Import app directly
import { app } from "/scripts/app.js";

// Simple debug function
function debug(...args) {
    console.log("[TrellisDebug]", ...args);
}

// Register extension
app.registerExtension({
    name: "Trellis.DebugViewer",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "TrellisDebugViewerNode") {
            debug("Registering debug viewer UI for", nodeData.name);
            
            // Make the node bigger
            const onDrawBackground = nodeType.prototype.onDrawBackground;
            nodeType.prototype.onDrawBackground = function(ctx) {
                if (onDrawBackground) {
                    onDrawBackground.apply(this, arguments);
                }
                this.size[1] = 400;
            };
            
            // Create the node UI
            nodeType.prototype.onNodeCreated = function() {
                debug("Creating debug viewer node UI");
                
                // Create container with bright background for visibility
                const container = document.createElement("div");
                container.style.width = "380px";
                container.style.height = "350px";
                container.style.backgroundColor = "#ff5722"; // Bright orange
                container.style.position = "relative";
                container.style.overflow = "hidden";
                container.style.display = "flex";
                container.style.justifyContent = "center";
                container.style.alignItems = "center";
                container.style.color = "white";
                container.style.fontWeight = "bold";
                container.style.fontSize = "20px";
                container.textContent = "Debug Container Visible";
                container.style.borderRadius = "6px";
                container.style.border = "3px solid #2196f3";
                
                // Status text
                const status = document.createElement("div");
                status.style.position = "absolute";
                status.style.top = "10px";
                status.style.left = "10px";
                status.style.backgroundColor = "rgba(0,0,0,0.7)";
                status.style.color = "white";
                status.style.padding = "5px 10px";
                status.style.borderRadius = "4px";
                status.style.zIndex = "100";
                status.textContent = "Status: Ready";
                container.appendChild(status);
                this.statusElement = status;
                
                // Add widget
                this.addWidget("preview", "debug_view", "", () => {}, {
                    element: container,
                    serialize: false
                });
                
                // Store container reference
                this.container = container;
                
                // Log to console for debugging
                debug("Debug viewer container created:", container);
                
                // Add a button to test interaction
                const testButton = document.createElement("button");
                testButton.textContent = "Test Visibility";
                testButton.style.position = "absolute";
                testButton.style.bottom = "10px";
                testButton.style.left = "50%";
                testButton.style.transform = "translateX(-50%)";
                testButton.style.padding = "8px 16px";
                testButton.style.borderRadius = "4px";
                testButton.style.border = "none";
                testButton.style.backgroundColor = "#2196f3";
                testButton.style.color = "white";
                testButton.style.fontWeight = "bold";
                testButton.style.cursor = "pointer";
                testButton.style.zIndex = "100";
                testButton.onclick = () => {
                    if (this.statusElement) {
                        this.statusElement.textContent = "Button clicked: " + new Date().toLocaleTimeString();
                    }
                    
                    // Toggle background color for visibility testing
                    if (container.style.backgroundColor === "rgb(255, 87, 34)") { // ff5722 in RGB
                        container.style.backgroundColor = "#4caf50"; // Green
                        container.textContent = "Color Changed - Container Visible";
                    } else {
                        container.style.backgroundColor = "#ff5722"; // Orange
                        container.textContent = "Debug Container Visible";
                    }
                    
                    debug("Debug viewer button clicked, container visible:", 
                          this.container.offsetParent !== null,
                          "Dimensions:", 
                          this.container.offsetWidth, 
                          this.container.offsetHeight);
                };
                container.appendChild(testButton);
            };
            
            // Handle node execution - test with model_path
            nodeType.prototype.onExecuted = function(message) {
                debug("Debug viewer node executed with message:", message);
                
                // Check for model_path in the message
                let modelPath = "";
                if (message?.model_path) {
                    modelPath = Array.isArray(message.model_path) 
                        ? message.model_path.join('') 
                        : message.model_path;
                } else if (message?.ui?.model_path) {
                    modelPath = Array.isArray(message.ui.model_path)
                        ? message.ui.model_path.join('')
                        : message.ui.model_path;
                }
                
                if (modelPath && this.statusElement) {
                    this.statusElement.textContent = "Model path: " + modelPath;
                    debug("Model path detected:", modelPath);
                }
            };
        }
    }
});

console.log("Trellis Debug Viewer registered");