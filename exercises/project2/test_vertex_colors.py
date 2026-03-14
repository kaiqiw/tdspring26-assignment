#!/usr/bin/env python3
"""Quick test to verify PLY vertex colors are imported correctly."""

from pathlib import Path
import sys

# Add project2 to path
sys.path.insert(0, str(Path(__file__).parent / "project2"))

import bpy
import project2_ex2_fbx_tiktok as project_module

# Test paths
PROJECT_ROOT = Path(__file__).parent / "project2"
PC_FILE = PROJECT_ROOT / "pointcloud_character_assets" / "pointclouds" / "David_Bust_point_cloud.ply"

def test_vertex_colors():
    """Test importing PLY with vertex colors."""
    print(f"\n{'='*70}")
    print(f"TEST: PLY Vertex Color Import")
    print(f"{'='*70}\n")
    
    # Reset scene
    print("[1/3] Resetting scene...")
    project_module.reset_scene()
    project_module.ensure_object_mode()
    print("✓ Scene reset\n")
    
    # Import pointcloud
    print(f"[2/3] Importing pointcloud: {PC_FILE.name}")
    if not PC_FILE.exists():
        print(f"✗ File not found: {PC_FILE}")
        return False
    
    pointcloud = project_module.import_pointcloud(PC_FILE, rotation=(1.5708, 0, 0))
    print(f"✓ Pointcloud imported\n")
    
    # Check for vertex colors
    print(f"[3/3] Checking vertex color attribute...")
    mesh = pointcloud.data
    
    # Check attributes
    if "Color" in mesh.attributes:
        color_attr = mesh.attributes["Color"]
        print(f"✓ Found 'Color' attribute (domain: {color_attr.domain})")
        
        # Sample first few colors
        print(f"\n  Sample vertex colors:")
        for i in range(min(5, len(mesh.vertices))):
            color_data = color_attr.data[i].vector
            print(f"    Vertex {i}: RGB({color_data.x:.2f}, {color_data.y:.2f}, {color_data.z:.2f})")
        
        print(f"\n✓ Vertex colors successfully imported!")
        return True
    else:
        print(f"✗ No 'Color' attribute found")
        print(f"  Available attributes: {[a.name for a in mesh.attributes]}")
        return False

if __name__ == "__main__":
    try:
        success = test_vertex_colors()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)