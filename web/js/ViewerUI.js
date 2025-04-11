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
 * Create main UI containers
 */
ViewerUI.prototype._createMainContainers = function() {
  var container = this.viewer.container;
  container.classList.add('model-viewer-container');
  container.classList.add('model-viewer-theme-' + this.options.theme);
};

/**
 * Create controls panel
 */
ViewerUI.prototype._createControlsPanel = function() {
  // Create controls container
  var controlsContainer = document.createElement('div');
  controlsContainer.className = 'model-viewer-controls ' + this.options.controlsPosition;
  this.viewer.container.appendChild(controlsContainer);
  this.elements.controlsContainer = controlsContainer;
  
  // Create camera controls group
  var cameraGroup = document.createElement('div');
  cameraGroup.className = 'model-viewer-control-group';
  
  var cameraTitle = document.createElement('h3');
  cameraTitle.textContent = 'Camera';
  cameraGroup.appendChild(cameraTitle);
  
  // Reset camera button
  var resetCameraButton = document.createElement('button');
  resetCameraButton.className = 'model-viewer-button';
  resetCameraButton.textContent = 'Reset Camera';
  resetCameraButton.addEventListener('click', this._onResetCamera.bind(this));
  cameraGroup.appendChild(resetCameraButton);
  
  // Center model button
  var centerModelButton = document.createElement('button');
  centerModelButton.className = 'model-viewer-button';
  centerModelButton.textContent = 'Center Model';
  centerModelButton.addEventListener('click', this._onCenterModel.bind(this));
  cameraGroup.appendChild(centerModelButton);
  
  controlsContainer.appendChild(cameraGroup);
  
  // Create animation controls group
  var animationGroup = document.createElement('div');
  animationGroup.className = 'model-viewer-control-group';
  
  var animationTitle = document.createElement('h3');
  animationTitle.textContent = 'Animation';
  animationGroup.appendChild(animationTitle);
  
  // Auto-rotate toggle
  var autoRotateButton = document.createElement('button');
  autoRotateButton.className = 'model-viewer-button';
  autoRotateButton.textContent = this.viewer.controls.autoRotate ? 'Stop Rotation' : 'Auto Rotate';
  autoRotateButton.addEventListener('click', this._onToggleAutoRotate.bind(this));
  this.elements.autoRotateButton = autoRotateButton;
  animationGroup.appendChild(autoRotateButton);
  
  controlsContainer.appendChild(animationGroup);
  
  // Create display controls group
  var displayGroup = document.createElement('div');
  displayGroup.className = 'model-viewer-control-group';
  
  var displayTitle = document.createElement('h3');
  displayTitle.textContent = 'Display';
  displayGroup.appendChild(displayTitle);
  
  // Background color picker
  var colorPickerLabel = document.createElement('label');
  colorPickerLabel.textContent = 'Background: ';
  colorPickerLabel.style.color = 'var(--viewer-text-color)';
  
  var colorPicker = document.createElement('input');
  colorPicker.type = 'color';
  colorPicker.value = '#' + this.viewer.scene.background.getHexString();
  colorPicker.addEventListener('input', this._onColorChange.bind(this));
  this.elements.colorPicker = colorPicker;
  
  colorPickerLabel.appendChild(colorPicker);
  displayGroup.appendChild(colorPickerLabel);
  
  controlsContainer.appendChild(displayGroup);
  
  // Create fullscreen button if enabled
  if (this.options.showFullscreen) {
    var fullscreenButton = document.createElement('button');
    fullscreenButton.className = 'model-viewer-button';
    fullscreenButton.textContent = 'Fullscreen';
    fullscreenButton.addEventListener('click', this._onToggleFullscreen.bind(this));
    this.elements.fullscreenButton = fullscreenButton;
    
    controlsContainer.appendChild(document.createElement('br'));
    controlsContainer.appendChild(fullscreenButton);
  }
};

/**
 * Create progress bar
 */
