// import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "Trellis.ModelViewer",
    
    async nodeCreated(node) {
        // Only process our viewer nodes
        if (node.type !== "TrellisModelViewerNode" && node.type !== "TrellisVideoPlayerNode") return;
        
        // Add container for viewer
        const previewContainer = document.createElement("div");
        previewContainer.style.width = "100%";
        previewContainer.style.height = "400px";
        previewContainer.style.backgroundColor = "#1a1a1a";
        previewContainer.style.borderRadius = "8px";
        previewContainer.style.overflow = "hidden";
        previewContainer.style.position = "relative";
        
        // Add placeholder text
        const placeholderText = document.createElement("div");
        placeholderText.style.position = "absolute";
        placeholderText.style.top = "50%";
        placeholderText.style.left = "50%";
        placeholderText.style.transform = "translate(-50%, -50%)";
        placeholderText.style.color = "#666";
        placeholderText.style.fontSize = "14px";
        placeholderText.textContent = "Connect a file path to view";
        
        previewContainer.appendChild(placeholderText);
        
        // Add to node
        node.addCustomWidget({
            name: "preview",
            element: previewContainer
        });
        
        // Keep references
        node.previewContainer = previewContainer;
        node.placeholderText = placeholderText;
        
        // Handle node execution
        const onExecuted = node.onExecuted;
        node.onExecuted = function(message) {
            if (onExecuted) {
                onExecuted.apply(this, arguments);
            }
            
            // Check if we got HTML content
            if (message && message.html) {
                placeholderText.style.display = "none";
                
                // Get file path from message
                const filePath = message.viewer_path || "";
                
                // Register file for viewing
                const fileId = Date.now().toString(); // Generate unique ID
                
                // Make sure registry exists
                if (!app.nodeTrellisFiles) {
                    app.nodeTrellisFiles = {};
                }
                
                // Store file info
                app.nodeTrellisFiles[fileId] = {
                    path: filePath,
                    type: filePath.endsWith(".mp4") ? "video" : "model"
                };
                
                // Create iframe for viewer
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.src = `/trellis/view/${fileId}`;
                
                // Clear container
                previewContainer.innerHTML = "";
                previewContainer.appendChild(iframe);
                
                // Add Open in New Window button
                const openButton = document.createElement("button");
                openButton.textContent = "Open in New Window";
                openButton.style.position = "absolute";
                openButton.style.bottom = "10px";
                openButton.style.right = "10px";
                openButton.style.zIndex = "100";
                openButton.style.backgroundColor = "#333";
                openButton.style.color = "#fff";
                openButton.style.border = "none";
                openButton.style.borderRadius = "4px";
                openButton.style.padding = "5px 10px";
                openButton.style.cursor = "pointer";
                
                openButton.onclick = () => {
                    window.open(`/trellis/view/${fileId}`, "_blank");
                };
                
                previewContainer.appendChild(openButton);
            }
        };
    }
});
