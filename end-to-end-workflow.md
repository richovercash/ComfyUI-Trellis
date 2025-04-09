# ComfyUI to Trellis 3D: End-to-End Workflow Guide

This guide demonstrates a complete workflow from generating images in ComfyUI to creating and viewing 3D models with Trellis.

## Prerequisites

- ComfyUI installed and working
- ComfyUI-Trellis extension installed
- Trellis server running (WebSocket or REST API)

## Workflow 1: Basic Image to 3D Model

This simple workflow takes an image generated in ComfyUI and creates a 3D model using Trellis.

### Step 1: Generate an Image in ComfyUI

1. Start with a **KSampler** node connected to a model, conditioning, and latent image
2. Add a **VAEDecode** node to convert the latent to an image
3. Connect a **SaveImage** node if you want to save the output image

### Step 2: Process with Trellis

1. Add a **TrellisProcessWebSocket** node to your workflow
2. Connect the image output from the VAEDecode node to the TrellisProcessWebSocket's "image" input
3. Configure the processing parameters:
   - **server_url**: WebSocket URL of your Trellis server
   - **seed**: Random seed for generation
   - **sparse_steps**: Number of sparse steps (try 12 to start)
   - **sparse_cfg_strength**: Sparse CFG strength (try 7.5 to start)
   - **slat_steps**: SLAT steps (try 12 to start)
   - **slat_cfg_strength**: SLAT CFG strength (try 3.0 to start)
   - **simplify**: Mesh simplification factor (try 0.95 to start)
   - **texture_size**: Texture size in pixels (try 1024 to start)

### Step 3: View the Output

1. Add a **TrellisModelViewerNode** to view the 3D model
2. Connect the "glb_path" output from the TrellisProcessWebSocket to the viewer's "glb_path" input
3. Add a **TrellisVideoPlayerNode** to view the video preview
4. Connect the "video_path" output from the TrellisProcessWebSocket to the player's "video_path" input
5. Run the workflow and wait for processing to complete
6. Open the generated HTML files to view the model and video in your browser

## Workflow 2: Advanced Pipeline with Parameter Experimentation

This advanced workflow helps you experiment with different Trellis parameters and manage the results.

### Step 1: Setup Session Management

1. Add a **TrellisSessionManager** node at the beginning of your workflow
2. Set the "action" to "create" and give it a meaningful "session_name"

### Step 2: Process with Different Parameters

1. Create three **TrellisProcessWebSocket** nodes with different parameter configurations:
   - Node 1: Fast processing (lower steps, smaller texture)
   - Node 2: Balanced processing (medium steps, medium texture)
   - Node 3: Quality processing (higher steps, larger texture)
2. Connect all three to the same image output
3. Connect the session ID and task ID from the SessionManager to each process node
4. Add a **TrellisStatusNode** to monitor the processing status

### Step 3: Compare Results

1. Add a **TrellisModelViewerNode** for each output
2. Use different viewer settings for easy comparison:
   - Different background colors
   - Different camera distances
   - Different auto-rotate settings
3. Run the workflow to process with all parameter sets
4. Compare the results to find the best settings for your specific image

## Workflow 3: Batch Processing Multiple Images

This workflow processes multiple images with Trellis in a batch.

### Step 1: Load Multiple Images

1. Use a **LoadImagesFromDirectory** or similar node to load multiple images
2. Alternatively, use a ComfyUI batch generation workflow to create multiple images

### Step 2: Process with TrellisMultiImageNode

1. Add a **TrellisMultiImageNode** to your workflow
2. Connect the batch of images to the multi-image node
3. Configure the processing parameters
4. Add a **TrellisSessionManager** to keep track of the session

### Step 3: Track and Organize Results

1. Use the TrellisFileManager utility (via Python scripting) to organize the output files
2. Add TrellisModelViewerNodes to preview each output
3. Use the TrellisMetadataManager to associate metadata with each output

## Parameter Tuning Guide

Different types of images may require different Trellis parameters for optimal results.

### Object Type

| Object Type | sparse_steps | sparse_cfg_strength | slat_steps | slat_cfg_strength | simplify |
|-------------|--------------|---------------------|------------|-------------------|----------|
| Simple | 8-10 | 6-7 | 8-10 | 2-3 | 0.95-0.98 |
| Moderate | 12-14 | 7-8 | 12-14 | 3-4 | 0.93-0.95 |
| Complex | 16-20 | 8-9 | 16-20 | 4-5 | 0.9-0.93 |

