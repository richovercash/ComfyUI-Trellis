/**
 * ModelLoader - A model loading system for the ModelViewer
 */

function ModelLoader(viewer) {
  this.viewer = viewer;
  this.loaders = {};
  this.currentUrl = null;
  this.currentModelType = null;
  
  // Initialize loaders
  this._initLoaders();
}

/**
 * Initialize loaders for different file formats
 */
ModelLoader.prototype._initLoaders = function() {
  // Basic loaders
  this.loaders.obj = new THREE.OBJLoader(this.viewer.loadingManager);
  this.loaders.mtl = new THREE.MTLLoader(this.viewer.loadingManager);
  
  // GLB/GLTF loader with Draco compression support
  this.loaders.gltf = new THREE.GLTFLoader(this.viewer.loadingManager);
  
  var dracoLoader = new THREE.DRACOLoader();
  dracoLoader.setDecoderPath('https://unpkg.com/three@latest/examples/jsm/libs/draco/gltf/');
  this.loaders.gltf.setDRACOLoader(dracoLoader);
};

/**
 * Load a 3D model from URL
 */
ModelLoader.prototype.load = function(url, options) {
  // Default options
  var defaultOptions = {
    centerModel: true,
    scaleToFit: true,
    scale: 1.0
  };
  
  var loadOptions = options || {};
  
  // Apply defaults for missing options
  for (var key in defaultOptions) {
    if (defaultOptions.hasOwnProperty(key) && loadOptions[key] === undefined) {
      loadOptions[key] = defaultOptions[key];
    }
  }
  
  // Clear previous model
  this.viewer.clearScene();
  this.currentUrl = url;
  
  // Determine file type from extension
  var fileExtension = this._getFileExtension(url).toLowerCase();
  this.currentModelType = fileExtension;
  
  // Trigger load start event
  this.viewer._triggerEvent('loadStart', { 
    url: url, 
    fileType: fileExtension 
  });
  

  // MODIFY THIS PART:
  // Check if this is a relative path to a downloaded model
  if (url.indexOf('/') === 0 || url.indexOf('http') === 0) {
    // URL is already absolute or starts with a slash
  } else {
    // For relative paths, check if it's in the trellis_downloads folder
    if (url.indexOf('trellis_downloads') === -1) {
      // Add the path to ComfyUI's trellis_downloads directory
      url = 'file/trellis_downloads/' + url;
    }
  }

  // Load model based on file type
  switch (fileExtension) {
    case 'obj':
      this._loadOBJ(url, loadOptions);
      break;
    case 'glb':
    case 'gltf':
      this._loadGLTF(url, loadOptions);
      break;
    default:
      var error = new Error('Unsupported file format: ' + fileExtension);
      this.viewer._triggerEvent('loadError', { url: url, error: error });
      console.error(error);
  }
  
  return this;
};

/**
 * Get file extension from URL
 */
ModelLoader.prototype._getFileExtension = function(url) {
  return url.split('.').pop().split('?')[0];
};

/**
 * Get directory path from URL
 */
ModelLoader.prototype._getDirectoryPath = function(url) {
  var parts = url.split('/');
  parts.pop();
  return parts.join('/') + '/';
};

/**
 * Get filename without extension
 */
ModelLoader.prototype._getFilenameWithoutExtension = function(url) {
  var filename = url.split('/').pop();
  return filename.substring(0, filename.lastIndexOf('.'));
};

/**
 * Load OBJ model
 */
ModelLoader.prototype._loadOBJ = function(url, options) {
  // Try to load MTL file first
  var mtlUrl = url.substring(0, url.lastIndexOf('.')) + '.mtl';
  var directoryPath = this._getDirectoryPath(url);
  
  var self = this;
  
  // First try to load materials if they exist
  fetch(mtlUrl)
    .then(function(response) {
      if (!response.ok) {
        throw new Error('MTL file not found, loading OBJ without materials');
      }
      return self._loadOBJWithMTL(url, mtlUrl, directoryPath, options);
    })
    .catch(function() {
      // If MTL loading fails, load OBJ without materials
      self._loadOBJWithoutMTL(url, options);
    });
};

/**
 * Load OBJ with MTL materials
 */
ModelLoader.prototype._loadOBJWithMTL = function(objUrl, mtlUrl, directoryPath, options) {
  var mtlLoader = this.loaders.mtl;
  mtlLoader.setPath(directoryPath);
  
  var self = this;
  
  mtlLoader.load(mtlUrl, function(materials) {
    materials.preload();
    
    var objLoader = self.loaders.obj;
    objLoader.setMaterials(materials);
    objLoader.setPath(directoryPath);
    
    objLoader.load(objUrl, function(object) {
      self._processLoadedModel(object, options);
    });
  });
};