ViewerUI.prototype._createProgressBar = function() {
  var progressContainer = document.createElement('div');
  progressContainer.className = 'model-viewer-progress';
  this.viewer.container.appendChild(progressContainer);
  this.elements.progressContainer = progressContainer;
  
  var progressBar = document.createElement('div');
  progressBar.className = 'model-viewer-progress-bar';
  progressContainer.appendChild(progressBar);
  this.elements.progressBar = progressBar;
  
  var progressBarInner = document.createElement('div');
  progressBarInner.className = 'model-viewer-progress-bar-inner';
  progressBar.appendChild(progressBarInner);
  this.elements.progressBarInner = progressBarInner;
  
  var progressText = document.createElement('div');
  progressText.className = 'model-viewer-progress-text';
  progressText.textContent = 'Loading...';
  progressContainer.appendChild(progressText);
  this.elements.progressText = progressText;
};

/**
 * Create model info panel
 */
ViewerUI.prototype._createModelInfoPanel = function() {
  var infoPanel = document.createElement('div');
  infoPanel.className = 'model-viewer-info';
  infoPanel.style.display = 'none';
  this.viewer.container.appendChild(infoPanel);
  this.elements.modelInfoPanel = infoPanel;
};

/**
 * Create message overlay
 */
ViewerUI.prototype._createMessageOverlay = function() {
  var messageOverlay = document.createElement('div');
  messageOverlay.className = 'model-viewer-message';
  this.viewer.container.appendChild(messageOverlay);
  this.elements.messageOverlay = messageOverlay;
};

/**
 * Attach viewer events
 */
ViewerUI.prototype._attachViewerEvents = function() {
  var self = this;
  
  // Load progress event
  this.viewer.addEventListener('loadProgress', function(data) {
    self._updateProgress(data.progress, 'Loading: ' + Math.round(data.progress) + '%');
  });
  
  // Load start event
  this.viewer.addEventListener('loadStart', function(data) {
    self._showProgress();
    self._updateProgress(0, 'Loading ' + data.fileType.toUpperCase() + ' model...');
  });
  
  // Load complete event
  this.viewer.addEventListener('loadComplete', function() {
    self._hideProgress();
  });
  
  // Model loaded event
  this.viewer.addEventListener('modelLoaded', function(data) {
    self._updateModelInfo(data.model, data.info);
  });
  
  // Load error event
  this.viewer.addEventListener('loadError', function(data) {
    self._showMessage('Error loading model: ' + (data.error ? data.error.message : 'Unknown error'));
  });
};

/**
 * Handle reset camera button click
 */
ViewerUI.prototype._onResetCamera = function() {
  this.viewer.resetCamera();
};

/**
 * Handle center model button click
 */
ViewerUI.prototype._onCenterModel = function() {
  this.viewer.centerModel();
};

/**
 * Handle auto-rotate toggle button click
 */
ViewerUI.prototype._onToggleAutoRotate = function() {
  var autoRotate = !this.viewer.controls.autoRotate;
  this.viewer.setAutoRotate(autoRotate);
  this.elements.autoRotateButton.textContent = autoRotate ? 'Stop Rotation' : 'Auto Rotate';
};

/**
 * Handle background color change
 */
ViewerUI.prototype._onColorChange = function(event) {
  this.viewer.setBackgroundColor(event.target.value);
};

/**
 * Handle fullscreen toggle
 */
ViewerUI.prototype._onToggleFullscreen = function() {
  var container = this.viewer.container;
  
  if (!document.fullscreenElement) {
    if (container.requestFullscreen) {
      container.requestFullscreen();
    } else if (container.mozRequestFullScreen) { // Firefox
      container.mozRequestFullScreen();
    } else if (container.webkitRequestFullscreen) { // Chrome, Safari and Opera
      container.webkitRequestFullscreen();
    } else if (container.msRequestFullscreen) { // IE/Edge
      container.msRequestFullscreen();
    }
    this.elements.fullscreenButton.textContent = 'Exit Fullscreen';
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.mozCancelFullScreen) { // Firefox
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) { // Chrome, Safari and Opera
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) { // IE/Edge
      document.msExitFullscreen();
    }
    this.elements.fullscreenButton.textContent = 'Fullscreen';
  }
};

