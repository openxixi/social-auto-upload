import os
import sys
import time
import argparse
import logging
import shutil
from datetime import datetime
from playwright.sync_api import sync_playwright

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def audio_to_video(audio_file_path, image_file_path, output_dir, prompt="女人正在说话", url="http://localhost:7860", vram_swap_coef=10, output_filename="generated_video.mp4"):
    """
    Upload audio and image to localhost:7860 to generate digital human video
    
    Args:
        audio_file_path: Path to the audio file
        image_file_path: Path to the image file (portrait)
        output_dir: Directory to save the generated video
        prompt: Prompt for the digital human (Chinese description)
        url: URL of the InfiniteTalk service
        output_filename: Name of the output video file (default: generated_video.mp4)
    """
    start_time = datetime.now()
    logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if files exist
    audio_abs_path = os.path.abspath(audio_file_path)
    image_abs_path = os.path.abspath(image_file_path)
    
    if not os.path.exists(audio_abs_path):
        logger.error(f"✗ Error: Audio file not found at {audio_abs_path}")
        return False
    logger.info(f"✓ Audio file found: {audio_abs_path} ({os.path.getsize(audio_abs_path)} bytes)")
    
    if not os.path.exists(image_abs_path):
        logger.error(f"✗ Error: Image file not found at {image_abs_path}")
        return False
    logger.info(f"✓ Image file found: {image_abs_path} ({os.path.getsize(image_abs_path)} bytes)")
    
    try:
        with sync_playwright() as p:
            # Use headless=True for better stability, or False to see browser
            logger.info(f"Launching browser and navigating to {url}...")
            try:
                browser = p.chromium.launch(headless=False, args=["--disable-gpu"])
            except Exception as e:
                msg = str(e)
                if "Executable doesn't exist" in msg:
                    logger.warning("Playwright Chromium 未安装，尝试使用本机 Chrome 作为兜底...")
                    try:
                        browser = p.chromium.launch(channel="chrome", headless=False, args=["--disable-gpu"])
                    except Exception as e2:
                        logger.error("启动浏览器失败。请先安装 Playwright 浏览器：python -m playwright install", exc_info=True)
                        return False
                else:
                    raise
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(60000)  # 60 second timeout for all operations
            page.goto(url)
            
            # Wait for page to load - use load instead of networkidle for faster loading
            logger.info("Waiting for page to load...")
            try:
                page.wait_for_load_state('load', timeout=60000)  # 60 seconds
                logger.info("✓ Page loaded (load state)")
            except Exception as e:
                logger.warning(f"Load state timeout, continuing anyway: {e}")
            
            # Give page extra time to fully render
            page.wait_for_timeout(5000)
            logger.info("✓ Page ready")
        
            # Find and upload image
            logger.info("\n=== Uploading Image ===")
            file_inputs = page.locator("input[type='file']")
            logger.info(f"File inputs found: {file_inputs.count()}")
            
            if file_inputs.count() == 0:
                logger.warning("No file inputs found, waiting a bit longer...")
                page.wait_for_timeout(3000)
                file_inputs = page.locator("input[type='file']")
                logger.info(f"File inputs found after wait: {file_inputs.count()}")
            
            if file_inputs.count() < 1:
                logger.error("No file input found")
                browser.close()
                return False
            
            try:
                # First file input is for image
                logger.info(f"Uploading image: {image_abs_path}")
                file_inputs.nth(0).set_input_files(image_abs_path)
                page.wait_for_timeout(3000)
                logger.info("✓ Image uploaded")
            except Exception as e:
                logger.error(f"Failed to upload image: {e}", exc_info=True)
                browser.close()
                return False
        
            # Find and upload audio
            logger.info("\n=== Uploading Audio ===")
            # Reload file inputs as they may have changed
            file_inputs = page.locator("input[type='file']")
            logger.info(f"File inputs available: {file_inputs.count()}")
            
            # Find the audio upload input by checking parent text
            audio_input_index = -1
            for idx in range(file_inputs.count()):
                try:
                    parent = file_inputs.nth(idx).locator("..")
                    parent_text = parent.inner_text()
                    logger.debug(f"Input {idx} parent text: {parent_text[:100]}")
                    if "驱动音频" in parent_text or "Drop Audio" in parent_text or "音频" in parent_text:
                        audio_input_index = idx
                        logger.info(f"✓ Found audio input at index {idx}")
                        break
                except Exception as debug_e:
                    logger.debug(f"Error checking input {idx}: {debug_e}")
            
            if audio_input_index < 0:
                # Fallback: try second file input
                audio_input_index = 1
                logger.warning(f"Using fallback audio input index: {audio_input_index}")
            
            try:
                logger.info(f"Uploading audio: {audio_abs_path}")
                file_inputs.nth(audio_input_index).set_input_files(audio_abs_path)
                page.wait_for_timeout(3000)
                logger.info("✓ Audio uploaded")
            except Exception as e:
                logger.error(f"Failed to upload audio: {e}", exc_info=True)
                browser.close()
                return False
        
            # Set prompt
            logger.info("\n=== Setting Prompt ===")
            logger.info(f"Prompt: {prompt}")
            try:
                textareas = page.locator("textarea")
                logger.info(f"Textareas found: {textareas.count()}")
                if textareas.count() > 0:
                    textareas.first.fill(prompt)
                    page.wait_for_timeout(1000)
                    logger.info("✓ Prompt set")
                else:
                    logger.warning("No textarea found for prompt")
            except Exception as e:
                logger.warning(f"Could not set prompt: {e}", exc_info=True)

            # Set VRAM swap coefficient
            logger.info("\n=== Setting VRAM Swap Coefficient ===")
            logger.info(f"显存交换系数: {vram_swap_coef}")
            try:
                label = page.locator("text=显存交换系数")
                if label.count() > 0:
                    number_input = label.first.locator("xpath=following::input[1]")
                    if number_input.count() == 0:
                        number_input = label.first.locator("..")
                        number_input = number_input.locator("input[type='number']")
                    if number_input.count() == 0:
                        number_input = label.first.locator("..")
                        number_input = number_input.locator("input")
                    if number_input.count() > 0:
                        number_input.first.fill(str(vram_swap_coef))
                        page.wait_for_timeout(500)
                        logger.info("✓ 显存交换系数已设置为 10")
                    else:
                        logger.warning("未找到显存交换系数输入框")
                else:
                    logger.warning("未找到显存交换系数标签")
            except Exception as e:
                logger.warning(f"设置显存交换系数失败: {e}", exc_info=True)
        
            # Find and click generate button
            logger.info("\n=== Starting Generation ===")
            gen_buttons = page.locator("button:has-text('开始生成')")
            if gen_buttons.count() == 0:
                logger.warning("'开始生成' button not found, looking for alternative...")
                # Try to find any button with "生成" in the text
                all_buttons = page.locator("button")
                logger.info(f"Total buttons on page: {all_buttons.count()}")
                
                for i in range(min(20, all_buttons.count())):
                    btn_text = all_buttons.nth(i).inner_text()
                    if "生成" in btn_text or "Generate" in btn_text:
                        logger.info(f"  Button {i}: '{btn_text}'")
                
                gen_buttons = page.locator("button").filter(has_text="生成")
            
            if gen_buttons.count() > 0:
                logger.info(f"Found {gen_buttons.count()} generate button(s)")
                try:
                    gen_buttons.first.click()
                    logger.info("✓ Generate button clicked")
                except Exception as e:
                    logger.warning(f"Failed to click generate button: {e}", exc_info=True)
            else:
                logger.error("Could not find generate button")
                browser.close()
                return False
        
            # Wait for generation
            logger.info("\n✓ Waiting for video generation (this may take several minutes)...")
            
            # Poll for results
            max_wait = 7200  # 2 hours maximum
            poll_interval = 10  # Check every 10 seconds
            elapsed = 0
            
            try:
                while elapsed < max_wait:
                    try:
                        page.wait_for_timeout(poll_interval * 1000)
                    except Exception as wait_error:
                        logger.warning(f"Wait timeout error (continuing): {wait_error}")
                        pass
                    
                    elapsed += poll_interval
                    
                    try:
                        videos = page.locator("video")
                        download_btns = page.locator("button:has-text('所有生成结果下载')")
                        
                        if videos.count() > 0 or download_btns.count() > 0:
                            logger.info(f"✓ Results detected after {elapsed} seconds!")
                            break
                    except Exception as check_error:
                        logger.debug(f"Error checking for results: {check_error}")
                        continue
                    
                    progress = (elapsed / max_wait) * 100
                    logger.info(f"⏳ Waiting... {elapsed}s ({progress:.0f}% of max timeout)")
                
                logger.info("✓ Generation complete or timeout reached")
            except KeyboardInterrupt:
                logger.warning("Generation interrupted by user")
            except Exception as e:
                logger.warning(f"Error during waiting: {e}")
                pass
        
            # Check for results
            logger.info("\n=== Checking Results ===")
            page.wait_for_timeout(5000)
            
            # Try to find video in results gallery
            videos = page.locator("video")
            logger.info(f"Video elements found: {videos.count()}")
            
            # Debug: Check page for any media or images
            images = page.locator("img")
            logger.info(f"Image elements found: {images.count()}")
            
            # Check for download buttons
            all_buttons = page.locator("button")
            logger.info(f"Total buttons: {all_buttons.count()}")
            
            download_btns = page.locator("button:has-text('下载')")
            logger.info(f"Download buttons found: {download_btns.count()}")
            
            # List some button texts for debugging
            logger.info("Button samples:")
            for i in range(min(15, all_buttons.count())):
                btn_text = all_buttons.nth(i).inner_text()[:50]
                if btn_text.strip():
                    logger.info(f"  Button {i}: '{btn_text}'")
            
            # Check if there's a results gallery div
            gallery = page.locator("div:has-text('生成结果')")
            logger.info(f"Gallery sections found: {gallery.count()}")
            
            # Check for results gallery download buttons instead of video elements
            download_btns = page.locator("button:has-text('所有生成结果下载')")
            logger.info(f"'All results download' buttons: {download_btns.count()}")
        
            if download_btns.count() > 0:
                logger.info("✓ Found result download button!")
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    logger.info("Waiting for download...")
                    with page.expect_download() as download_info:
                        download_btns.first.click()
                    download = download_info.value
                    output_file = os.path.join(output_dir, download.suggested_filename)
                    download.save_as(output_file)
                    file_size = os.path.getsize(output_file)
                    logger.info(f"✓ Downloaded results to: {output_file} ({file_size} bytes)")
                    browser.close()
                    return True
                except Exception as e:
                    logger.error(f"Download failed: {e}", exc_info=True)
            
            if videos.count() > 0:
                logger.info("✓ Video generated!")
                
                # Try multiple methods to download the video
                download_success = False
                
                # Method 1: Look for download icon/link (⇣ symbol or download aria-label)
                try:
                    # Try finding elements with download icon or aria-label
                    download_links = page.locator('a[download], a:has-text("⇣"), button:has-text("⇣"), [aria-label*="download" i], [aria-label*="下载" i]')
                    if download_links.count() > 0:
                        logger.info(f"Found {download_links.count()} download link/button(s) with icon")
                        try:
                            logger.info("Clicking download link/button...")
                            with page.expect_download(timeout=30000) as download_info:
                                download_links.first.click()
                            download = download_info.value
                            output_file = os.path.join(output_dir, download.suggested_filename)
                            os.makedirs(output_dir, exist_ok=True)
                            download.save_as(output_file)
                            file_size = os.path.getsize(output_file)
                            logger.info(f"✓ Downloaded video to: {output_file} ({file_size} bytes)")
                            download_success = True
                        except Exception as e:
                            logger.warning(f"Download via icon/link failed: {e}")
                except Exception as e:
                    logger.debug(f"Error searching for download icon: {e}")
                
                # Method 2: Try different button text patterns
                if not download_success:
                    download_patterns = ["下载", "Download", "保存", "Save"]
                    for pattern in download_patterns:
                        download_btns = page.locator(f"button:has-text('{pattern}')")
                        if download_btns.count() > 0:
                            logger.info(f"Found {download_btns.count()} '{pattern}' button(s)")
                            try:
                                logger.info("Waiting for download...")
                                with page.expect_download(timeout=30000) as download_info:
                                    download_btns.first.click()
                                download = download_info.value
                                output_file = os.path.join(output_dir, download.suggested_filename)
                                os.makedirs(output_dir, exist_ok=True)
                                download.save_as(output_file)
                                file_size = os.path.getsize(output_file)
                                logger.info(f"✓ Downloaded video to: {output_file} ({file_size} bytes)")
                                download_success = True
                                break
                            except Exception as e:
                                logger.warning(f"Download via '{pattern}' button failed: {e}")
                
                # Method 2: Right-click on video and download
                if not download_success:
                    logger.info("Trying to extract video URL directly...")
                    try:
                        video_element = videos.first
                        video_src = video_element.get_attribute("src")
                        if video_src:
                            logger.info(f"Found video source: {video_src}")
                            
                            # If it's a blob URL, we need to download differently
                            if video_src.startswith("blob:"):
                                logger.info("Video is a blob URL, attempting to download via page context...")
                                logger.info(f"Target output filename: {output_filename}")
                                # Try to trigger download via JavaScript
                                page.evaluate("""
                                    (videoElement, filename) => {
                                        const a = document.createElement('a');
                                        a.href = videoElement.src;
                                        a.download = filename;
                                        document.body.appendChild(a);
                                        a.click();
                                        document.body.removeChild(a);
                                    }
                                """, video_element.element_handle(), output_filename)
                                
                                # Wait for download
                                try:
                                    with page.expect_download(timeout=30000) as download_info:
                                        pass
                                    download = download_info.value
                                    logger.info(f"Browser suggested filename: {download.suggested_filename}")
                                    
                                    # Save to a temporary path first
                                    temp_path = os.path.join(output_dir, download.suggested_filename)
                                    output_file = os.path.join(output_dir, output_filename)
                                    logger.info(f"Downloading to temp: {temp_path}")
                                    logger.info(f"Will rename to: {output_file}")
                                    
                                    os.makedirs(output_dir, exist_ok=True)
                                    
                                    # Download to temp location
                                    download.save_as(temp_path)
                                    logger.info(f"✓ File downloaded to temp location")
                                    
                                    # Wait a moment for file handle to be released
                                    page.wait_for_timeout(500)
                                    
                                    # Verify temp file exists
                                    if not os.path.exists(temp_path):
                                        logger.error(f"✗ Temp file not found after download: {temp_path}")
                                        raise FileNotFoundError(f"Downloaded file not found: {temp_path}")
                                    
                                    temp_size = os.path.getsize(temp_path)
                                    logger.info(f"✓ Temp file size: {temp_size} bytes")
                                    
                                    # Remove target file if it exists
                                    if os.path.exists(output_file):
                                        logger.warning(f"Target file already exists, removing: {output_file}")
                                        try:
                                            os.remove(output_file)
                                        except Exception as del_err:
                                            logger.warning(f"Could not remove existing file: {del_err}")
                                    
                                    # Rename to target filename using shutil.move for better reliability
                                    logger.info(f"Renaming {os.path.basename(temp_path)} -> {os.path.basename(output_file)}")
                                    shutil.move(temp_path, output_file)
                                    
                                    # Verify rename succeeded
                                    if not os.path.exists(output_file):
                                        logger.error(f"✗ Rename failed, target file not found: {output_file}")
                                        raise FileNotFoundError(f"Renamed file not found: {output_file}")
                                    
                                    file_size = os.path.getsize(output_file)
                                    logger.info(f"✓ Successfully renamed and saved video to: {output_file} ({file_size} bytes)")
                                    download_success = True
                                except Exception as e:
                                    logger.error(f"✗ Blob download/rename failed: {e}")
                                    logger.error(f"Download exception details:", exc_info=True)
                                    
                                    # Try to salvage: check if temp file was downloaded
                                    try:
                                        temp_path = os.path.join(output_dir, download.suggested_filename) if 'download' in locals() else None
                                        if temp_path and os.path.exists(temp_path):
                                            logger.warning(f"Attempting to recover: temp file exists at {temp_path}")
                                            output_file = os.path.join(output_dir, output_filename)
                                            
                                            # Remove target if exists
                                            if os.path.exists(output_file):
                                                os.remove(output_file)
                                            
                                            # Try rename again
                                            shutil.move(temp_path, output_file)
                                            
                                            if os.path.exists(output_file):
                                                file_size = os.path.getsize(output_file)
                                                logger.info(f"✓ Recovery successful: {output_file} ({file_size} bytes)")
                                                download_success = True
                                    except Exception as recovery_error:
                                        logger.error(f"Recovery attempt failed: {recovery_error}")
                            else:
                                # Direct URL, can download using requests or similar
                                logger.info(f"Direct video URL found, saving to output directory...")
                                logger.info(f"Target output filename: {output_filename}")
                                import requests
                                response = requests.get(video_src)
                                output_file = os.path.join(output_dir, output_filename)
                                logger.info(f"Saving as: {output_file}")
                                os.makedirs(output_dir, exist_ok=True)
                                with open(output_file, 'wb') as f:
                                    f.write(response.content)
                                file_size = os.path.getsize(output_file)
                                logger.info(f"✓ Downloaded video to: {output_file} ({file_size} bytes)")
                                download_success = True
                    except Exception as e:
                        logger.error(f"Failed to extract and download video: {e}", exc_info=True)
                
                browser.close()
                return download_success
            else:
                logger.warning("No video found in results")
            
            browser.close()
            return False
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return False
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"总耗时: {duration}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate digital human video from audio and image")
    parser.add_argument("audio_file", help="Path to the audio file")
    parser.add_argument("image_file", help="Path to the image file")
    parser.add_argument("output_dir", help="Directory to save the generated video")
    parser.add_argument("--prompt", default="男人正在说话", help="Prompt for the digital human")
    parser.add_argument("--vram-swap-coef", type=float, default=40, help="显存交换系数") # 测试40最快1h2min，20慢1h5min，10慢1h51min
    parser.add_argument("--url", default="http://localhost:7860", help="URL of the InfiniteTalk service")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Audio to Video Generation")
    logger.info("=" * 60)
    
    success = audio_to_video(args.audio_file, args.image_file, args.output_dir, args.prompt, args.url, args.vram_swap_coef)
        
    logger.info("=" * 60)
    if success:
        logger.info("✓✓✓ SUCCESS! Video generation complete ✓✓✓")
        sys.exit(0)
    else:
        logger.error("✗✗✗ FAILED! Video generation failed ✗✗✗")
        sys.exit(1)