### Texture Quality

| Desired Quality | texture_size | Typical Use Case |
|-----------------|--------------|------------------|
| Low (Fast) | 512 | Quick tests, draft models |
| Medium | 1024 | General purpose, good balance |
| High | 1536 | Detailed textures, close viewing |
| Ultra | 2048 | Maximum quality, presentation |

### Processing Time vs. Quality

- Lower settings (sparse_steps=8, texture_size=512): ~2-5 minutes
- Medium settings (sparse_steps=12, texture_size=1024): ~5-10 minutes
- High settings (sparse_steps=20, texture_size=2048): ~15-30 minutes

## Troubleshooting

### Connection Issues

- If you can't connect to the Trellis server:
  - Check the server URL in your node configuration
  - Verify the server is running and accessible
  - Check for any firewall or network restrictions
  - Try connecting through the REST API if WebSocket fails

### Processing Errors

- If processing fails:
  - Check the ComfyUI console for error messages
  - Verify your image is suitable for 3D processing
  - Try decreasing the texture size if you're running out of memory
  - Try increasing the simplify value if the mesh is too complex

### Viewing Issues

- If the model viewer shows errors:
  - Check that the GLB file was properly downloaded
  - Verify the file path is correct and accessible
  - Try viewing the GLB file in another viewer like [Three.js Editor](https://threejs.org/editor/)
  - Check browser console for JavaScript errors

## Best Practices

1. **Start Simple**: Begin with lower settings and gradually increase for better quality
2. **Save Sessions**: Always use TrellisSessionManager to keep track of your processing
3. **Metadata**: Use TrellisMetadataManager to save parameter details with each model
4. **File Organization**: Use TrellisFileManager to keep your files organized
5. **Pre-processing**: For best results, ensure your input images have:
   - Clean backgrounds (ideally white, gray, or transparent)
   - Good lighting from multiple angles
   - Subject centered in the frame
   - No extreme perspective distortion

## Example ComfyUI Workflow JSON

Below is a simple example workflow in JSON format that you can import into ComfyUI:

```json
{
  "last_node_id": 8,
  "last_link_id": 9,
  "nodes": [
    {
      "id": 1,
      "type": "KSampler",
      "pos": [
        200,
        200
      ],
      "size": {
        "0": 315,
        "1": 262
      },
      "flags": {},
      "order": 0,
      "inputs": [
        {
          "name": "model",
          "type": "MODEL",
          "link": 1
        },
        {
          "name": "positive",
          "type": "CONDITIONING",
          "link": 2
        },
        {
          "name": "negative",
          "type": "CONDITIONING",
          "link": 3
        },
        {
          "name": "latent_image",
          "type": "LATENT",
          "link": 4
        }
      ],
      "outputs": [
        {
          "name": "LATENT",
          "type": "LATENT",
          "links": [
            5
          ]
        }
      ],
      "properties": {
        "Node name for S&R": "KSampler"
      },
      "widgets_values": [
        789012,
        "sample_euler_ancestral",
        25,
        8,
        "enable"
      ]
    },
    {
      "id": 2,
      "type": "CheckpointLoaderSimple",
      "pos": [
        -120,
        110
      ],
      "size": {
        "0": 255,
        "1": 98
      },
      "flags": {},
      "order": 1,
      "outputs": [
        {
          "name": "MODEL",
          "type": "MODEL",
          "links": [
            1
          ]
        },
        {
          "name": "CLIP",
          "type": "CLIP",
          "links": [
            6,
            7
          ]
        },
        {
          "name": "VAE",
          "type": "VAE",
          "links": []
        }
      ],
      "properties": {
        "Node name for S&R": "CheckpointLoaderSimple"
      },
      "widgets_values": [
        "dreamshaper_8.safetensors"
      ]
    },
    {
      "id": 3,
      "type": "CLIPTextEncode",
      "pos": [
        -120,
        260
      ],
      "size": {
        "0": 256.39751999999724,
        "1": 96.11071999999984
      },
      "flags": {},
      "order": 2,
      "inputs": [
        {
          "name": "clip",
          "type": "CLIP",
          "link": 6
        }
      ],
      "outputs": [
        {
          "name": "CONDITIONING",
          "type": "CONDITIONING",
          "links": [
            2
          ]
        }
      ],
      "properties": {
        "Node name for S&R": "CLIPTextEncode"
      },
      "widgets_values": [
        "beautiful 3d object, centered, white background, photorealistic"
      ]
    },
    {
      "id": 4,
      "type": "CLIPTextEncode",
      "pos": [
        -120,
        370
      ],
      "size": {
        "0": 255.6748046875,
        "1": 117.9248046875
      },
      "flags": {},
      "order": 3,
      "inputs": [
        {
          "name": "clip",
          "type": "CLIP",
          "link": 7
        }
      ],
      "outputs": [
        {
          "name": "CONDITIONING",
          "type": "CONDITIONING",
          "links": [
            3
          ]
        }
      ],
      "properties": {
        "Node name for S&R": "CLIPTextEncode"
      },
      "widgets_values": [
        "text, watermark, ugly, distorted, blurry"
      ]
    },
    {
      "id": 5,
      "type": "EmptyLatentImage",
      "pos": [
        -120,
        520
      ],
      "size": {
        "0": 255.29867999999995,
        "1": 106.46643999999998
      },
      "flags": {},
      "order": 4,
      "inputs": [],
      "outputs": [
        {
          "name": "LATENT",
          "type": "LATENT",
          "links": [
            4
          ]
        }
      ],
      "properties": {
        "Node name for S&R": "EmptyLatentImage"
      },
      "widgets_values": [
        512,
        512,
        1
      ]
    },
    {
      "id": 6,
      "type": "VAEDecode",
      "pos": [
        570,
        200
      ],
      "size": {
        "0": 210,
        "1": 46
      },
      "flags": {},
      "order": 5,
      "inputs": [
        {
          "name": "samples",
          "type": "LATENT",
          "link": 5
        },
        {
          "name": "vae",
          "type": "VAE",
          "link": null
        }
      ],
      "outputs": [
        {
          "name": "IMAGE",
          "type": "IMAGE",
          "links": [
            8,
            9
          ]
        }
      ],
      "properties": {
        "Node name for S&R": "VAEDecode"
      }
    },
    {
      "id": 7,
      "type": "TrellisProcessWebSocket",
      "pos": [
        810,
        200
      ],
      "size": {
        "0": 400,
        "1": 400
      },
      "flags": {},
      "order": 6,
      "inputs": [
        {
          "name": "image",
          "type": "IMAGE",
          "link": 8
        }
      ],
      "outputs": [
        {
          "name": "glb_path",
          "type": "STRING",
          "links": [
            10
          ]
        },
        {
          "name": "video_path",
          "type": "STRING",
          "links": [
            11
          ]
        }
      ],
      "properties": {},
      "widgets_values": [
        "ws://18.199.134.45:46173",
        1,
        12,
        7.5,
        12,
        3.0,
        0.95,
        1024
      ]
    },
    {
      "id": 8,
      "type": "SaveImage",
      "pos": [
        570,
        300
      ],
      "size": {
        "0": 210,
        "1": 270
      },
      "flags": {},
      "order": 7,
      "inputs": [
        {
          "name": "images",
          "type": "IMAGE",
          "link": 9
        }
      ],
      "properties": {},
      "widgets_values": [
        "ComfyUI",
        "png"
      ]
    },
    {
      "id": 9,
      "type": "TrellisModelViewerNode",
      "pos": [
        1250,
        150
      ],
      "size": {
        "0": 315,
        "1": 170
      },
      "flags": {},
      "order": 8,
      "inputs": [
        {
          "name": "glb_path",
          "type": "STRING",
          "link": 10
        }
      ],
      "outputs": [
        {
          "name": "viewer_html",
          "type": "HTML",
          "links": []
        },
        {
          "name": "viewer_path",
          "type": "STRING",
          "links": []
        }
      ],
      "properties": {},
      "widgets_values": [
        "",
        "#222222",
        800,
        600,
        "enabled",
        2.0
      ]
    },
    {
      "id": 10,
      "type": "TrellisVideoPlayerNode",
      "pos": [
        1250,
        350
      ],
      "size": {
        "0": 315,
        "1": 146
      },
      "flags": {},
      "order": 9,
      "inputs": [
        {
          "name": "video_path",
          "type": "STRING",
          "link": 11
        }
      ],
      "outputs": [
        {
          "name": "player_html",
          "type": "HTML",
          "links": []
        },
        {
          "name": "player_path",
          "type": "STRING",
          "links": []
        }
      ],
      "properties": {},
      "widgets_values": [
        "",
        800,
        "enabled",
        "enabled",
        "enabled"
      ]
    }
  ],
  "links": [
    {
      "id": 1,
      "from_node": 2,
      "from_output": 0,
      "to_node": 1,
      "to_input": 0
    },
    {
      "id": 2,
      "from_node": 3,
      "from_output": 0,
      "to_node": 1,
      "to_input": 1
    },
    {
      "id": 3,
      "from_node": 4,
      "from_output": 0,
      "to_node": 1,
      "to_input": 2
    },
    {
      "id": 4,
      "from_node": 5,
      "from_output": 0,
      "to_node": 1,
      "to_input": 3
    },
    {
      "id": 5,
      "from_node": 1,
      "from_output": 0,
      "to_node": 6,
      "to_input": 0
    },
    {
      "id": 6,
      "from_node": 2,
      "from_output": 1,
      "to_node": 3,
      "to_input": 0
    },
    {
      "id": 7,
      "from_node": 2,
      "from_output": 1,
      "to_node": 4,
      "to_input": 0
    },
    {
      "id": 8,
      "from_node": 6,
      "from_output": 0,
      "to_node": 7,
      "to_input": 0
    },
    {
      "id": 9,
      "from_node": 6,
      "from_output": 0,
      "to_node": 8,
      "to_input": 0
    },
    {
      "id": 10,
      "from_node": 7,
      "from_output": 0,
      "to_node": 9,
      "to_input": 0
    },
    {
      "id": 11,
      "from_node": 7,
      "from_output": 1,
      "to_node": 10,
      "to_input": 0
    }
  ]
}
```

## Advanced Optimization Techniques

### Input Image Optimization

For best results with Trellis 3D model generation, prepare your input images with these tips:

1. **Background**: Use a solid white, gray, or transparent background to help the model separate the foreground object
2. **Lighting**: Even, diffused lighting from multiple angles reduces harsh shadows
3. **Object Placement**: Center the subject with some margin around all edges
4. **Perspective**: Use a neutral perspective, avoiding extreme angles
5. **Detail**: Ensure important details are clearly visible and not obscured

### Processing Parameter Optimization

Fine-tune your Trellis parameters based on the specific type of object:

1. **Organic Objects** (people, animals, plants):
   - Higher `sparse_steps` (16-20)
   - Higher `slat_steps` (14-16)
   - Lower `simplify` (0.90-0.93)

2. **Hard-Surface Objects** (machinery, buildings, furniture):
   - Moderate `sparse_steps` (12-14)
   - Higher `sparse_cfg_strength` (8-9)
   - Higher `simplify` (0.94-0.97)

3. **Simple Shapes** (geometric forms, basic objects):
   - Lower `sparse_steps` (8-10)
   - Lower `slat_steps` (8-10)
   - Higher `simplify` (0.96-0.98)

### Performance Optimization

When processing large batches or working with limited resources:

1. **Memory Management**:
   - Lower `texture_size` for initial tests (512 or 1024)
   - Process images sequentially rather than in parallel

2. **Speed Optimization**:
   - Use the "fast" preset for initial tests
   - Cache and reuse results with the SessionManager

3. **Quality vs. Speed**:
   - For quick drafts: sparse_steps=8, texture_size=512
   - For final output: sparse_steps=16-20, texture_size=2048

## Integration with Other ComfyUI Extensions

ComfyUI-Trellis can be used alongside other extensions for a more powerful workflow:

### ComfyUI-Impact Pack

Use Impact Pack's image processing nodes to prepare images before sending to Trellis:
- Detailers for enhancing specific areas
- Inpainting to clean up backgrounds
- Mask processing to isolate objects

### ComfyUI-AnimateDiff

Generate animated sequences and process key frames with Trellis to create animated 3D models or scenes.

### ComfyUI-Manager

Install and manage the Trellis extension and its dependencies through the ComfyUI-Manager interface.

## API Integration

The ComfyUI-Trellis nodes can be integrated into larger applications using ComfyUI's API:

1. Set up a workflow with Trellis nodes
2. Use the ComfyUI API to trigger the workflow programmatically
3. Retrieve the output file paths via the API
4. Incorporate the 3D models into your application

## Conclusion

The ComfyUI-Trellis integration provides a powerful pipeline for converting AI-generated images into 3D models. By following this guide and experimenting with different parameters, you can achieve impressive results for a variety of use cases.

Remember to organize your files, save your sessions, and document your parameter choices for the best long-term workflow.
