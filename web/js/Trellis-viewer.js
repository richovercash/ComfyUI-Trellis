/**
 * TrellisViewer - Main integration module for the 3D model viewer
 * 
 * This module provides a simple API for integrating the 3D model viewer
 * into a node-based system.
 */

var TrellisViewer = (function() {
  // Private variables
  var viewers = {};
  var nextId = 1;
  
  /**
   * Create a new viewer instance
   * 
   * @param {Object} options - Viewer configuration options
   * @param {HTMLElement|string} options.container - Container element or selector
   * @param {Object} options.viewer - Viewer options
   * @param {Object} options.ui - UI options
   * @returns {Object} Viewer instance API
   */
  function create(options) {
    // Validate options
    if (!options || !options.container) {
      throw new Error('Container is required');
    }
    
    // Get container element
    var container;
    if (typeof options.container === 'string') {
      container = document.querySelector(options.container);
      if (!container) {
        throw new Error('Container element not found: ' + options.container);
      }
    } else {
      container = options.container;
    }
    
    // Create viewer options
    var viewerOptions = Object.assign({
      container: container
    }, options.viewer || {});
    
    // Create UI options
    var uiOptions = options.ui || {};
    
    // Generate viewer ID
    var id = 'trellis-viewer-' + nextId++;
    
    // Create ModelViewer instance
    var viewer = new ModelViewer(viewerOptions);
    
    // Create ModelLoader instance
    var loader = new ModelLoader(viewer);
    
    // Create ViewerUI instance if not disabled
    var ui = null;
    if (options.ui !== false) {
      ui = new ViewerUI(viewer, uiOptions);
    }
    
    // Store viewer instance
    viewers[id] = {
      id: id,
      viewer: viewer,
      loader: loader,
      ui: ui
    };
    
    // Return public API
    return {
      /**
       * Get viewer ID
       * @returns {string} Viewer ID
       */
      getId: function() {
        return id;
      },
      
      /**
       * Load a model
       * 
       * @param {string} url - Model URL
       * @param {Object} options - Loading options
       * @returns {Object} Viewer API for chaining
       */
      loadModel: function(url, options) {
        loader.load(url, options);
        return this;
      },
      
      /**
       * Set background color
       * 
       * @param {string|number} color - Color in hex format
       * @returns {Object} Viewer API for chaining
       */
      setBackground: function(color) {
        viewer.setBackgroundColor(color);
        return this;
      },
      
      /**
       * Set auto-rotation
       * 
       * @param {boolean} enabled - Whether auto-rotation should be enabled
       * @returns {Object} Viewer API for chaining
       */
      setAutoRotate: function(enabled) {
        viewer.setAutoRotate(enabled);
        return this;
      },
      
      /**
       * Reset camera to initial position
       * 
       * @returns {Object} Viewer API for chaining
       */
      resetCamera: function() {
        viewer.resetCamera();
        return this;
      },
      
      /**
       * Center model in scene
       * 
       * @returns {Object} Viewer API for chaining
       */
      centerModel: function() {
        viewer.centerModel();
        return this;
      },
      
      /**
       * Add an event listener
       * 
       * @param {string} event - Event name
       * @param {Function} callback - Event callback
       * @returns {Object} Viewer API for chaining
       */
      on: function(event, callback) {
        viewer.addEventListener(event, callback);
        return this;
      },
      
      /**
       * Remove an event listener
       * 
       * @param {string} event - Event name
       * @param {Function} callback - Event callback
       * @returns {Object} Viewer API for chaining
       */
      off: function(event, callback) {
        viewer.removeEventListener(event, callback);
        return this;
      },
      
      /**
       * Show a message
       * 
       * @param {string} message - Message text
       * @param {number} duration - Duration in milliseconds
       * @returns {Object} Viewer API for chaining
       */
      showMessage: function(message, duration) {
        if (ui) {
          ui._showMessage(message, duration);
        }
        return this;
      },
      
      /**
       * Set UI theme
       * 
       * @param {string} theme - Theme name ('dark' or 'light')
       * @returns {Object} Viewer API for chaining
       */
      setTheme: function(theme) {
        if (ui) {
          ui.setTheme(theme);
        }
        return this;
      },
      
      /**
       * Resize viewer
       * 
       * @returns {Object} Viewer API for chaining
       */
      resize: function() {
        viewer._handleResize();
        return this;
      },
      
      /**
       * Get direct access to internal viewer
       * 
       * @returns {ModelViewer} Internal viewer instance
       */
      getViewer: function() {
        return viewer;
      },
      
      /**
       * Get direct access to loader
       * 
       * @returns {ModelLoader} Internal loader instance
       */
      getLoader: function() {
        return loader;
      },
      
      /**
       * Get direct access to UI
       * 
       * @returns {ViewerUI} Internal UI instance
       */
      getUI: function() {
        return ui;
      },
      
      /**
       * Destroy the viewer and free resources
       */
      destroy: function() {
        // Dispose of viewer
        viewer.dispose();
        
        // Remove from viewers list
        delete viewers[id];
      }
    };
  }
  
  /**
   * Get a viewer instance by ID
   * 
   * @param {string} id - Viewer ID
   * @returns {Object} Viewer instance API or null if not found
   */
  function get(id) {
    return viewers[id] ? viewers[id].api : null;
  }
  
  /**
   * Get all viewer instances
   * 
   * @returns {Object} Object with viewer IDs as keys and viewer APIs as values
   */
  function getAll() {
    var result = {};
    for (var id in viewers) {
      if (viewers.hasOwnProperty(id)) {
        result[id] = viewers[id].api;
      }
    }
    return result;
  }
  
  // Public API
  return {
    create: create,
    get: get,
    getAll: getAll
  };
})();