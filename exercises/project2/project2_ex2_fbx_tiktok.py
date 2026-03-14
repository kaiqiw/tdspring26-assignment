"""Week 2 Exercise 2: Pointcloud + Character Animation with RadianceField

This script uses typer to create a CLI tool that:
1. Loads RadianceField geometry node group from radiancefield.blend
2. Imports pointcloud file(s) (.ply format)
3. Applies RadianceField geometry nodes to pointclouds
4. Imports animated FBX character(s)
5. Creates TikTok-style camera following the character
6. Renders to MP4 or PNG with combined pointcloud+character names
"""

from pathlib import Path
from typing import Optional
import json

import bpy
import typer
from mathutils import Vector, Euler

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False

app = typer.Typer(help="Import pointcloud + character FBX with RadianceField geometry nodes")

# Constants
SAVE_NAME = "week2ex2_pointcloud_character.blend"
FRAME_STEP = 5  # Bake keyframes every N frames
CAMERA_DISTANCE = 2.5
CAMERA_HEIGHT_OFFSET = 1.5
TARGET_BONE_NAME = "mixamorig:Hips"

# Pointcloud position configuration
POINTCLOUD_CONFIG = {
    "David_Bust": {
        "location": (0, 1.5, 2),
        "rotation": (90, 0, 0),
    },
    "Hydrant_vertical": {
        "location": (0, 1, 1.5),
        "rotation": (90, 0, 0),
    },
    "Mailbox": {
        "location": (0, 1, 1.9),
        "rotation": (90, 0, 0),
    },
    "Panzernashorn_Tobler": {
        "location": (0, 1, 0.6),
        "rotation": (90, 0, 0),
    },
}

# Camera configuration based on character
CAMERA_CONFIG = {
    "doozy-hiphop": {
        "distance": 1.5,
        "height_offset": 3,
    },
    "mouse-hiphop": {
        "distance": 2,
        "height_offset": 2,
    },
    "michelle-hiphop": {
        "distance": 2.5,
        "height_offset": 1.5,
    },
    "vegas-hiphop": {
        "distance": 1.5,
        "height_offset": 2,
    },
}

# Default paths
PROJECT_ROOT = Path(__file__).parent
RADIANCEFIELD_BLEND = PROJECT_ROOT / "radiancefield.blend"
POINTCLOUDS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "pointclouds"
CHARACTERS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "characters"


def reset_scene() -> None:
    """Reset to a clean scene with proper settings."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    
    # TikTok aspect ratio: 9:16 (vertical video)
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1920
    bpy.context.scene.render.resolution_percentage = 100


def ensure_object_mode() -> None:
    """Ensure we're in object mode."""
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def load_radiance_field_nodegroup() -> Optional[bpy.types.NodeTree]:
    """Load RadianceField node group from radiancefield.blend.
    
    Returns:
        The RadianceField node tree, or None if not found.
    """
    if not RADIANCEFIELD_BLEND.exists():
        typer.secho(
            f"Error: radiancefield.blend not found at {RADIANCEFIELD_BLEND}",
            fg=typer.colors.RED
        )
        return None
    
    typer.echo(f"Loading RadianceField node group from {RADIANCEFIELD_BLEND.name}...")
    
    # Link the node group from external blend file
    with bpy.data.libraries.load(str(RADIANCEFIELD_BLEND), link=False) as (data_from, data_to):
        # Load all node groups
        data_to.node_groups = data_from.node_groups
    
    # Find RadianceField node group
    if "RadianceField" in bpy.data.node_groups:
        nodegroup = bpy.data.node_groups["RadianceField"]
        typer.secho(f"✓ Loaded RadianceField node group", fg=typer.colors.GREEN)
        return nodegroup
    else:
        typer.secho("⚠ RadianceField node group not found in radiancefield.blend", fg=typer.colors.YELLOW)
        typer.echo(f"Available node groups: {list(bpy.data.node_groups.keys())}")
        return None


