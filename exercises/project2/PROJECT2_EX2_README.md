# Project 2 Exercise 2: Pointcloud + Character Animation with RadianceField

## Overview

This script (`project2_ex2_fbx_tiktok.py`) creates complex scenes combining:
- **Pointcloud Data** (.ply format) from the `pointcloud_character_assets/` folder
- **Animated Characters** (FBX files) with Mixamo rigging
- **RadianceField Geometry Nodes** from `radiancefield.blend`
- **TikTok-style Camera** (9:16 vertical) that tracks character animation
- **Multi-format Rendering** (MP4 or single-frame PNG)

## Features

### 1. Pointcloud Import
- Import single `.ply` files or batch import all files from the folder
- Automatic rotation support via CLI
- Integration with RadianceField geometry nodes
- Object naming (`Pointcloud` convention)

### 2. RadianceField Geometry Nodes
- Automatically loads node group from `radiancefield.blend`
- Applies modifier to pointcloud mesh
- Supports bounding box configuration (Socket_3)

### 3. Character Animation
- Import FBX files with skeletal animation
- Auto-detect Mixamo armature (bone: `mixamorig:Hips`)
- Position and rotate characters via CLI parameters
- TikTok-style camera automatically tracks character movement

### 4. Rendering
- **PNG**: Single frame export for testing
- **MP4**: Full animation export with quality presets (high/medium/low)
- 9:16 vertical resolution (1080x1920) for TikTok format
- Automatic filename generation combining pointcloud + character names

## Installation

The dependencies are in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key packages:
- `typer` - CLI framework
- `trimesh` - PLY pointcloud import/handling
- `bpy` - Blender Python API (already in `.venv/`)

## Usage

### Commands

#### 1. Test Pointcloud Import

Import and verify a single pointcloud file:

```bash
python project2_ex2_fbx_tiktok.py test-pointcloud David_Bust_point_cloud.ply
```

Import all pointclouds in the folder:

```bash
python project2_ex2_fbx_tiktok.py test-pointcloud --all
```

With rotation (degrees, x,y,z format):

```bash
python project2_ex2_fbx_tiktok.py test-pointcloud David_Bust_point_cloud.ply --rotation "0,90,0"
```

#### 2. Create Complete Scene

Create a scene with pointcloud + character animation:

```bash
python project2_ex2_fbx_tiktok.py create David_Bust_point_cloud.ply \
  --character mouse-hiphop.fbx \
  --output my_scene.blend
```

With custom positioning:

```bash
python project2_ex2_fbx_tiktok.py create David_Bust_point_cloud.ply \
  --character michelle-hiphop.fbx \
  --char-location "0.5,0,0" \
  --char-rotation "0,45,0" \
  --output scene_custom.blend
```

Skip lighting:

```bash
python project2_ex2_fbx_tiktok.py create Mailbox_point_cloud.ply \
  --character mouse-hiphop.fbx \
  --no-lights \
  --output minimal_scene.blend
```

#### 3. Render Scene

**Render to MP4 (full animation):**

```bash
python project2_ex2_fbx_tiktok.py render scene.blend -o output.mp4
```

With quality and FPS options:

```bash
python project2_ex2_fbx_tiktok.py render scene.blend \
  --format mp4 \
  --quality medium \
  --fps 30 \
  --output output_30fps.mp4
```

**Render single frame to PNG:**

```bash
python project2_ex2_fbx_tiktok.py render scene.blend --format png --frame 50 -o frame_50.png
```

**Render frame range to MP4:**

```bash
python project2_ex2_fbx_tiktok.py render scene.blend \
  --format mp4 \
  --start 1 \
  --end 100 \
  --output partial_animation.mp4
```

### Available Pointcloud Files

Located in `pointcloud_character_assets/pointclouds/`:
- `David_Bust_point_cloud.ply` (2.1M vertices, ~55 MB)
- `Hydrant_vertical_point_cloud.ply` (1.5M vertices, ~40 MB)
- `Mailbox_point_cloud.ply` (1.9M vertices, ~49 MB)
- `McLaren_point_cloud.ply` (~56 MB)
- `Panzernashorn_Tobler_point_cloud.ply` (~53 MB)

### Available Character FBX Files

