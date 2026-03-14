"""Batch render all pointcloud + character combinations.

This script generates all 20 combinations of:
- 5 pointclouds
- 4 characters

And renders each as a low-quality MP4 file for quick iteration.
"""

from pathlib import Path
import sys
import time
import io
import os

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project2 to path to import the script
sys.path.insert(0, str(Path(__file__).parent))

# Import the project2_ex2 module
import project2_ex2_fbx_tiktok as project_module

# Paths
PROJECT_ROOT = Path(__file__).parent
POINTCLOUDS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "pointclouds"
CHARACTERS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "characters"
OUTPUT_FOLDER = PROJECT_ROOT / "batch_output"

# Point cloud files
POINTCLOUDS = [
    "David_Bust_point_cloud.ply",
    "Hydrant_vertical_point_cloud.ply",
    "Mailbox_point_cloud.ply",
    "McLaren_point_cloud.ply",
    "Panzernashorn_Tobler_point_cloud.ply",
]

# Character FBX files
CHARACTERS = [
    "doozy-hiphop.fbx",
    "michelle-hiphop.fbx",
    "mouse-hiphop.fbx",
    "vegas-hiphop.fbx",
]

# Render settings
QUALITY = "low"  # Use low quality for faster rendering
FPS = 24
OUTPUT_FORMAT = "mp4"  # or "png"


def get_python_executable() -> str:
    """Get the path to the Python executable in the venv."""
    if sys.platform == "win32":
        return str(Path(sys.prefix) / "Scripts" / "python.exe")
    else:
        return str(Path(sys.prefix) / "bin" / "python")


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful."""
    try:
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✓ {description}")
            return True
        else:
            print(f"   ✗ {description}")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"   ✗ {description} - Exception: {e}")
        return False


def get_pc_name(filename: str) -> str:
    """Extract clean name from pointcloud filename."""
    # Remove .ply extension and get just the name
    return filename.replace("_point_cloud.ply", "")


def get_char_name(filename: str) -> str:
    """Extract clean name from character filename."""
    # Remove .fbx extension
    return filename.replace(".fbx", "")


def main():
    """Generate all 20 combinations."""
    output_folder = OUTPUT_FOLDER
    output_folder.mkdir(parents=True, exist_ok=True)
    
    python_exe = get_python_executable()
    script_path = PROJECT_ROOT / "project2_ex2_fbx_tiktok.py"
    
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
        
        for char_idx, char_file in enumerate(CHARACTERS, 1):
            char_name = get_char_name(char_file)
            
            combination_num = (pc_idx - 1) * len(CHARACTERS) + char_idx
            
            print(f"\n{'-'*70}")
            print(f"[{combination_num}/{total}] {pc_name} + {char_name}")
            print(f"{'-'*70}")
            
            # Generate output filenames
            blend_name = f"{pc_name}_{char_name}.blend"
            blend_path = output_folder / blend_name
            
            video_name = f"{pc_name}_{char_name}.{OUTPUT_FORMAT}"
            video_path = output_folder / video_name
            
            # Step 1: Create scene
            print(f"\n[Step 1/2] Creating scene...")
            # Pass relative paths from the script's directory
            pc_full_path = POINTCLOUDS_FOLDER / pc_file
            char_full_path = CHARACTERS_FOLDER / char_file
            
            create_cmd = [
                python_exe,
                str(script_path),
                "create",
                str(pc_full_path),  # Full path to pointcloud
                "--character", str(char_full_path),  # Full path to character
                "--rotation", "90,0,0",  # X-axis rotation 90 degrees
                "--output", str(blend_path),
            ]
            
            if not run_command(create_cmd, f"Create scene: {blend_name}"):
                failed += 1
                print(f">> Skipping render for this combination")
                continue
            
            # Step 2: Render video
            print(f"\n[Step 2/2] Rendering video...")
            render_cmd = [
                python_exe,
                str(script_path),
                "render",
                str(blend_path),
                "--format", OUTPUT_FORMAT,
                "--quality", QUALITY,
                "--fps", str(FPS),
                "--output", str(video_path),
            ]
            
            if run_command(render_cmd, f"Render video: {video_name}"):
                completed += 1
                # Get file size
                if video_path.exists():
                    size_mb = video_path.stat().st_size / (1024 * 1024)
                    print(f"   [File] {size_mb:.1f} MB")
            else:
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
    print(f"[OUTPUT] Output folder: {output_folder}")
    print(f"{'='*70}\n")
    
    if completed == total:
        print("[SUCCESS] All combinations rendered successfully!")
        return 0
    else:
        print(f"[WARNING] Some combinations failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