def import_pointcloud(
    pc_path: Path, rotation: tuple[float, float, float] = (0, 0, 0)
) -> Optional[bpy.types.Object]:
    """Import a pointcloud PLY file and preserve vertex colors like Blender's native importer."""
    
    typer.echo(f"Importing pointcloud: {pc_path}")
    
    if not pc_path.exists():
        typer.secho(f"Error: Pointcloud file not found: {pc_path}", fg=typer.colors.RED)
        return None

    try:
        import struct
        
        # Read PLY file manually to extract vertex colors
        vertices = []
        colors = []
        
        with open(pc_path, 'rb') as f:
            # Read header
            header_lines = []
            while True:
                line = f.readline().decode('ascii').strip()
                header_lines.append(line)
                if line == 'end_header':
                    break
            
            # Parse header to find vertex count and vertex format
            num_vertices = 0
            vertex_size = 0
            prop_format = {}  # {property_name: (format_char, size)}
            
            for line in header_lines:
                if line.startswith('element vertex'):
                    num_vertices = int(line.split()[-1])
                elif line.startswith('property'):
                    parts = line.split()
                    if len(parts) >= 3:
                        prop_type = parts[1]
                        prop_name = ' '.join(parts[2:])  # Handle properties with spaces
                        
                        # Map PLY types to struct format
                        if prop_type == 'double':
                            prop_format[prop_name] = ('d', 8)
                            vertex_size += 8
                        elif prop_type == 'float':
                            prop_format[prop_name] = ('f', 4)
                            vertex_size += 4
                        elif prop_type == 'uchar':
                            prop_format[prop_name] = ('B', 1)
                            vertex_size += 1
                        elif prop_type == 'uint':
                            prop_format[prop_name] = ('I', 4)
                            vertex_size += 4
                        elif prop_type == 'int':
                            prop_format[prop_name] = ('i', 4)
                            vertex_size += 4
            
            typer.secho(f"PLY format: {num_vertices} vertices, {vertex_size} bytes each", fg=typer.colors.CYAN)
            
            # Read vertices with correct byte layout
            for _ in range(num_vertices):
                data = f.read(vertex_size)
                if len(data) < vertex_size:
                    break
                
                offset = 0
                vertex = []
                rgb = [1.0, 1.0, 1.0]
                
                # Extract properties in order
                for prop_name, (fmt, size) in prop_format.items():
                    value = struct.unpack_from(f'<{fmt}', data, offset)[0]
                    
                    if prop_name == 'x':
                        vertex.append(value)
                    elif prop_name == 'y':
                        vertex.append(value)
                    elif prop_name == 'z':
                        vertex.append(value)
                    elif prop_name in ['red', 'diffuse_red']:
                        rgb[0] = value / 255.0 if fmt == 'B' else value
                    elif prop_name in ['green', 'diffuse_green']:
                        rgb[1] = value / 255.0 if fmt == 'B' else value
                    elif prop_name in ['blue', 'diffuse_blue']:
                        rgb[2] = value / 255.0 if fmt == 'B' else value
                    
                    offset += size
                
                if len(vertex) == 3:
                    vertices.append(tuple(vertex))
                    colors.append(tuple(rgb) + (1.0,))  # Add alpha
        
        typer.secho(f"✓ Loaded {len(vertices)} vertices from PLY", fg=typer.colors.GREEN)
        
        if len(colors) == len(vertices) and any(c[:3] != (1.0, 1.0, 1.0) for c in colors):
            typer.secho(f"✓ Vertex colors found ({len(colors)} colors)", fg=typer.colors.GREEN)
        
        # Create Blender mesh
        bpy_mesh = bpy.data.meshes.new(name="PointcloudMesh")
        bpy_mesh.from_pydata(vertices=vertices, edges=[], faces=[])
        
        # Add colors as 'Col' attribute (matching Blender's native import naming)
        if colors:
            color_attr = bpy_mesh.attributes.new(
                name="Col",  # Use 'Col' like Blender's native importer
                type='FLOAT_COLOR',
                domain='POINT'
            )
            for i, color in enumerate(colors):
                color_attr.data[i].color = color
        
        bpy_mesh.update()
        
        # Create object
        obj = bpy.data.objects.new("Pointcloud", bpy_mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        # Create material with vertex color support
        mat = bpy.data.materials.new(name="PointcloudMaterial")
        mat.use_nodes = True
        
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        
        # Create Attribute node for vertex colors
        attr_node = mat.node_tree.nodes.new(type='ShaderNodeAttribute')
        attr_node.attribute_name = 'Col'
        
        mat.node_tree.links.new(attr_node.outputs['Color'], bsdf.inputs['Base Color'])
        obj.data.materials.append(mat)
        
        typer.secho(f"✓ Material created with vertex color support", fg=typer.colors.GREEN)
        
        # Apply rotation
        if rotation != (0, 0, 0):
            from mathutils import Euler
            obj.rotation_euler = Euler((
                rotation[0] * 3.14159 / 180,
                rotation[1] * 3.14159 / 180,
                rotation[2] * 3.14159 / 180,
            ), 'XYZ')
            typer.secho(
                f"✓ Rotation applied: {rotation}",
                fg=typer.colors.GREEN,
            )
        
        return obj
        
    except Exception as e:
        typer.secho(f"Error: Failed to import pointcloud: {e}", fg=typer.colors.RED)
        import traceback
        traceback.print_exc()
        return None


def apply_radiance_field_modifier(
    pointcloud: bpy.types.Object,
    nodegroup: bpy.types.NodeTree,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> Optional[bpy.types.Modifier]:
    """Apply RadianceField geometry node modifier to pointcloud.
    
    Args:
        pointcloud: The pointcloud mesh object
        nodegroup: The RadianceField node tree
        rotation: XYZ rotation in degrees
        
    Returns:
        The geometry nodes modifier, or None if failed.
    """
    ensure_object_mode()
    
    # Apply rotation
    if any(rotation):
        typer.echo(f"Applying rotation: {rotation}")
        pointcloud.rotation_euler = Euler((
            rotation[0] * 3.14159 / 180,
            rotation[1] * 3.14159 / 180,
            rotation[2] * 3.14159 / 180,
        ), 'XYZ')
        bpy.context.view_layer.update()
    
    # Add geometry nodes modifier (use "NODES" instead of "GEOMETRY_NODES")
    modifier = pointcloud.modifiers.new(name="GeometryNodes", type="NODES")
    modifier.node_group = nodegroup
    
    typer.secho(f"✓ Applied RadianceField modifier to {pointcloud.name}", fg=typer.colors.GREEN)
    return modifier


def set_pointcloud_bounding_box(
    pointcloud: bpy.types.Object,
    bbox_min: tuple[float, float, float] = (-1, -1, -1),
    bbox_max: tuple[float, float, float] = (1, 1, 1),
) -> None:
    """Set bounding box for the pointcloud via geometry node modifier.
    
    Args:
        pointcloud: The pointcloud mesh object with GeometryNodes modifier
        bbox_min: Minimum corner of bounding box (x, y, z)
        bbox_max: Maximum corner of bounding box (x, y, z)
    """
    if "GeometryNodes" not in pointcloud.modifiers:
        typer.secho(
            f"Error: {pointcloud.name} has no GeometryNodes modifier",
            fg=typer.colors.RED
        )
        return
    
    modifier = pointcloud.modifiers["GeometryNodes"]
    
    try:
        # Socket_3 appears to be the bounding box input
        # These are typically 3-component vectors
        modifier["Socket_3"] = (bbox_min[0], bbox_min[1], bbox_min[2])
        # If there's a separate max, it might be Socket_4
        # For now, just set the min box
        typer.echo(f"Set bounding box to: min={bbox_min}, max={bbox_max}")
        typer.secho(f"✓ Bounding box configured", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"⚠ Could not set bounding box: {e}", fg=typer.colors.YELLOW)


def import_fbx(fbx_path: Path) -> list[bpy.types.Object]:
    """Import FBX file and return imported objects."""
    if not fbx_path.exists():
        typer.secho(f"Error: FBX file not found: {fbx_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    typer.echo(f"Importing FBX: {fbx_path.name}")
    
    # Get objects before import
    objects_before = set(bpy.data.objects)
    
    # Import FBX
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    
    # Get newly imported objects
    objects_after = set(bpy.data.objects)
    imported_objects = list(objects_after - objects_before)
    
    typer.secho(f"✓ Imported {len(imported_objects)} objects from FBX", fg=typer.colors.GREEN)
    return imported_objects


def find_armature(
    imported_objects: list[bpy.types.Object],
) -> Optional[bpy.types.Object]:
    """Find the armature object from imported objects."""
    for obj in imported_objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def get_target_world_location(
    armature: bpy.types.Object, bone_name: str
) -> tuple[float, float, float]:
    """Get world location of a bone in the armature."""
    if bone_name in armature.pose.bones:
        bone = armature.pose.bones[bone_name]
        matrix = armature.matrix_world @ bone.matrix
        return tuple(matrix.translation)
    
    # Fallback to armature origin
    return tuple(armature.matrix_world.translation)


def position_character(
    character_armature: bpy.types.Object,
    location: tuple[float, float, float],
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> None:
    """Position and rotate a character in the scene.
    
    Args:
        character_armature: The imported armature object
        location: XYZ position
        rotation: XYZ rotation in degrees
    """
    ensure_object_mode()
    
    character_armature.location = location
    
    if any(rotation):
        character_armature.rotation_euler = Euler((
            rotation[0] * 3.14159 / 180,
            rotation[1] * 3.14159 / 180,
            rotation[2] * 3.14159 / 180,
        ), 'XYZ')
    
    typer.echo(f"Positioned {character_armature.name} at {location} with rotation {rotation}")


def create_tiktok_camera(name: str = "TikTokCamera") -> bpy.types.Object:
    """Create a camera optimized for TikTok-style vertical video."""
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    camera.name = name
    camera.data.name = f"{name}_data"
    
    # Camera settings for portrait video
    camera.data.lens = 50
    camera.data.sensor_width = 36
    camera.data.sensor_height = 36 * (16 / 9)
    
    # Set as active camera
    bpy.context.scene.camera = camera
    
    return camera


def setup_camera_tracking(
    camera: bpy.types.Object,
    target: bpy.types.Object,
    bone_name: Optional[str] = None,
    frame_start: int = 1,
    frame_end: int = 250,
    camera_distance: float = 2.5,
    camera_height_offset: float = 1.5,
) -> None:
    """Setup camera to follow the target with baked keyframes.
    
    Args:
        camera: Camera object
        target: Target object (usually armature)
        bone_name: Bone name to track (if target is armature)
        frame_start: Start frame
        frame_end: End frame
        camera_distance: Distance from target (Y axis)
        camera_height_offset: Height above target (Z axis)
    """
    typer.echo(f"Setting up camera tracking from frame {frame_start} to {frame_end}")
    typer.echo(f"Camera distance: {camera_distance}, height offset: {camera_height_offset}")
    
    # Clear existing animation data
    if camera.animation_data:
        camera.animation_data_clear()
    
    scene = bpy.context.scene
    
    # Bake keyframes
    for frame in range(frame_start, frame_end + 1, FRAME_STEP):
        scene.frame_set(frame)
        
        # Get target location
        if target.type == "ARMATURE" and bone_name:
            target_loc = get_target_world_location(target, bone_name)
        else:
            target_loc = tuple(target.matrix_world.translation)
        
        # Position camera behind and above target
        camera.location = (
            target_loc[0],
            target_loc[1] - camera_distance,
            target_loc[2] + camera_height_offset,
        )
        
        # Point camera at target
        direction = Vector(
            (
                target_loc[0] - camera.location[0],
                target_loc[1] - camera.location[1],
                target_loc[2] - camera.location[2],
            )
        )
        
        # Calculate rotation to look at target
        track_quat = direction.to_track_quat("-Z", "Y")
        camera.rotation_euler = track_quat.to_euler()
        
        # Insert keyframes
        camera.keyframe_insert(data_path="location", frame=frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    typer.secho(
        f"✓ Baked {(frame_end - frame_start) // FRAME_STEP + 1} keyframes",
        fg=typer.colors.GREEN,
    )


def add_studio_lighting() -> None:
    """Add basic three-point lighting setup."""
    typer.echo("Adding studio lighting")
    
    # Key light
    bpy.ops.object.light_add(type="AREA", location=(2, -2, 4))
    key_light = bpy.context.active_object
    key_light.name = "KeyLight"
    key_light.data.energy = 200
    key_light.data.size = 2
    
    # Fill light
    bpy.ops.object.light_add(type="AREA", location=(-2, -1, 2))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 100
    fill_light.data.size = 2
    
    # Rim light
    bpy.ops.object.light_add(type="SPOT", location=(0, 2, 3))
    rim_light = bpy.context.active_object
    rim_light.name = "RimLight"
    rim_light.data.energy = 150
    
    typer.secho("✓ Lighting setup complete", fg=typer.colors.GREEN)


def save_blend_file(output_path: Optional[Path] = None) -> None:
    """Save the blend file."""
    if output_path is None:
        output_path = Path.cwd() / SAVE_NAME
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    typer.secho(f"✓ Saved: {output_path}", fg=typer.colors.GREEN)


def render_to_mp4(
    output_path: Path,
    fps: int = 24,
    quality: str = "high",
    frame_start: Optional[int] = None,
    frame_end: Optional[int] = None,
) -> Path:
    """Render animation directly to MP4 file using Blender's FFmpeg."""
    scene = bpy.context.scene
    
    # Use scene frame range if not specified
    if frame_start is None:
        frame_start = scene.frame_start
    if frame_end is None:
        frame_end = scene.frame_end
    
    # Quality settings mapping
    quality_settings = {
        "high": {"bitrate": 8000, "gop": 12},
        "medium": {"bitrate": 4000, "gop": 15},
        "low": {"bitrate": 2000, "gop": 18},
    }
    
    if quality not in quality_settings:
        typer.secho(f"Warning: Unknown quality '{quality}', using 'medium'", fg=typer.colors.YELLOW)
        quality = "medium"
    
    settings = quality_settings[quality]
    
    typer.echo(f"Rendering frames {frame_start} to {frame_end}...")
    
    # Store original settings to restore later
    original_media_type = scene.render.image_settings.media_type
    original_format = scene.render.image_settings.file_format
    original_filepath = scene.render.filepath
    original_start = scene.frame_start
    original_end = scene.frame_end
    
    try:
        # Configure FFmpeg output
        scene.render.image_settings.media_type = 'VIDEO'
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        
        # Quality settings
        scene.render.ffmpeg.constant_rate_factor = 'HIGH' if quality == 'high' else 'MEDIUM' if quality == 'medium' else 'LOW'
        scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
        scene.render.ffmpeg.video_bitrate = settings["bitrate"]
        scene.render.ffmpeg.gopsize = settings["gop"]
        
        # Audio settings
        scene.render.ffmpeg.audio_codec = 'AAC'
        scene.render.ffmpeg.audio_bitrate = 192
        
        # Frame rate
        scene.render.fps = fps
        scene.render.fps_base = 1.0
        
        # Set output path and frame range
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(output_path)
        scene.frame_start = frame_start
        scene.frame_end = frame_end
        
        typer.echo(f"Output will be written to: {scene.render.filepath}")
        typer.echo(f"Encoding to MP4 with quality={quality} (bitrate={settings['bitrate']}kbps)...")
        
        # Render animation
        bpy.ops.render.render(animation=True, write_still=False)
        
        typer.secho(f"✓ MP4 rendered successfully: {output_path}", fg=typer.colors.GREEN)
        
        # Get file size
        if output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            typer.echo(f"  File size: {file_size_mb:.2f} MB")
            typer.echo(f"  Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
            typer.echo(f"  Frame rate: {fps} fps")
            typer.echo(f"  Duration: {(frame_end - frame_start + 1) / fps:.2f} seconds")
        
    except Exception as e:
        typer.secho(f"Error during rendering: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    finally:
        # Restore original settings
        scene.render.image_settings.media_type = original_media_type
        scene.render.image_settings.file_format = original_format
        scene.render.filepath = original_filepath
        scene.frame_start = original_start
        scene.frame_end = original_end
    
    return output_path


def render_to_png(
    output_path: Path,
    frame: int = 1,
) -> Path:
    """Render a single frame to PNG file."""
    scene = bpy.context.scene
    
    typer.echo(f"Rendering frame {frame} to PNG...")
    
    # Store original settings
    original_format = scene.render.image_settings.file_format
    original_filepath = scene.render.filepath
    original_frame = scene.frame_current
    
    try:
        # Configure PNG output
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.compression = 15  # 0-15, higher = more compression
        
        # Set output path and frame
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(output_path)
        scene.frame_set(frame)
        
        typer.echo(f"Output will be written to: {scene.render.filepath}")
        
        # Render single frame
        bpy.ops.render.render(write_still=True)
        
        typer.secho(f"✓ PNG rendered successfully: {output_path}", fg=typer.colors.GREEN)
        
        if output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            typer.echo(f"  File size: {file_size_mb:.2f} MB")
            typer.echo(f"  Frame: {frame}")
        
    except Exception as e:
        typer.secho(f"Error during rendering: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    finally:
        # Restore original settings
        scene.render.image_settings.file_format = original_format
        scene.render.filepath = original_filepath
        scene.frame_set(original_frame)
    
    return output_path


@app.command()
def test_pointcloud(
    pointcloud_file: Optional[Path] = typer.Argument(None, help="Path to .ply pointcloud file (or use --all for all files)"),
    all_files: bool = typer.Option(False, "--all", help="Import all pointclouds from the default folder"),
    rotation: str = typer.Option("0,0,0", "--rotation", "-r", help="Rotation in degrees (x,y,z format)"),
) -> None:
    """Test importing and processing pointcloud files.
    
    Examples:
        python project2_ex2_fbx_tiktok.py test-pointcloud David_Bust_point_cloud.ply
        python project2_ex2_fbx_tiktok.py test-pointcloud --all
    """
    typer.secho("🔍 Testing Pointcloud Import", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)
    
    # Reset scene
    typer.echo("Resetting scene...")
    reset_scene()
    ensure_object_mode()
    
    # Load RadianceField node group
    nodegroup = load_radiance_field_nodegroup()
    if not nodegroup:
        typer.secho("Warning: Could not load RadianceField node group", fg=typer.colors.YELLOW)
    
    # Parse rotation
    try:
        rot_values = tuple(float(x.strip()) for x in rotation.split(","))
        if len(rot_values) != 3:
            raise ValueError("Expected 3 values")
    except (ValueError, AttributeError):
        typer.secho(f"Error: Invalid rotation format '{rotation}'. Use 'x,y,z'", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Get pointcloud files
    files_to_import = []
    if all_files:
        if POINTCLOUDS_FOLDER.exists():
            files_to_import = sorted(POINTCLOUDS_FOLDER.glob("*.ply"))
            typer.echo(f"Found {len(files_to_import)} pointcloud files")
        else:
            typer.secho(f"Error: Pointclouds folder not found: {POINTCLOUDS_FOLDER}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    elif pointcloud_file:
        # Resolve file path
        if not pointcloud_file.is_absolute():
            pointcloud_file = POINTCLOUDS_FOLDER / pointcloud_file
        files_to_import = [pointcloud_file]
    else:
        typer.secho("Error: Provide either a pointcloud file or use --all", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Import each pointcloud
    for ply_path in files_to_import:
        typer.echo(f"\n--- Processing {ply_path.name} ---")
        
        # Import pointcloud
        pointcloud = import_pointcloud(ply_path)
        if not pointcloud:
            continue
        
        # Apply RadianceField modifier
        if nodegroup:
            apply_radiance_field_modifier(pointcloud, nodegroup, rot_values)
        
        # Report stats
        typer.echo(f"Vertices: {len(pointcloud.data.vertices)}")
        typer.echo(f"Location: {pointcloud.location}")
        typer.echo(f"Rotation: {pointcloud.rotation_euler}")
    
    typer.echo("\n" + "=" * 50)
    typer.secho("✓ Test complete", fg=typer.colors.GREEN)


@app.command()
def create(
    pointcloud_file: Optional[Path] = typer.Argument(None, help="Path to .ply pointcloud file"),
    character_file: Optional[Path] = typer.Option(None, "--character", "-c", help="Path to FBX character file"),
    pointcloud_rotation: str = typer.Option("0,0,0", "--pc-rotation", help="Pointcloud rotation in degrees (x,y,z)"),
    character_location: str = typer.Option("0,0,0", "--char-location", "-l", help="Character position (x,y,z)"),
    character_rotation: str = typer.Option("0,0,0", "--char-rotation", help="Character rotation in degrees (x,y,z)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output .blend file path"),
    no_lights: bool = typer.Option(False, "--no-lights", help="Skip adding studio lights"),
) -> None:
    """Create a scene with pointcloud + character animation.
    
    Examples:
        python project2_ex2_fbx_tiktok.py create David_Bust_point_cloud.ply --character mouse-hiphop.fbx
        python project2_ex2_fbx_tiktok.py create David_Bust_point_cloud.ply --character mouse-hiphop.fbx --char-location "0,0,0"
    """
    typer.secho("🎬 Creating Pointcloud + Character Scene", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)
    
    # Step 1: Reset scene
    typer.echo("1. Resetting scene...")
    reset_scene()
    ensure_object_mode()
    
    # Step 2: Load RadianceField node group
    typer.echo("2. Loading RadianceField geometry nodes...")
    nodegroup = load_radiance_field_nodegroup()
    if not nodegroup:
        typer.secho("Error: Could not load RadianceField node group", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Step 3: Parse parameters
    try:
        pc_rot = tuple(float(x.strip()) for x in pointcloud_rotation.split(","))
        char_loc = tuple(float(x.strip()) for x in character_location.split(","))
        char_rot = tuple(float(x.strip()) for x in character_rotation.split(","))
        if len(pc_rot) != 3 or len(char_loc) != 3 or len(char_rot) != 3:
            raise ValueError("Expected 3 values for each parameter")
    except (ValueError, AttributeError) as e:
        typer.secho(f"Error: Invalid parameter format: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Step 4: Import pointcloud
    if not pointcloud_file:
        typer.secho("Error: Pointcloud file is required", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    if not pointcloud_file.is_absolute():
        pointcloud_file = POINTCLOUDS_FOLDER / pointcloud_file
    
    typer.echo(f"3. Importing pointcloud...")
    pointcloud = import_pointcloud(pointcloud_file)
    if not pointcloud:
        raise typer.Exit(code=1)
    
    # Check if pointcloud has custom config and apply it
    pc_stem = pointcloud_file.stem.replace("_point_cloud", "")
    custom_location = (0, 0, 0)  # Default location
    
    if pc_stem in POINTCLOUD_CONFIG:
        pc_config = POINTCLOUD_CONFIG[pc_stem]
        custom_location = pc_config.get("location", (0, 0, 0))
        # Override pointcloud rotation from config if not specified in CLI
        if pointcloud_rotation == "0,0,0":
            pc_rot = pc_config.get("rotation", (0, 0, 0))
    
    # Apply pointcloud location
    pointcloud.location = custom_location
    typer.secho(f"✓ Pointcloud location: {custom_location}", fg=typer.colors.GREEN)
    
    # Apply RadianceField modifier
    typer.echo("4. Applying RadianceField geometry nodes...")
    apply_radiance_field_modifier(pointcloud, nodegroup, pc_rot)
    
    # Step 5: Import character FBX
    if character_file:
        if not character_file.is_absolute():
            character_file = CHARACTERS_FOLDER / character_file
        
        typer.echo("5. Importing character FBX...")
        imported_objects = import_fbx(character_file)
        
        # Find armature
        armature = find_armature(imported_objects)
        if not armature:
            typer.secho("Warning: No armature found in FBX", fg=typer.colors.YELLOW)
        else:
            typer.echo("6. Positioning character...")
            position_character(armature, char_loc, char_rot)
            
            # Determine end frame from animation
            end_frame = 250
            if armature.animation_data and armature.animation_data.action:
                end_frame = int(armature.animation_data.action.frame_range[1])
                typer.secho(f"✓ Using animation end frame: {end_frame}", fg=typer.colors.GREEN)
            
            # Set frame range
            bpy.context.scene.frame_start = 1
            bpy.context.scene.frame_end = end_frame
            
            # Create camera and setup tracking
            typer.echo("7. Creating TikTok camera...")
            camera = create_tiktok_camera()
            
            # Get camera config based on character filename
            char_name_stem = character_file.stem
            cam_config = CAMERA_CONFIG.get(char_name_stem, {
                "distance": CAMERA_DISTANCE,
                "height_offset": CAMERA_HEIGHT_OFFSET,
            })
            cam_dist = cam_config.get("distance", CAMERA_DISTANCE)
            cam_height = cam_config.get("height_offset", CAMERA_HEIGHT_OFFSET)
            
            typer.echo("8. Setting up camera tracking...")
            setup_camera_tracking(
                camera, armature, TARGET_BONE_NAME, 1, end_frame,
                camera_distance=cam_dist,
                camera_height_offset=cam_height
            )
    else:
        typer.echo("5. Skipping character import (no FBX file specified)")
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 250
    
    # Step 6: Add lighting
    if not no_lights:
        typer.echo("9. Adding studio lighting...")
        add_studio_lighting()
    else:
        typer.echo("9. Skipping lights (--no-lights specified)")
    
    # Step 7: Save file
    typer.echo("10. Saving blend file...")
    if not output:
        pc_name = pointcloud_file.stem
        char_name = character_file.stem if character_file else "nochar"
        output = Path.cwd() / f"{pc_name}_{char_name}.blend"
    
    save_blend_file(output)
    
    typer.echo("=" * 50)
    typer.secho("✨ Setup complete!", fg=typer.colors.GREEN, bold=True)


@app.command()
def render(
    blend_file: Path = typer.Argument(..., help="Path to the blend file to render"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path (.mp4 or .png)"),
    format: str = typer.Option("mp4", "--format", "-f", help="Output format: mp4 or png"),
    fps: int = typer.Option(24, "--fps", help="Frames per second (for mp4)"),
    quality: str = typer.Option("high", "--quality", "-q", help="Quality preset: high, medium, or low"),
    frame: int = typer.Option(1, "--frame", help="Frame number to render (for png)"),
    frame_start: Optional[int] = typer.Option(None, "--start", "-s", help="Start frame (for mp4)"),
    frame_end: Optional[int] = typer.Option(None, "--end", "-e", help="End frame (for mp4)"),
) -> None:
    """Render a blend file animation to MP4 or a single frame to PNG.
    
    Examples:
        python project2_ex2_fbx_tiktok.py render scene.blend
        python project2_ex2_fbx_tiktok.py render scene.blend -f png --frame 50
        python project2_ex2_fbx_tiktok.py render scene.blend -q medium --fps 30
    """
    typer.secho("🎬 Rendering Animation", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)
    
    if not blend_file.exists():
        typer.secho(f"Error: Blend file not found: {blend_file}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Load the blend file
    typer.echo(f"Loading blend file: {blend_file}")
    bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    ensure_object_mode()
    
    # Verify we have a camera
    if bpy.context.scene.camera is None:
        typer.secho("Error: Scene has no active camera!", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Default output path
    if output is None:
        output = blend_file.with_suffix(f".{format}")
    
    # Render based on format
    if format.lower() == "png":
        typer.echo(f"\nRendering frame {frame} to PNG: {output}")
        render_to_png(output, frame)
    elif format.lower() == "mp4":
        typer.echo(f"\nRendering to MP4: {output}")
        render_to_mp4(
            output_path=output,
            fps=fps,
            quality=quality,
            frame_start=frame_start,
            frame_end=frame_end,
        )
    else:
        typer.secho(f"Error: Unknown format '{format}'. Use 'mp4' or 'png'", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    typer.echo("=" * 50)
    typer.secho("✨ Render complete!", fg=typer.colors.GREEN, bold=True)


if __name__ == "__main__":
    app()
