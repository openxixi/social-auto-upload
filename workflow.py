#!/usr/bin/env python
"""
Complete workflow: Text -> TTS Audio -> Digital Human Video
"""
import os
import sys
import argparse
import logging
import socket
from txt_to_voice import automate_tts
from audio_to_video import audio_to_video

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_generated_audio(output_dir, preferred_name="generated_audio.wav"):
    """Find generated audio file in output directory.

    Returns the path if found, otherwise None.
    """
    preferred_path = os.path.join(output_dir, preferred_name)
    if os.path.exists(preferred_path):
        return preferred_path

    if not os.path.isdir(output_dir):
        return None

    audio_exts = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
    candidates = []
    for fname in os.listdir(output_dir):
        fpath = os.path.join(output_dir, fname)
        if not os.path.isfile(fpath):
            continue
        _, ext = os.path.splitext(fname)
        if ext.lower() in audio_exts:
            candidates.append(fpath)

    if not candidates:
        return None

    # Use the most recently modified audio file
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]

def check_service_available(url):
    """Check if a service is available at the given URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.warning(f"Could not check service availability: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Complete workflow: Text -> TTS Audio -> Digital Human Video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate video from text
  python workflow.py text_file.txt voice_reference.m4a portrait.jpg output_dir/
  
  # Generate video with custom prompt
  python workflow.py text_file.txt voice_reference.m4a portrait.jpg output_dir/ --prompt "男人正在说话"
        """
    )
    
    parser.add_argument("text_file", help="Path to the text file")
    parser.add_argument("audio_reference", help="Path to the reference audio file (for TTS voice)")
    parser.add_argument("image_file", help="Path to the portrait image file")
    parser.add_argument("output_dir", help="Directory to save outputs")
    parser.add_argument("--prompt", default="男人正在说话", help="Prompt for digital human")
    parser.add_argument("--vram-swap-coef", type=float, default=40, help="显存交换系数")
    parser.add_argument("--keep-audio", action="store_true", help="Keep generated audio file")
    parser.add_argument("--tts-url", default="http://localhost:7866", help="URL of TTS service")
    parser.add_argument("--video-url", default="http://localhost:7860", help="URL of digital human service")
    parser.add_argument("--skip-tts", action="store_true", help="Skip TTS generation (use existing audio)")
    parser.add_argument(
        "--audio-file",
        help="Path to an existing audio file to use when --skip-tts is set",
        default=None,
    )
    
    args = parser.parse_args()
    
    # Validate input files
    required_files = [args.text_file, args.audio_reference, args.image_file]
    for f in required_files:
        if not os.path.exists(f):
            logger.error(f"✗ Error: File not found: {f}")
            return False

    if args.audio_file and not os.path.exists(args.audio_file):
        logger.error(f"✗ Error: File not found: {args.audio_file}")
        return False
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("TEXT TO VIDEO WORKFLOW")
    logger.info("=" * 60)
    
    gen_audio = os.path.join(args.output_dir, "generated_audio.wav")
    
    # Step 1: Generate TTS audio (if not skipped)
    if not args.skip_tts:
        logger.info("\n[STEP 1/2] Generating TTS audio from text...")
        logger.info("-" * 60)
        logger.info(f"TTS Service URL: {args.tts_url}")
        
        # Check if TTS service is available
        if not check_service_available(args.tts_url):
            logger.error(f"✗ TTS service not available at {args.tts_url}")
            logger.info("Please start the TTS service first, or use --skip-tts if audio already exists")
            return False
        
        logger.info("✓ TTS service is available")
        
        try:
            logger.info(f"Text file: {args.text_file}")
            logger.info(f"Reference audio: {args.audio_reference}")
            logger.info(f"Output dir: {args.output_dir}")
            
            automate_tts(args.text_file, args.audio_reference, args.output_dir, url=args.tts_url)
            
            # Check if audio was generated
            resolved_audio = find_generated_audio(args.output_dir)
            if resolved_audio and os.path.exists(resolved_audio):
                gen_audio = resolved_audio
                size = os.path.getsize(gen_audio)
                logger.info(f"✓ Audio generated: {gen_audio} ({size} bytes)")
            else:
                logger.error("✗ Audio generation failed - no audio file found")
                logger.info(f"Contents of {args.output_dir}:")
                if os.path.exists(args.output_dir):
                    for item in os.listdir(args.output_dir):
                        logger.info(f"  - {item}")
                return False
        except Exception as e:
            logger.error(f"✗ TTS generation error: {e}", exc_info=True)
            return False
    else:
        logger.info("\n[STEP 1/2] Skipping TTS generation (--skip-tts)")
        logger.info("-" * 60)
        # Priority: explicit --audio-file > output_dir generated audio > audio_reference
        resolved_audio = None
        if args.audio_file:
            resolved_audio = args.audio_file
        else:
            resolved_audio = find_generated_audio(args.output_dir)

        if not resolved_audio or not os.path.exists(resolved_audio):
            if os.path.exists(args.audio_reference):
                logger.warning(
                    "No generated audio found in output_dir; using audio_reference as input audio."
                )
                resolved_audio = args.audio_reference

        if not resolved_audio or not os.path.exists(resolved_audio):
            logger.error("✗ Audio file not found for video generation")
            logger.info("Provide --audio-file or generate audio first or remove --skip-tts flag")
            return False

        gen_audio = resolved_audio
        size = os.path.getsize(gen_audio)
        logger.info(f"✓ Using existing audio: {gen_audio} ({size} bytes)")
    
    # Step 2: Generate digital human video
    logger.info("\n[STEP 2/2] Generating digital human video...")
    logger.info("-" * 60)
    logger.info(f"Video Service URL: {args.video_url}")
    
    # Check if video service is available
    if not check_service_available(args.video_url):
        logger.error(f"✗ Video service not available at {args.video_url}")
        logger.info("Please start the video generation service first")
        return False
    
    logger.info("✓ Video service is available")
    
    try:
        logger.info(f"Audio: {gen_audio}")
        logger.info(f"Image: {args.image_file}")
        logger.info(f"Prompt: {args.prompt}")
        
        success = audio_to_video(
            audio_file_path=gen_audio,
            image_file_path=args.image_file,
            output_dir=args.output_dir,
            prompt=args.prompt,
            url=args.video_url,
            vram_swap_coef=args.vram_swap_coef
        )
        
        if not success:
            logger.error("✗ Video generation failed")
            return False
        
    except Exception as e:
        logger.error(f"✗ Video generation error: {e}", exc_info=True)
        return False
    
    # Cleanup if not keeping audio
    if not args.keep_audio and os.path.exists(gen_audio):
        os.remove(gen_audio)
        logger.info(f"✓ Cleaned up temporary audio file")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓✓✓ WORKFLOW COMPLETE ✓✓✓")
    logger.info("=" * 60)
    logger.info(f"Output directory: {args.output_dir}")
    logger.info("Generated files:")
    for f in os.listdir(args.output_dir):
        fp = os.path.join(args.output_dir, f)
        size = os.path.getsize(fp)
        logger.info(f"  - {f} ({size:,} bytes)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