/**
 * Update progress bar
 */
ViewerUI.prototype._updateProgress = function(progress, text) {
  if (!this.elements.progressContainer) return;
  
  this.elements.progressBarInner.style.width = progress + '%';
  
  if (text && this.elements.progressText) {
    this.elements.progressText.textContent = text;
  }
};

/**
 * Show progress bar
 */
ViewerUI.prototype._showProgress = function() {
  if (!this.elements.progressContainer) return;
  this.elements.progressContainer.classList.add('visible');
};

/**
 * Hide progress bar
 */
ViewerUI.prototype._hideProgress = function() {
  if (!this.elements.progressContainer) return;
  
  // Add a small delay before hiding
  var self = this;
  setTimeout(function() {
    self.elements.progressContainer.classList.remove('visible');
  }, 500);
};

/**
 * Update model info panel
 */
ViewerUI.prototype._updateModelInfo = function(model, info) {
  if (!this.elements.modelInfoPanel || !info) return;
  
  var infoPanel = this.elements.modelInfoPanel;
  infoPanel.innerHTML = '';
  
  // Add title
  var title = document.createElement('h3');
  title.textContent = 'Model Information';
  infoPanel.appendChild(title);
  
  // Add vertex count
  var vertices = document.createElement('div');
  vertices.textContent = 'Vertices: ' + info.vertexCount.toLocaleString();
  infoPanel.appendChild(vertices);
  
  // Add face count
  var faces = document.createElement('div');
  faces.textContent = 'Faces: ' + info.faceCount.toLocaleString();
  infoPanel.appendChild(faces);
  
  // Add material count
  var materials = document.createElement('div');
  materials.textContent = 'Materials: ' + info.materialCount;
  infoPanel.appendChild(materials);
  
  // Add dimensions
  var dimensions = document.createElement('div');
  dimensions.textContent = 'Dimensions: ' + 
    info.dimensions.width.toFixed(2) + ' x ' + 
    info.dimensions.height.toFixed(2) + ' x ' + 
    info.dimensions.depth.toFixed(2);
  infoPanel.appendChild(dimensions);
  
  // Show the info panel
  infoPanel.style.display = 'block';
};

/**
 * Show a message in the overlay
 */
ViewerUI.prototype._showMessage = function(message, duration) {
  if (!this.elements.messageOverlay) return;
  
  this.elements.messageOverlay.textContent = message;
  this.elements.messageOverlay.style.display = 'block';
  
  // Hide after duration if specified
  if (duration) {
    var self = this;
    setTimeout(function() {
      self._hideMessage();
    }, duration);
  }
};

/**
 * Hide the message overlay
 */
ViewerUI.prototype._hideMessage = function() {
  if (!this.elements.messageOverlay) return;
  this.elements.messageOverlay.style.display = 'none';
};

/**
 * Set the theme
 */
ViewerUI.prototype.setTheme = function(theme) {
  if (theme !== 'dark' && theme !== 'light') {
    console.warn('Invalid theme: ' + theme + '. Must be "dark" or "light".');
    return;
  }
  
  // Remove current theme class
  this.viewer.container.classList.remove('model-viewer-theme-' + this.options.theme);
  
  // Set new theme
  this.options.theme = theme;
  this.viewer.container.classList.add('model-viewer-theme-' + theme);
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
      background-color: var(--viewer-bg-color);
      border-radius: 5px;
      backdrop-filter: blur(5px);
      font-family: sans-serif;
      font-size: 14px;
      color: var(--viewer-text-color);
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
      max-width: 80%;
      text-align: center;
      z-index: 20;
      display: none;
    }