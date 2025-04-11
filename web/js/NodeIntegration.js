/**
 * NodeIntegration - Integration module for node-based systems
 * 
 * This module provides functions for creating and manipulating model viewers
 * in a node-based system like ComfyUI.
 */

var TrellisNodeIntegration = (function() {
    // Store node references
    var nodes = {};
    
    /**
     * Initialize a viewer for a node
     * 
     * @param {string} nodeId - The ID of the node
     * @param {HTMLElement} container - The container element for the viewer
     * @param {Object} options - Viewer options
     * @returns {Object} Viewer instance
     */
    function initializeViewer(nodeId, container, options) {
      // Create default options
      var defaultOptions = {
        container: container,
        viewer: {
          backgroundColor: 0x222222,
          controlsAutoRotate: false
        },
        ui: {
          showStats: true,
          showModelInfo: true,
          theme: 'dark'
        }
      };
      
      // Merge with provided options
      var viewerOptions = mergeOptions(defaultOptions, options || {});
      
      // Create viewer
      var viewer = TrellisViewer.create(viewerOptions);
      
      // Store node reference
      nodes[nodeId] = {
        id: nodeId,
        viewer: viewer,
        modelPath: null,
        lastUpdate: Date.now()
      };
      
      return viewer;
    }
    
    /**
     * Load a model into a viewer node
     * 
     * @param {string} nodeId - The ID of the node
     * @param {string} modelPath - Path to the 3D model
     * @param {Object} options - Loading options
     * @returns {boolean} Success status
     */
    function loadModel(nodeId, modelPath, options) {
      var node = nodes[nodeId];
      
      if (!node) {
        console.error('Node not found: ' + nodeId);
        return false;
      }
      
      // Default loading options
      var loadOptions = {
        centerModel: true,
        scaleToFit: true
      };
      
      // Merge with provided options
      if (options) {
        for (var key in options) {
          if (options.hasOwnProperty(key)) {
            loadOptions[key] = options[key];
          }
        }
      }
      
      // Load model
      node.viewer.loadModel(modelPath, loadOptions);
      node.modelPath = modelPath;
      node.lastUpdate = Date.now();
      
      return true;
    }
    
    /**
     * Check for updates to a node
     * 
     * @param {string} nodeId - The ID of the node
     * @param {string} modelPath - Current model path
     * @returns {boolean} True if the model has been updated
     */
    function checkForUpdates(nodeId, modelPath) {
      var node = nodes[nodeId];
      
      if (!node) {
        return false;
      }
      
      // Check if model path has changed
      if (node.modelPath !== modelPath) {
        return true;
      }
      
      return false;
    }
    
    /**
     * Remove a viewer node
     * 
     * @param {string} nodeId - The ID of the node
     * @returns {boolean} Success status
     */
    function removeNode(nodeId) {
      var node = nodes[nodeId];
      
      if (!node) {
        console.error('Node not found: ' + nodeId);
        return false;
      }
      
      // Destroy viewer
      node.viewer.destroy();
      
      // Remove node reference
      delete nodes[nodeId];
      
      return true;
    }
    
    /**
     * Get a viewer node
     * 
     * @param {string} nodeId - The ID of the node
     * @returns {Object} Node object or null if not found
     */
    function getNode(nodeId) {
      return nodes[nodeId] || null;
    }
    
    /**
     * Get all viewer nodes
     * 
     * @returns {Object} Object with node IDs as keys and node objects as values
     */
    function getAllNodes() {
      return Object.assign({}, nodes);
    }
    
    /**
     * Merge options objects
     * 
     * @param {Object} target - Target object
     * @param {Object} source - Source object
     * @returns {Object} Merged object
     * @private
     */
    function mergeOptions(target, source) {
      var result = Object.assign({}, target);
      
      // Merge first level properties
      for (var key in source) {
        if (source.hasOwnProperty(key)) {
          if (typeof source[key] === 'object' && source[key] !== null && 
              typeof target[key] === 'object' && target[key] !== null) {
            // Recursive merge for objects
            result[key] = mergeOptions(target[key], source[key]);
          } else {
            // Direct assignment for primitives
            result[key] = source[key];
          }
        }
      }
      
      return result;
    }
    
    // Public API
    return {
      initializeViewer: initializeViewer,
      loadModel: loadModel,
      checkForUpdates: checkForUpdates,
      removeNode: removeNode,
      getNode: getNode,
      getAllNodes: getAllNodes
    };
  })();