/**
 * ComfyUI Integration Example
 * 
 * This example shows how to integrate the Trellis 3D Model Viewer
 * into a system like ComfyUI.
 */

// Example ComfyUI node implementation for model viewing
class ModelViewerNode {
    constructor() {
      this.nodeId = 'model-viewer-' + Math.floor(Math.random() * 10000);
      this.element = null;
      this.viewer = null;
      this.modelPath = null;
      this.initialized = false;
      
      // Node configuration
      this.config = {
        title: '3D Model Viewer',
        type: 'modelViewer',
        inputs: [
          { name: 'modelPath', type: 'string' }
        ],
        outputs: [],
        properties: [
          { name: 'backgroundColor', type: 'color', default: '#222222' },
          { name: 'autoRotate', type: 'boolean', default: true },
          { name: 'theme', type: 'select', options: ['dark', 'light'], default: 'dark' }
        ]
      };
    }
    
    /**
     * Initialize the node UI
     * @param {HTMLElement} element - The node's DOM element
     */
    initialize(element) {
      this.element = element;
      
      // Create viewer container
      var container = document.createElement('div');
      container.className = 'model-viewer-container';
      container.style.width = '100%';
      container.style.height = '300px';
      container.style.background = '#333';
      
      // Append container to node element
      element.appendChild(container);
      
      // Initialize viewer
      this.viewer = TrellisNodeIntegration.initializeViewer(this.nodeId, container, {
        viewer: {
          backgroundColor: this.hexToRgb(this.config.properties[0].default),
          controlsAutoRotate: this.config.properties[1].default
        },
        ui: {
          theme: this.config.properties[2].default
        }
      });
      
      this.initialized = true;
      
      // Handle events
      this.viewer.on('loadError', function(data) {
        console.error('Error loading model in node ' + this.nodeId + ':', data.error);
      }.bind(this));
    }
    
    /**
     * Process node inputs and update the viewer
     * @param {Object} inputs - Node inputs
     */
    process(inputs) {
      if (!this.initialized) {
        console.warn('Node not initialized: ' + this.nodeId);
        return;
      }
      
      // Get model path from inputs
      var modelPath = inputs.modelPath;
      
      // Check if model path has changed
      if (modelPath !== this.modelPath) {
        // Update model in viewer
        TrellisNodeIntegration.loadModel(this.nodeId, modelPath);
        this.modelPath = modelPath;
      }
    }
    
    /**
     * Update node properties
     * @param {Object} properties - Node properties
     */
    updateProperties(properties) {
      if (!this.initialized || !this.viewer) {
        return;
      }
      
      // Update background color
      if (properties.backgroundColor) {
        this.viewer.setBackground(properties.backgroundColor);
      }
      
      // Update auto rotate
      if (properties.autoRotate !== undefined) {
        this.viewer.setAutoRotate(properties.autoRotate);
      }
      
      // Update theme
      if (properties.theme) {
        this.viewer.setTheme(properties.theme);
      }
    }
    
    /**
     * Clean up resources when node is removed
     */
    cleanup() {
      if (this.initialized) {
        TrellisNodeIntegration.removeNode(this.nodeId);
        this.initialized = false;
      }
    }
    
    /**
     * Convert hex color to RGB value
     * @param {string} hex - Hex color string
     * @returns {number} RGB color value
     * @private
     */
    hexToRgb(hex) {
      // Remove # if present
      hex = hex.replace(/^#/, '');
      
      // Parse hex values
      var r = parseInt(hex.substring(0, 2), 16) / 255;
      var g = parseInt(hex.substring(2, 4), 16) / 255;
      var b = parseInt(hex.substring(4, 6), 16) / 255;
      
      // Create RGB color
      return (r << 16) | (g << 8) | b;
    }
  }
  
  // Example of registering the node in a ComfyUI-like system
  function registerModelViewerNode() {
    if (typeof app !== 'undefined' && app.registerNodeType) {
      app.registerNodeType('ModelViewer', ModelViewerNode);
      console.log('ModelViewer node registered');
    } else {
      console.warn('app.registerNodeType not available - ModelViewer node not registered');
    }
  }
  
