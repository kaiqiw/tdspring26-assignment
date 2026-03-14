#!/usr/bin/env python3
"""Batch render all pointcloud + character combinations.

This script generates all 20 combinations of:
- 5 pointclouds (David_Bust, Hydrant_vertical, Mailbox, McLaren, Panzernashorn_Tobler)
- 4 characters (doozy, michelle, mouse, vegas)

And renders each combination as an MP4 video (low quality for quick iteration).

Usage:
    python batch_render_all.py
"""

from pathlib import Path
import sys
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the project module
import project2_ex2_fbx_tiktok

# Paths
POINTCLOUDS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "pointclouds"
CHARACTERS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "characters"
OUTPUT_FOLDER = PROJECT_ROOT / "batch_output"

# Point clouds: 5 files
POINTCLOUDS = [
    "David_Bust_point_cloud.ply",
    "Hydrant_vertical_point_cloud.ply",
    "Mailbox_point_cloud.ply",
    "McLaren_point_cloud.ply",
    "Panzernashorn_Tobler_point_cloud.ply",
]

# Characters: 4 files
CHARACTERS = [
    "doozy-hiphop.fbx",
    "michelle-hiphop.fbx",
    "mouse-hiphop.fbx",
    "vegas-hiphop.fbx",
]

# Render settings
QUALITY = "low"
FPS = 24
OUTPUT_FORMAT = "mp4"


def get_pc_name(filename: str) -> str:
    """Extract clean name from pointcloud filename."""
    return filename.replace("_point_cloud.ply", "")


def get_char_name(filename: str) -> str:
    """Extract clean name from character filename."""
    return filename.replace(".fbx", "")


def main():
    """Generate all 20 combinations."""
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    total = len(POINTCLOUDS) * len(CHARACTERS)
    completed = 0
    failed = 0
    
    print(f"""
================================================================================
BATCH RENDER: Pointcloud + Character Combinations
Total combinations: {total}
Output quality: {QUALITY}
Output format: {OUTPUT_FORMAT}
================================================================================
""")
    
    start_time = time.time()
    
    for pc_idx, pc_file in enumerate(POINTCLOUDS, 1):
        pc_name = get_pc_name(pc_file)
        pc_path = POINTCLOUDS_FOLDER / pc_file
        
        for char_idx, char_file in enumerate(CHARACTERS, 1):
            char_name = get_char_name(char_file)
            char_path = CHARACTERS_FOLDER / char_file
            
            combination_num = (pc_idx - 1) * len(CHARACTERS) + char_idx
            
            print(f"\n{'-'*70}")
            print(f"[{combination_num}/{total}] {pc_name} + {char_name}")
            print(f"{'-'*70}")
            
            # Generate output filenames
            blend_name = f"{pc_name}_{char_name}.blend"
            blend_path = OUTPUT_FOLDER / blend_name
            
            video_name = f"{pc_name}_{char_name}.{OUTPUT_FORMAT}"
            video_path = OUTPUT_FOLDER / video_name
            
            # Step 1: Create scene
            print(f"\n[Step 1/2] Creating scene: {blend_name}")
            try:
                project2_ex2_fbx_tiktok.app([
                    "create",
                    str(pc_path),
                    "--character", str(char_path),
                    "--pc-rotation", "90,0,0",  # Rotate pointcloud 90 degrees on X axis
                    "--output", str(blend_path),
                ])
                print(f"[OK] Scene created")
            except SystemExit as e:
                if e.code == 0:
                    print(f"[OK] Scene created")
                else:
                    print(f"[FAIL] Scene creation failed (exit code: {e.code})")
                    failed += 1
                    continue
            except Exception as e:
                print(f"[ERROR] Scene creation failed: {e}")
                failed += 1
                continue
            
            # Step 2: Render video
            print(f"\n[Step 2/2] Rendering video: {video_name}")
            try:
                project2_ex2_fbx_tiktok.app([
                    "render",
                    str(blend_path),
                    "--format", OUTPUT_FORMAT,
                    "--quality", QUALITY,
                    "--fps", str(FPS),
                    "--output", str(video_path),
                ])
                print(f"[OK] Video rendered")
                
                # Get file size
                if video_path.exists():
                    size_mb = video_path.stat().st_size / (1024 * 1024)
                    print(f"    File size: {size_mb:.1f} MB")
                    completed += 1
                else:
                    print(f"[FAIL] Video file not found")
                    failed += 1
                    
            except SystemExit as e:
                if e.code == 0:
                    print(f"[OK] Video rendered")
                    if video_path.exists():
                        size_mb = video_path.stat().st_size / (1024 * 1024)
                        print(f"    File size: {size_mb:.1f} MB")
                        completed += 1
                else:
                    print(f"[FAIL] Video render failed (exit code: {e.code})")
                    failed += 1
            except Exception as e:
                print(f"[ERROR] Video render failed: {e}")
                failed += 1
    
    # Summary
    elapsed_time = time.time() - start_time
    elapsed_minutes = elapsed_time / 60
    
    print(f"\n{'='*70}")
    print(f"BATCH RENDER COMPLETE")
    print(f"{'='*70}")
    print(f"[OK] Completed: {completed}/{total}")
    print(f"[FAIL] Failed: {failed}/{total}")
    print(f"[TIME] Total time: {elapsed_minutes:.1f} minutes")
    print(f"[OUTPUT] Output folder: {OUTPUT_FOLDER}")
    print(f"{'='*70}\n")
    
    if completed == total:
        print("[SUCCESS] All 20 combinations rendered successfully!")
        return 0
    else:
        print(f"[WARNING] Some combinations failed. {completed} completed, {failed} failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
