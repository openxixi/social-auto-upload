#!/usr/bin/env python
"""
Rename the latest generated video to the correct filename
"""
import os
import sys

def rename_latest_video(output_dir, target_filename):
    """Find and rename the latest .mp4 file to target filename"""
    
    if not os.path.exists(output_dir):
        print(f"✗ Output directory not found: {output_dir}")
        return False
    
    # Find all mp4 files
    mp4_files = []
    for fname in os.listdir(output_dir):
        if fname.endswith('.mp4'):
            fpath = os.path.join(output_dir, fname)
            if os.path.isfile(fpath):
                mtime = os.path.getmtime(fpath)
                mp4_files.append((fpath, mtime, fname))
    
    if not mp4_files:
        print(f"✗ No .mp4 files found in {output_dir}")
        return False
    
    # Sort by modification time (newest first)
    mp4_files.sort(key=lambda x: x[1], reverse=True)
    
    latest_file = mp4_files[0][0]
    latest_name = mp4_files[0][2]
    
    print(f"Latest video file: {latest_name}")
    print(f"Size: {os.path.getsize(latest_file):,} bytes")
    
    target_path = os.path.join(output_dir, target_filename)
    
    # Check if already correctly named
    if latest_name == target_filename:
        print(f"✓ File is already named correctly: {target_filename}")
        return True
    
    # Check if target already exists
    if os.path.exists(target_path):
        print(f"⚠ Target file already exists: {target_filename}")
        response = input("Remove existing file? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            return False
        os.remove(target_path)
        print(f"✓ Removed existing file")
    
    # Rename
    print(f"Renaming:")
    print(f"  From: {latest_name}")
    print(f"  To:   {target_filename}")
    
    os.rename(latest_file, target_path)
    
    if os.path.exists(target_path):
        print(f"✓ Successfully renamed to: {target_filename}")
        print(f"✓ Full path: {target_path}")
        return True
    else:
        print(f"✗ Rename failed")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python rename_latest_video.py <output_dir> <target_filename>")
        print("Example: python rename_latest_video.py ./output_video/ 3_余喜致良知1.mp4")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    target_filename = sys.argv[2]
    
    success = rename_latest_video(output_dir, target_filename)
    sys.exit(0 if success else 1)
