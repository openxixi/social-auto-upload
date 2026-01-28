import os
import sys
import time
import logging
from datetime import datetime

# Setup logging
log_file = f"audio_to_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from playwright.sync_api import sync_playwright

def test_audio_to_video():
    """Test the audio to video generation"""
    
    # File paths
    audio_file = "generated_audio.wav"
    image_file = "test_img.png"
    output_dir = "output_video"
    prompt = "男人正在说话"
    url = "http://localhost:7860"
    
    logger.info("=" * 60)
    logger.info("Starting Audio to Video Generation Test")
    logger.info("=" * 60)
    
    # Check files
    logger.info(f"Checking audio file: {audio_file}")
    if not os.path.exists(audio_file):
        logger.error(f"✗ Audio file not found: {audio_file}")
        return False
    logger.info(f"✓ Audio file found: {os.path.getsize(audio_file)} bytes")
    
    logger.info(f"Checking image file: {image_file}")
    if not os.path.exists(image_file):
        logger.error(f"✗ Image file not found: {image_file}")
        return False
    logger.info(f"✓ Image file found: {os.path.getsize(image_file)} bytes")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"✓ Output directory ready: {output_dir}")
    
    try:
        logger.info("\nLaunching browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--disable-gpu"])
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(60000)
            
            logger.info(f"Navigating to {url}...")
            page.goto(url)
            
            logger.info("Waiting for page to load...")
            try:
                page.wait_for_load_state('load', timeout=60000)
                logger.info("✓ Page loaded (load state)")
            except Exception as e:
                logger.warning(f"Load state timeout, continuing anyway: {e}")
            
            page.wait_for_timeout(5000)
            logger.info("✓ Page ready")
            
            # Upload image
            logger.info("\n=== Uploading Image ===")
            file_inputs = page.locator("input[type='file']")
            count = file_inputs.count()
            logger.info(f"File inputs found: {count}")
            
            if count == 0:
                logger.error("No file inputs found")
                browser.close()
                return False
            
            try:
                logger.info(f"Uploading image: {image_file}")
                file_inputs.nth(0).set_input_files(image_file)
                page.wait_for_timeout(3000)
                logger.info("✓ Image uploaded")
            except Exception as e:
                logger.error(f"Failed to upload image: {e}")
                browser.close()
                return False
            
            # Upload audio
            logger.info("\n=== Uploading Audio ===")
            file_inputs = page.locator("input[type='file']")
            logger.info(f"File inputs found after image upload: {file_inputs.count()}")
            
            audio_input_index = 1  # Default to second input
            for idx in range(file_inputs.count()):
                try:
                    parent = file_inputs.nth(idx).locator("..")
                    parent_text = parent.inner_text()
                    if "驱动音频" in parent_text or "Drop Audio" in parent_text or "音频" in parent_text:
                        audio_input_index = idx
                        logger.info(f"✓ Found audio input at index {idx}")
                        break
                except:
                    pass
            
            try:
                logger.info(f"Uploading audio: {audio_file}")
                file_inputs.nth(audio_input_index).set_input_files(audio_file)
                page.wait_for_timeout(3000)
                logger.info("✓ Audio uploaded")
            except Exception as e:
                logger.error(f"Failed to upload audio: {e}")
                browser.close()
                return False
            
            # Set prompt
            logger.info("\n=== Setting Prompt ===")
            logger.info(f"Prompt: {prompt}")
            try:
                textareas = page.locator("textarea")
                if textareas.count() > 0:
                    textareas.first.fill(prompt)
                    page.wait_for_timeout(1000)
                    logger.info("✓ Prompt set")
            except Exception as e:
                logger.warning(f"Could not set prompt: {e}")
            
            # Click generate button
            logger.info("\n=== Starting Generation ===")
            gen_buttons = page.locator("button:has-text('开始生成')")
            if gen_buttons.count() == 0:
                logger.warning("'开始生成' button not found, looking for alternatives...")
                gen_buttons = page.locator("button").filter(has_text="生成")
                if gen_buttons.count() == 0:
                    all_buttons = page.locator("button")
                    logger.info(f"Total buttons: {all_buttons.count()}")
                    for i in range(min(10, all_buttons.count())):
                        btn_text = all_buttons.nth(i).inner_text()
                        if btn_text.strip():
                            logger.info(f"  Button {i}: '{btn_text[:40]}'")
            
            if gen_buttons.count() > 0:
                try:
                    logger.info("Clicking generate button...")
                    gen_buttons.first.click()
                    logger.info("✓ Generate button clicked")
                except Exception as e:
                    logger.error(f"Failed to click generate button: {e}")
                    browser.close()
                    return False
            else:
                logger.error("Could not find generate button")
                browser.close()
                return False
            
            # Wait for results
            logger.info("\n✓ Waiting for video generation (max 5 minutes)...")
            max_wait = 300
            poll_interval = 10
            elapsed = 0
            
            while elapsed < max_wait:
                page.wait_for_timeout(poll_interval * 1000)
                elapsed += poll_interval
                
                videos = page.locator("video")
                download_btns = page.locator("button:has-text('所有生成结果下载')")
                
                if videos.count() > 0 or download_btns.count() > 0:
                    logger.info(f"✓ Results detected after {elapsed} seconds!")
                    break
                
                progress = (elapsed / max_wait) * 100
                logger.info(f"⏳ Waiting... {elapsed}s ({progress:.0f}% timeout)")
            
            logger.info("✓ Generation complete or timeout reached")
            
            # Check results
            logger.info("\n=== Checking Results ===")
            page.wait_for_timeout(5000)
            
            videos = page.locator("video")
            logger.info(f"Video elements: {videos.count()}")
            
            download_btns = page.locator("button:has-text('所有生成结果下载')")
            logger.info(f"'All results download' buttons: {download_btns.count()}")
            
            if download_btns.count() > 0:
                logger.info("✓ Found result download button")
                try:
                    logger.info("Downloading results...")
                    with page.expect_download() as download_info:
                        download_btns.first.click()
                    download = download_info.value
                    output_file = os.path.join(output_dir, download.suggested_filename)
                    download.save_as(output_file)
                    logger.info(f"✓ Downloaded: {output_file}")
                    file_size = os.path.getsize(output_file)
                    logger.info(f"✓ File size: {file_size} bytes")
                    browser.close()
                    return True
                except Exception as e:
                    logger.error(f"Download failed: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            elif videos.count() > 0:
                logger.info("✓ Video found!")
                download_btns = page.locator("button:has-text('下载')")
                if download_btns.count() > 0:
                    try:
                        logger.info("Downloading video...")
                        with page.expect_download() as download_info:
                            download_btns.first.click()
                        download = download_info.value
                        output_file = os.path.join(output_dir, download.suggested_filename)
                        download.save_as(output_file)
                        logger.info(f"✓ Downloaded: {output_file}")
                        file_size = os.path.getsize(output_file)
                        logger.info(f"✓ File size: {file_size} bytes")
                        browser.close()
                        return True
                    except Exception as e:
                        logger.error(f"Download failed: {e}")
            else:
                logger.warning("No results found")
            
            browser.close()
            return False
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        logger.info("\n" + "=" * 60)
        logger.info(f"Log saved to: {log_file}")
        logger.info("=" * 60)

if __name__ == "__main__":
    success = test_audio_to_video()
    if success:
        logger.info("\n✓✓✓ SUCCESS ✓✓✓")
        sys.exit(0)
    else:
        logger.error("\n✗✗✗ FAILED ✗✗✗")
        sys.exit(1)
