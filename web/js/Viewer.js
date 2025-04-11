/**
 * ViewerUI - User interface controller for the ModelViewer
 */

function ViewerUI(viewer, options) {
  this.viewer = viewer;
  this.loader = null;
  
  // Default options
  this.options = {
    showControls: true,
    showStats: true,
    showProgress: true,
    showModelInfo: true,
    showFullscreen: true,
    controlsPosition: 'top-right', // 'top-right', 'top-left', 'bottom-right', 'bottom-left'
    theme: 'dark', // 'dark', 'light'
    progressBarColor: '#4285f4'
  };
  
  // Apply custom options
  if (options) {
    for (var key in options) {
      if (options.hasOwnProperty(key)) {
        this.options[key] = options[key];
      }
    }
  }
  
  // Create DOM elements
  this.elements = {
    controlsContainer: null,
    progressContainer: null,
    progressBar: null,
    progressBarInner: null,
    progressText: null,
    modelInfoPanel: null,
    messageOverlay: null
  };
  
  // Initialize UI
  this._initUI();
  this._attachViewerEvents();
}

/**
 * Initialize the UI elements
 */
ViewerUI.prototype._initUI = function() {
  // Insert styles
  this._insertStyles();
  
  // Create main containers
  this._createMainContainers();
  
  // Create UI components based on options
  if (this.options.showControls) {
    this._createControlsPanel();
  }
  
  if (this.options.showProgress) {
    this._createProgressBar();
  }
  
  if (this.options.showModelInfo) {
    this._createModelInfoPanel();
  }
  
  // Create message overlay (for errors, etc.)
  this._createMessageOverlay();
};

/**
 * Insert CSS styles for UI elements
 */
ViewerUI.prototype._insertStyles = function() {
  var styleElement = document.createElement('style');
  styleElement.id = 'model-viewer-styles';
  
  var css = `
    .model-viewer-container {
      position: relative;
      overflow: hidden;
    }
    
    .model-viewer-theme-dark {
      --viewer-bg-color: rgba(0, 0, 0, 0.7);
      --viewer-border-color: rgba(255, 255, 255, 0.2);
      --viewer-text-color: #ffffff;
      --viewer-accent-color: ${this.options.progressBarColor};
    }
    
    .model-viewer-theme-light {
      --viewer-bg-color: rgba(255, 255, 255, 0.7);
      --viewer-border-color: rgba(0, 0, 0, 0.2);
      --viewer-text-color: #000000;
      --viewer-accent-color: ${this.options.progressBarColor};
    }
    
    .model-viewer-controls {
      position: absolute;
      z-index: 10;
      padding: 10px;
      background-color: var(--viewer-bg-color);
      border-radius: 5px;
      backdrop-filter: blur(5px);
      font-family: sans-serif;
      font-size: 14px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
      color: var(--viewer-text-color);
      transition: opacity 0.3s;
    }
    
    .model-viewer-controls.top-left {
      top: 10px;
      left: 10px;
    }
    
    .model-viewer-controls.top-right {
      top: 10px;
      right: 10px;
    }
    
    .model-viewer-controls.bottom-left {
      bottom: 10px;
      left: 10px;
    }
    
    .model-viewer-controls.bottom-right {
      bottom: 10px;
      right: 10px;
    }
    
    .model-viewer-control-group {
      margin-bottom: 10px;
    }
    
    .model-viewer-control-group h3 {
      margin: 0 0 5px 0;
      font-size: 12px;
      text-transform: uppercase;
      opacity: 0.7;
    }
    
    .model-viewer-button {
      background-color: var(--viewer-accent-color);
      color: white;
      border: none;
      border-radius: 3px;
      padding: 5px 10px;
      margin: 2px;
      cursor: pointer;
      font-size: 12px;
    }
    
    .model-viewer-button:hover {
      opacity: 0.9;
    }
    
    .model-viewer-button:active {
      opacity: 0.8;
    }
    
    .model-viewer-progress {
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
      padding: 10px;
      background-color: var(--viewer-bg-color);
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: transform 0.3s;
      z-index: 10;
      transform: translateY(100%);
    }
    
    .model-viewer-progress.visible {
      transform: translateY(0);
    }
    
    .model-viewer-progress-bar {
      width: 100%;
      height: 4px;
      background-color: rgba(255, 255, 255, 0.2);
      border-radius: 2px;
      overflow: hidden;
      margin-bottom: 5px;
    }
    
    .model-viewer-progress-bar-inner {
      height: 100%;
      width: 0%;
      background-color: var(--viewer-accent-color);
      transition: width 0.2s;
    }
    
    .model-viewer-progress-text {
      font-size: 12px;
      font-family: sans-serif;
      color: var(--viewer-text-color);
    }
    
    .model-viewer-info {
      position: absolute;
      bottom: 10px;
      left: 10px;
      padding: 10px;
      background-color: var(--viewer-bg-color);
      border-radius: 5px;
      backdrop-filter: blur(5px);
      font-family: sans-serif;
      font-size: 12px;
      color: var(--viewer-text-color);
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
      max-width: 200px;
      opacity: 0.9;
    }
    
    .model-viewer-info h3 {
      margin: 0 0 5px 0;
      font-size: 14px;
    }
    
    .model-viewer-info div {
      margin-bottom: 3px;
    }
    
    .model-viewer-message {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      padding: 15px 20px;
      background-color: var(--viewer-bg-
