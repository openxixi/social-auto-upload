import os
import time
import argparse
from playwright.sync_api import sync_playwright

def automate_tts(text_file_path, audio_file_path, output_dir, url="http://localhost:7866"):
    # Read text from file
    with open(text_file_path, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(url)
        
        # Wait for page to load
        page.wait_for_load_state('networkidle')
        
        # Find and fill text input
        textarea = page.wait_for_selector("textarea")
        textarea.fill(text)
        
        # Find and upload audio file
        # First click the upload button to open file chooser
        upload_button = page.locator("button").nth(3)  # '将音频拖放到此处' button
        with page.expect_file_chooser() as fc_info:
            upload_button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(os.path.abspath(audio_file_path))
        print("\r\n")
        print(audio_file_path)
        print("before audio file")
        print(os.path.abspath(audio_file_path))
        time.sleep(5)  # Wait for upload to complete
        print("after audio file")
        # Debug: print all buttons
        buttons = page.locator("button")
        print("All buttons found:")
        for i in range(buttons.count()):
            print(f"Button {i}: '{buttons.nth(i).inner_text()}'")
        
        # Click generate button
        generate_buttons = page.locator("button:has-text('音频生成')")
        generate_buttons.nth(1).click()  # Click the second one
        
        # Wait for generation (adjust time as needed)
        page.wait_for_timeout(10000)  # 10 seconds
        
        # Debug: print all buttons after generation
        buttons = page.locator("button")
        print("All buttons after generation:")
        for i in range(buttons.count()):
            print(f"Button {i}: '{buttons.nth(i).inner_text()}'")
        
        # Debug: print all links
        links = page.locator("a")
        print("All links:")
        for i in range(links.count()):
            print(f"Link {i}: '{links.nth(i).inner_text()}' href='{links.nth(i).get_attribute('href')}'")
        
        # Debug: print all audio elements
        audios = page.locator("audio")
        print("All audio elements:")
        for i in range(audios.count()):
            src = audios.nth(i).get_attribute('src')
            print(f"Audio {i}: src='{src}'")
        
        # If there is an audio, perhaps download the src
        if audios.count() > 0:
            src = audios.nth(0).get_attribute('src')
            if src:
                # Download the audio file
                response = page.request.get(src)
                with open(os.path.join(output_dir, "generated_audio.wav"), "wb") as f:
                    f.write(response.body())
                print(f"Downloaded audio to {os.path.join(output_dir, 'generated_audio.wav')}")
                browser.close()
                print("Automation completed")
                return
        
        # Click generate button (start recording)
        generate_button = page.locator("button:has-text('生成语音')").first
        generate_button.click()
        
        # Wait for recording
        page.wait_for_timeout(10000)  # Adjust time for recording length
        
        # Click again to stop
        generate_button.click()
        
        # Wait for processing
        page.wait_for_timeout(5000)
        
        # Debug: print all audio elements
        audios = page.locator("audio")
        print("All audio elements after stop:")
        for i in range(audios.count()):
            src = audios.nth(i).get_attribute('src')
            print(f"Audio {i}: src='{src}'")
        
        # If there is an audio, download
        if audios.count() > 0:
            src = audios.nth(0).get_attribute('src')
            if src and src.startswith('blob:'):
                # For blob, perhaps find download button near it
                print("Blob URL, looking for download button")
                download_btns = page.locator("button:has-text('下载')")
                if download_btns.count() > 0:
                    download_btns.first.click()
                    # Wait for download
                    page.wait_for_timeout(5000)
                    print("Download clicked")
                else:
                    print("No download button found")
            elif src.startswith('http'):
                response = page.request.get(src)
                with open(os.path.join(output_dir, "generated_audio.wav"), "wb") as f:
                    f.write(response.body())
                print(f"Downloaded audio to {os.path.join(output_dir, 'generated_audio.wav')}")
        
        browser.close()
        print("Automation completed")
        
        browser.close()
        print("Automation completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate TTS generation on localhost:7866")
    parser.add_argument("text_file", help="Path to the text file")
    parser.add_argument("audio_file", help="Path to the reference audio file")
    parser.add_argument("output_dir", help="Directory to save downloaded TTS")
    parser.add_argument("--url", default="http://localhost:7866", help="URL of the Gradio interface")
    
    args = parser.parse_args()
    
    automate_tts(args.text_file, args.audio_file, args.output_dir, args.url)