  // Example of how to initialize the node system
  function initializeNodeSystem() {
    // Create some UI elements for demonstration
    
    // 1. Container for node system
    var container = document.createElement('div');
    container.id = 'node-system';
    container.style.width = '100%';
    container.style.height = '100vh';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.backgroundColor = '#1e1e1e';
    document.body.appendChild(container);
    
    // 2. Header
    var header = document.createElement('div');
    header.style.padding = '10px';
    header.style.backgroundColor = '#333';
    header.style.color = 'white';
    header.innerHTML = '<h2>ComfyUI-style Integration Demo</h2>';
    container.appendChild(header);
    
    // 3. Main area
    var main = document.createElement('div');
    main.style.flex = '1';
    main.style.display = 'flex';
    main.style.overflow = 'hidden';
    container.appendChild(main);
    
    // 4. Node panel (left sidebar)
    var nodePanel = document.createElement('div');
    nodePanel.style.width = '250px';
    nodePanel.style.backgroundColor = '#252525';
    nodePanel.style.padding = '10px';
    nodePanel.style.color = 'white';
    nodePanel.innerHTML = '<h3>Nodes</h3>';
    main.appendChild(nodePanel);
    
    // 5. Canvas (main area)
    var canvas = document.createElement('div');
    canvas.style.flex = '1';
    canvas.style.position = 'relative';
    canvas.style.overflow = 'auto';
    main.appendChild(canvas);
    
    // 6. Example node
    var nodeElement = document.createElement('div');
    nodeElement.style.width = '300px';
    nodeElement.style.backgroundColor = '#444';
    nodeElement.style.borderRadius = '5px';
    nodeElement.style.position = 'absolute';
    nodeElement.style.top = '50px';
    nodeElement.style.left = '50px';
    nodeElement.style.boxShadow = '0 3px 10px rgba(0, 0, 0, 0.3)';
    
    // Node header
    var nodeHeader = document.createElement('div');
    nodeHeader.style.backgroundColor = '#555';
    nodeHeader.style.borderTopLeftRadius = '5px';
    nodeHeader.style.borderTopRightRadius = '5px';
    nodeHeader.style.padding = '8px';
    nodeHeader.style.color = 'white';
    nodeHeader.style.fontWeight = 'bold';
    nodeHeader.textContent = '3D Model Viewer';
    nodeElement.appendChild(nodeHeader);
    
    // Node content
    var nodeContent = document.createElement('div');
    nodeContent.style.padding = '10px';
    nodeElement.appendChild(nodeContent);
    
    canvas.appendChild(nodeElement);
    
    // Create node instance
    var node = new ModelViewerNode();
    node.initialize(nodeContent);
    
    // Simulate input
    var modelPath = 'models/example.glb';
    node.process({ modelPath: modelPath });
    
    // Add model selection buttons
    var buttonContainer = document.createElement('div');
    buttonContainer.style.marginTop = '10px';
    buttonContainer.style.display = 'flex';
    buttonContainer.style.gap = '5px';
    nodeContent.appendChild(buttonContainer);
    
    var models = [
      { name: 'GLB Example', path: 'models/example.glb' },
      { name: 'OBJ Cube', path: 'models/cube.obj' }
    ];
    
    models.forEach(function(model) {
      var button = document.createElement('button');
      button.textContent = model.name;
      button.style.flex = '1';
      button.style.backgroundColor = '#4285f4';
      button.style.color = 'white';
      button.style.border = 'none';
      button.style.padding = '5px';
      button.style.borderRadius = '3px';
      button.style.cursor = 'pointer';
      
      button.addEventListener('click', function() {
        node.process({ modelPath: model.path });
      });
      
      buttonContainer.appendChild(button);
    });
    
    // Add property controls
    var propertiesContainer = document.createElement('div');
    propertiesContainer.style.marginTop = '10px';
    nodeContent.appendChild(propertiesContainer);
    
    // Background color control
    var bgColorContainer = document.createElement('div');
    bgColorContainer.style.display = 'flex';
    bgColorContainer.style.alignItems = 'center';
    bgColorContainer.style.marginBottom = '5px';
    
    var bgColorLabel = document.createElement('label');
    bgColorLabel.textContent = 'Background:';
    bgColorLabel.style.color = 'white';
    bgColorLabel.style.flex = '1';
    
    var bgColorInput = document.createElement('input');
    bgColorInput.type = 'color';
    bgColorInput.value = '#222222';
    bgColorInput.addEventListener('input', function() {
      node.updateProperties({ backgroundColor: this.value });
    });
    
    bgColorContainer.appendChild(bgColorLabel);
    bgColorContainer.appendChild(bgColorInput);
    propertiesContainer.appendChild(bgColorContainer);
    
    // Auto rotate control
    var autoRotateContainer = document.createElement('div');
    autoRotateContainer.style.display = 'flex';
    autoRotateContainer.style.alignItems = 'center';
    autoRotateContainer.style.marginBottom = '5px';
    
    var autoRotateLabel = document.createElement('label');
    autoRotateLabel.textContent = 'Auto Rotate:';
    autoRotateLabel.style.color = 'white';
    autoRotateLabel.style.flex = '1';
    
    var autoRotateInput = document.createElement('input');
    autoRotateInput.type = 'checkbox';
    autoRotateInput.checked = true;
    autoRotateInput.addEventListener('change', function() {
      node.updateProperties({ autoRotate: this.checked });
    });
    
    autoRotateContainer.appendChild(autoRotateLabel);
    autoRotateContainer.appendChild(autoRotateInput);
    propertiesContainer.appendChild(autoRotateContainer);
    
    // Theme control
    var themeContainer = document.createElement('div');
    themeContainer.style.display = 'flex';
    themeContainer.style.alignItems = 'center';
    
    var themeLabel = document.createElement('label');
    themeLabel.textContent = 'Theme:';
    themeLabel.style.color = 'white';
    themeLabel.style.flex = '1';
    
    var themeSelect = document.createElement('select');
    themeSelect.style.backgroundColor = '#333';
    themeSelect.style.color = 'white';
    themeSelect.style.border = '1px solid #555';
    themeSelect.style.padding = '3px';
    
    var darkOption = document.createElement('option');
    darkOption.value = 'dark';
    darkOption.textContent = 'Dark';
    themeSelect.appendChild(darkOption);
    
    var lightOption = document.createElement('option');
    lightOption.value = 'light';
    lightOption.textContent = 'Light';
    themeSelect.appendChild(lightOption);
    
    themeSelect.addEventListener('change', function() {
      node.updateProperties({ theme: this.value });
    });
    
    themeContainer.appendChild(themeLabel);
    themeContainer.appendChild(themeSelect);
    propertiesContainer.appendChild(themeContainer);
  }
  
  // Initialize demo when document is loaded
  document.addEventListener('DOMContentLoaded', initializeNodeSystem);