/**
 * Load OBJ without MTL materials
 */
ModelLoader.prototype._loadOBJWithoutMTL = function(url, options) {
  var objLoader = this.loaders.obj;
  var self = this;
  
  objLoader.load(url, function(object) {
    // Set default materials with vertex colors
    object.traverse(function(node) {
      if (node.isMesh && node.material && !node.material.map) {
        node.material.vertexColors = true;
      }
    });
    
    self._processLoadedModel(object, options);
  });
};

/**
 * Load GLTF/GLB model
 */
ModelLoader.prototype._loadGLTF = function(url, options) {
  var loader = this.loaders.gltf;
  var self = this;
  
  loader.load(url, function(gltf) {
    var model = gltf.scene;
    
    // Handle animations if present
    if (gltf.animations && gltf.animations.length) {
      self.viewer.mixer = new THREE.AnimationMixer(model);
      
      for (var i = 0; i < gltf.animations.length; i++) {
        self.viewer.mixer.clipAction(gltf.animations[i]).play();
      }
      
      self.viewer._triggerEvent('animationsLoaded', {
        count: gltf.animations.length,
        animations: gltf.animations
      });
    }
    
    self._processLoadedModel(model, options);
  });
};

/**
 * Process a loaded model (scale, center, add to scene)
 */
ModelLoader.prototype._processLoadedModel = function(model, options) {
  // Store reference to current model
  this.viewer.currentModel = model;
  
  // Scale model
  if (options.scaleToFit) {
    this._scaleModelToFit(model);
  } else if (options.scale !== 1.0) {
    model.scale.set(options.scale, options.scale, options.scale);
  }
  
  // Center model if requested
  if (options.centerModel) {
    this._centerModel(model);
  }
  
  // Add model to scene
  this.viewer.scene.add(model);
  
  // Trigger load complete event with model info
  var modelInfo = this._getModelInfo(model);
  this.viewer._triggerEvent('modelLoaded', {
    model: model,
    type: this.currentModelType,
    url: this.currentUrl,
    info: modelInfo
  });
};

/**
 * Scale model to fit in view
 */
ModelLoader.prototype._scaleModelToFit = function(model) {
  // Create bounding box
  var box = new THREE.Box3().setFromObject(model);
  var size = box.getSize(new THREE.Vector3());
  
  // Get max dimension
  var maxDim = Math.max(size.x, size.y, size.z);
  
  // Scale based on max dimension (aiming for a standardized size)
  var targetSize = 5.0; // Standard target size
  var scale = targetSize / maxDim;
  
  model.scale.set(scale, scale, scale);
};

/**
 * Center model in scene
 */
ModelLoader.prototype._centerModel = function(model) {
  // Create bounding box
  var box = new THREE.Box3().setFromObject(model);
  var center = box.getCenter(new THREE.Vector3());
  
  // Move model so its center is at (0,0,0)
  model.position.sub(center);
  
  // Update controls target
  if (this.viewer.controls) {
    this.viewer.controls.target.set(0, 0, 0);
    this.viewer.controls.update();
  }
};

/**
 * Get information about the model
 */
ModelLoader.prototype._getModelInfo = function(model) {
  var vertexCount = 0;
  var faceCount = 0;
  var materialCount = 0;
  var materials = new Set();
  
  // Traverse model to count vertices, faces, and materials
  model.traverse(function(object) {
    if (object.isMesh) {
      if (object.geometry) {
        if (object.geometry.attributes.position) {
          vertexCount += object.geometry.attributes.position.count;
        }
        
        if (object.geometry.index) {
          faceCount += object.geometry.index.count / 3;
        } else if (object.geometry.attributes.position) {
          faceCount += object.geometry.attributes.position.count / 3;
        }
      }
      
      if (object.material) {
        if (Array.isArray(object.material)) {
          for (var i = 0; i < object.material.length; i++) {
            materials.add(object.material[i]);
          }
        } else {
          materials.add(object.material);
        }
      }
    }
  });
  
  materialCount = materials.size;
  
  // Create bounding box
  var box = new THREE.Box3().setFromObject(model);
  var size = box.getSize(new THREE.Vector3());
  
  return {
    vertexCount: vertexCount,
    faceCount: Math.floor(faceCount),
    materialCount: materialCount,
    dimensions: {
      width: size.x,
      height: size.y,
      depth: size.z
    }
  };
};
