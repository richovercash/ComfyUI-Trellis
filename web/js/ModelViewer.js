/**
 * ModelViewer - A modular Three.js-based 3D model viewer
 */

function ModelViewer(options) {
  // Default options
  this.options = {
    container: null,
    backgroundColor: 0x000000,
    useEnvironment: true,
    cameraFov: 45,
    cameraNear: 0.1,
    cameraFar: 1000,
    cameraPosition: [5, 2, 8],
    cameraTarget: [0, 0.5, 0],
    controlsEnablePan: true,
    controlsEnableZoom: true,
    controlsEnableRotate: true,
    controlsEnableDamping: true,
    controlsDampingFactor: 0.05,
    controlsAutoRotate: false,
    controlsAutoRotateSpeed: 0.5,
    rendererAntialias: true,
    rendererAlpha: true
  };

  // Override with provided options
  if (options) {
    for (var key in options) {
      if (options.hasOwnProperty(key)) {
        this.options[key] = options[key];
      }
    }
  }

  // Validate container
  if (!this.options.container) {
    throw new Error('Container element is required');
  }

  // Initialize properties
  this.container = this.options.container;
  this.scene = null;
  this.camera = null;
  this.renderer = null;
  this.controls = null;
  this.mixer = null;
  this.clock = null;
  this.currentModel = null;
  this.loadingManager = null;
  this.eventListeners = {};

  // Initialize components
  this._initRenderer();
  this._initScene();
  this._initCamera();
  this._initControls();
  this._initLights();
  this._initClock();
  this._initLoadingManager();
  
  // Handle window resize
  var self = this;
  window.addEventListener('resize', function() {
    self._handleResize();
  });
  
  // Start animation loop
  this._animate();
}

/**
 * Initialize the WebGL renderer
 */
ModelViewer.prototype._initRenderer = function() {
  this.renderer = new THREE.WebGLRenderer({
    antialias: this.options.rendererAntialias,
    alpha: this.options.rendererAlpha
  });
  
  this.renderer.setPixelRatio(window.devicePixelRatio);
  this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
  this.renderer.outputEncoding = THREE.sRGBEncoding;
  this.renderer.physicallyCorrectLights = true;
  this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
  this.renderer.toneMappingExposure = 1.0;
  
  this.container.appendChild(this.renderer.domElement);
};

/**
 * Initialize the scene and environment
 */
ModelViewer.prototype._initScene = function() {
  this.scene = new THREE.Scene();
  this.scene.background = new THREE.Color(this.options.backgroundColor);
  
  if (this.options.useEnvironment) {
    var pmremGenerator = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmremGenerator.fromScene(
      new THREE.RoomEnvironment(this.renderer), 0.04
    ).texture;
  }
};

/**
 * Initialize the camera
 */
ModelViewer.prototype._initCamera = function() {
  this.camera = new THREE.PerspectiveCamera(
    this.options.cameraFov,
    this.container.clientWidth / this.container.clientHeight,
    this.options.cameraNear,
    this.options.cameraFar
  );
  
  this.camera.position.set(
    this.options.cameraPosition[0],
    this.options.cameraPosition[1],
    this.options.cameraPosition[2]
  );
  
  this.scene.add(this.camera);
};

/**
 * Initialize orbit controls
 */
ModelViewer.prototype._initControls = function() {
  this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
  
  this.controls.target.set(
    this.options.cameraTarget[0],
    this.options.cameraTarget[1],
    this.options.cameraTarget[2]
  );
  
  this.controls.enablePan = this.options.controlsEnablePan;
  this.controls.enableZoom = this.options.controlsEnableZoom;
  this.controls.enableRotate = this.options.controlsEnableRotate;
  this.controls.enableDamping = this.options.controlsEnableDamping;
  this.controls.dampingFactor = this.options.controlsDampingFactor;
  this.controls.autoRotate = this.options.controlsAutoRotate;
  this.controls.autoRotateSpeed = this.options.controlsAutoRotateSpeed;
  
  this.controls.update();
};

/**
 * Initialize scene lighting
 */
ModelViewer.prototype._initLights = function() {
  // Add ambient light
  var ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  this.scene.add(ambientLight);
  
  // Add directional light (main light)
  var directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(1, 2, 3);
  this.scene.add(directionalLight);
  
  // Add back light
  var backLight = new THREE.DirectionalLight(0xffffff, 0.5);
  backLight.position.set(-1, 2, -3);
  this.scene.add(backLight);
  
  // Add point light to camera
  var pointLight = new THREE.PointLight(0xffffff, 0.5);
  this.camera.add(pointLight);
};

/**
 * Initialize animation clock
 */
ModelViewer.prototype._initClock = function() {
  this.clock = new THREE.Clock();
};

/**
 * Initialize loading manager with progress tracking
 */
