import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run txt_to_voice then audio_to_video")
    parser.add_argument("text_file", help="Path to text file")
    parser.add_argument("ref_audio", help="Path to reference audio")
    parser.add_argument("audio_out_dir", help="Output dir for generated audio")
    parser.add_argument("image_file", help="Path to image file")
    parser.add_argument("video_out_dir", help="Output dir for generated video")
    parser.add_argument("--prompt", default="男人正在说话", help="Prompt for audio_to_video")
    args = parser.parse_args()

    text_file = Path(args.text_file)
    ref_audio = Path(args.ref_audio)
    audio_out_dir = Path(args.audio_out_dir)
    image_file = Path(args.image_file)
    video_out_dir = Path(args.video_out_dir)

    cmd1 = (
        f'python .\\txt_to_voice.py "{text_file}" "{ref_audio}" "{audio_out_dir}"'
    )
    cmd2 = (
        f'python .\\audio_to_video.py "{audio_out_dir / "generated_audio.wav"}" '
        f'"{image_file}" "{video_out_dir}" --prompt "{args.prompt}"'
    )

    run_cmd(cmd1)
    run_cmd(cmd2)


if __name__ == "__main__":
    main()
