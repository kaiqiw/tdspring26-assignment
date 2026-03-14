#!/usr/bin/env python3
"""Test first combination to verify the batch render pipeline."""

from pathlib import Path
import sys
import subprocess

PROJECT_ROOT = Path(__file__).parent / "project2"
BATCH_SCRIPT = PROJECT_ROOT / "batch_render.py"

# Get Python executable
if sys.platform == "win32":
    python_exe = str(Path(sys.prefix) / "Scripts" / "python.exe")
else:
    python_exe = str(Path(sys.prefix) / "bin" / "python")

print(f"""
{'='*70}
TEST: Batch Render Pipeline (First Combination Only)
{'='*70}

Using Python: {python_exe}
Script: {BATCH_SCRIPT}

This will:
1. Import David_Bust point cloud with X-axis 90° rotation
2. Import doozy character
3. Create scene with RadianceField node
4. Render as low-quality MP4

Estimated time: 5-10 minutes
""")

# Create a test version that only runs first combination
test_code = '''
from pathlib import Path
import sys
import time
import io
import os
import subprocess

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, str(Path(__file__).parent))

PROJECT_ROOT = Path(__file__).parent
POINTCLOUDS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "pointclouds"
CHARACTERS_FOLDER = PROJECT_ROOT / "pointcloud_character_assets" / "characters"
OUTPUT_FOLDER = PROJECT_ROOT / "batch_output_test"

# Test only first combination
POINTCLOUDS = ["David_Bust_point_cloud.ply"]
CHARACTERS = ["doozy-hiphop.fbx"]

QUALITY = "low"
FPS = 24
OUTPUT_FORMAT = "mp4"

def get_python_executable() -> str:
    if sys.platform == "win32":
        return str(Path(sys.prefix) / "Scripts" / "python.exe")
    else:
        return str(Path(sys.prefix) / "bin" / "python")

def run_command(cmd: list, description: str) -> bool:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✓ {description}")
            return True
        else:
            print(f"   ✗ {description}")
            if result.stderr:
                print(f"   Error: {result.stderr[:300]}")
            return False
    except Exception as e:
        print(f"   ✗ {description} - Exception: {e}")
        return False

def get_pc_name(filename: str) -> str:
    return filename.replace("_point_cloud.ply", "")

def get_char_name(filename: str) -> str:
    return filename.replace(".fbx", "")

output_folder = OUTPUT_FOLDER
output_folder.mkdir(parents=True, exist_ok=True)

python_exe = get_python_executable()
script_path = PROJECT_ROOT / "project2_ex2_fbx_tiktok.py"

pc_file = POINTCLOUDS[0]
char_file = CHARACTERS[0]

pc_name = get_pc_name(pc_file)
char_name = get_char_name(char_file)

print(f"\\n{'-'*70}")
print(f"TEST: {pc_name} + {char_name}")
print(f"{'-'*70}")

blend_name = f"{pc_name}_{char_name}.blend"
blend_path = output_folder / blend_name

video_name = f"{pc_name}_{char_name}.{OUTPUT_FORMAT}"
video_path = output_folder / video_name

print(f"\\n[Step 1/2] Creating scene...")
pc_full_path = POINTCLOUDS_FOLDER / pc_file
char_full_path = CHARACTERS_FOLDER / char_file

create_cmd = [
    python_exe,
    str(script_path),
    "create",
    str(pc_full_path),
    "--character", str(char_full_path),
    "--rotation", "90,0,0",
    "--output", str(blend_path),
]

print(f"  PC: {pc_full_path}")
print(f"  Char: {char_full_path}")

if not run_command(create_cmd, f"Create scene: {blend_name}"):
    print("\\n✗ Scene creation failed!")
    sys.exit(1)

print(f"\\n[Step 2/2] Rendering video...")
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
    if video_path.exists():
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"   [File] {size_mb:.1f} MB")
        print(f"\\n✓ TEST PASSED: {video_path}")
    else:
        print(f"\\n✗ Video file not created")
        sys.exit(1)
else:
    print("\\n✗ Rendering failed!")
    sys.exit(1)

print(f"\\n{'='*70}")
print(f"TEST COMPLETE - Ready for full batch render!")
print(f"{'='*70}\\n")
'''

# Write and run test script
test_script = PROJECT_ROOT / "test_first_combination.py"
test_script.write_text(test_code)

print(f"Running test...\n")
result = subprocess.run([python_exe, str(test_script)], cwd=PROJECT_ROOT)
sys.exit(result.returncode)