ModelViewer.prototype._initLoadingManager = function() {
  var self = this;
  
  this.loadingManager = new THREE.LoadingManager();
  
  this.loadingManager.onProgress = function(url, loaded, total) {
    var progress = (loaded / total) * 100;
    self._triggerEvent('loadProgress', { url: url, loaded: loaded, total: total, progress: progress });
  };
  
  this.loadingManager.onError = function(url) {
    self._triggerEvent('loadError', { url: url });
  };
  
  this.loadingManager.onLoad = function() {
    self._triggerEvent('loadComplete');
  };
};

/**
 * Handle window resize
 */
ModelViewer.prototype._handleResize = function() {
  var width = this.container.clientWidth;
  var height = this.container.clientHeight;
  
  this.camera.aspect = width / height;
  this.camera.updateProjectionMatrix();
  
  this.renderer.setSize(width, height);
  this._triggerEvent('resize', { width: width, height: height });
};

/**
 * Animation loop
 */
ModelViewer.prototype._animate = function() {
  var self = this;
  
  requestAnimationFrame(function() {
    self._animate();
  });
  
  var delta = this.clock.getDelta();
  
  // Update mixer if it exists (for animations)
  if (this.mixer) {
    this.mixer.update(delta);
  }
  
  // Update controls
  if (this.controls) {
    this.controls.update();
  }
  
  // Render scene
  this.renderer.render(this.scene, this.camera);
  
  this._triggerEvent('animate', { delta: delta });
};

/**
 * Add an event listener
 */
ModelViewer.prototype.addEventListener = function(event, callback) {
  if (!this.eventListeners[event]) {
    this.eventListeners[event] = [];
  }
  this.eventListeners[event].push(callback);
  
  return this;
};

/**
 * Remove an event listener
 */
ModelViewer.prototype.removeEventListener = function(event, callback) {
  if (this.eventListeners[event]) {
    this.eventListeners[event] = this.eventListeners[event].filter(function(cb) {
      return cb !== callback;
    });
  }
  
  return this;
};

/**
 * Trigger an event
 */
ModelViewer.prototype._triggerEvent = function(event, data) {
  if (this.eventListeners[event]) {
    for (var i = 0; i < this.eventListeners[event].length; i++) {
      this.eventListeners[event][i](data);
    }
  }
};

/**
 * Set background color
 */
ModelViewer.prototype.setBackgroundColor = function(color) {
  this.scene.background = new THREE.Color(color);
  return this;
};

/**
 * Toggle camera auto-rotation
 */
ModelViewer.prototype.setAutoRotate = function(enabled) {
  this.controls.autoRotate = enabled;
  return this;
};

/**
 * Set auto-rotation speed
 */
ModelViewer.prototype.setAutoRotateSpeed = function(speed) {
  this.controls.autoRotateSpeed = speed;
  return this;
};

/**
 * Reset camera to initial position
 */
ModelViewer.prototype.resetCamera = function() {
  this.camera.position.set(
    this.options.cameraPosition[0],
    this.options.cameraPosition[1],
    this.options.cameraPosition[2]
  );
  
  this.controls.target.set(
    this.options.cameraTarget[0],
    this.options.cameraTarget[1],
    this.options.cameraTarget[2]
  );
  
  this.controls.update();
  
  return this;
};

/**
 * Center model in scene
 */
ModelViewer.prototype.centerModel = function() {
  if (!this.currentModel) return this;
  
  var box = new THREE.Box3().setFromObject(this.currentModel);
  var center = box.getCenter(new THREE.Vector3());
  
  // Update controls target
  this.controls.target.copy(center);
  this.controls.update();
  
  return this;
};

/**
 * Clear the scene (remove all models)
 */
ModelViewer.prototype.clearScene = function() {
  // Keep lights and camera, remove everything else
  var objectsToRemove = [];
  
  this.scene.traverse(function(object) {
    if (object !== this.scene && 
        !(object instanceof THREE.Camera) && 
        !(object instanceof THREE.Light)) {
      objectsToRemove.push(object);
    }
  }.bind(this));
  
  for (var i = 0; i < objectsToRemove.length; i++) {
    this.scene.remove(objectsToRemove[i]);
  }
  
  this.currentModel = null;
  
  if (this.mixer) {
    this.mixer.stopAllAction();
    this.mixer = null;
  }
  
  return this;
};

/**
 * Dispose of the viewer and all its resources
 */
ModelViewer.prototype.dispose = function() {
  // Remove event listeners
  window.removeEventListener('resize', this._handleResize);
  
  // Dispose of Three.js objects
  this.clearScene();
  
  if (this.renderer) {
    this.renderer.dispose();
    this.container.removeChild(this.renderer.domElement);
  }
  
  if (this.controls) {
    this.controls.dispose();
  }
  
  // Clear references
  this.scene = null;
  this.camera = null;
  this.renderer = null;
  this.controls = null;
  this.mixer = null;
  this.clock = null;
  this.currentModel = null;
  this.loadingManager = null;
  this.eventListeners = {};
};