Located in `pointcloud_character_assets/characters/`:
- `mouse-hiphop.fbx`
- `michelle-hiphop.fbx`
- `doozy-hiphop.fbx`
- `vegas-hiphop.fbx`

## Workflow Example

1. **Explore a pointcloud:**
   ```bash
   python project2_ex2_fbx_tiktok.py test-pointcloud Mailbox_point_cloud.ply
   ```

2. **Create a scene with a character:**
   ```bash
   python project2_ex2_fbx_tiktok.py create Mailbox_point_cloud.ply \
     --character michelle-hiphop.fbx \
     --output mailbox_michelle.blend
   ```

3. **Render a test frame:**
   ```bash
   python project2_ex2_fbx_tiktok.py render mailbox_michelle.blend \
     --format png --frame 1 --output test.png
   ```

4. **Render full animation:**
   ```bash
   python project2_ex2_fbx_tiktok.py render mailbox_michelle.blend \
     --format mp4 --quality high --output mailbox_michelle.mp4
   ```

## Output Files

All commands generate files in the current working directory:

- `.blend` - Blender project file (readable in Blender GUI)
- `.mp4` - H.264 encoded video (MP4 container)
- `.png` - Single frame image (32-bit RGBA)

Output filenames combine:
- Pointcloud name (e.g., `David_Bust_point_cloud`)
- Character name (e.g., `mouse_hiphop`)
- Format extension (`.blend`, `.mp4`, or `.png`)

Example: `David_Bust_point_cloud_mouse_hiphop.blend`

## Parameters Reference

### Common Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--rotation` / `-r` | string | `0,0,0` | Rotation in degrees (x,y,z format) |
| `--output` / `-o` | path | Auto-generated | Output file path |
| `--no-lights` | flag | False | Skip studio lighting setup |

### Character Positioning

| Parameter | Type | Default | Description |
| `--char-location` / `-l` | string | `0,0,0` | Character position (x,y,z) |
| `--char-rotation` | string | `0,0,0` | Character rotation in degrees (x,y,z) |
| `--pc-rotation` | string | `0,0,0` | Pointcloud rotation in degrees (x,y,z) |

### Rendering

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--format` / `-f` | choice | `mp4` | Output format: `mp4` or `png` |
| `--quality` / `-q` | choice | `high` | Quality: `high`, `medium`, `low` |
| `--fps` | int | 24 | Frames per second (MP4 only) |
| `--frame` | int | 1 | Frame number to render (PNG only) |
| `--start` / `-s` | int | Scene start | Start frame (MP4 only) |
| `--end` / `-e` | int | Scene end | End frame (MP4 only) |

## Technical Details

### RadianceField Node Group

The `radiancefield.blend` file contains a Geometry Nodes group that:
- Visualizes pointcloud data with customizable rendering
- Supports bounding box filtering (Socket_3)
- Can be configured with custom parameters per pointcloud

### Camera Setup

The TikTok camera:
- Aspect ratio: 9:16 (vertical video for social media)
- Resolution: 1080×1920 pixels
- Tracking: Follows `mixamorig:Hips` bone of animated character
- Keyframes: Baked every 5 frames for smooth motion

### Supported Formats

- **Import**: `.ply` (pointcloud), `.fbx` (animated character)
- **Export**: `.blend` (Blender project), `.mp4` (H.264 video), `.png` (image)

## Troubleshooting

### "RadianceField node group not found"

The `radiancefield.blend` file may not be in the correct location. Verify:
- File exists at: `exercises/project2/radiancefield.blend`
- It contains a node group named `"RadianceField"`

### "PLY importer not available"

`trimesh` library is required. Install it:
```bash
pip install trimesh
```

### Rendering is slow

Use lower quality settings for faster preview renders:
```bash
python project2_ex2_fbx_tiktok.py render scene.blend --quality low
```

### "No armature found" warning

The FBX file might not be a rigged character. Use one of the provided FBX files from `pointcloud_character_assets/characters/`.

## Notes

- All paths are relative to `exercises/project2/`
- Pointcloud files are large (~50 MB each); first import may take time
- MP4 rendering is CPU-intensive; quality affects processing time
- Blender GUI is not opened; all operations are command-line based
