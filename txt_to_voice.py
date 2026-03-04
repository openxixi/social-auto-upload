import os
import time
import argparse
import sys
from datetime import datetime
import wave
from playwright.sync_api import sync_playwright

def automate_tts(text_file_path, audio_file_path, output_dir, url="http://localhost:7866"):
    def get_wav_duration_seconds(file_path):
        try:
            with wave.open(file_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate) if rate else None
        except Exception:
            return None
    def download_blob_audio(page, blob_url, output_path):
        data = page.evaluate(
            """
            async (blobUrl) => {
                const response = await fetch(blobUrl);
                const blob = await response.blob();
                const buffer = await blob.arrayBuffer();
                return Array.from(new Uint8Array(buffer));
            }
            """,
            blob_url,
        )
        if data:
            with open(output_path, "wb") as f:
                f.write(bytes(data))
            return True
        return False

    def download_from_link(page, output_path):
        link = page.locator("a[href*='/gradio_api/file=']").first
        if link.count() == 0:
            return False
        href = link.get_attribute("href")
        if not href:
            return False
        response = page.request.get(href)
        with open(output_path, "wb") as f:
            f.write(response.body())
        return True
    # Preflight checks
    if not os.path.exists(text_file_path):
        print(f"✗ Error: Text file not found at {os.path.abspath(text_file_path)}")
        return
    if not os.path.exists(audio_file_path):
        print(f"✗ Error: Audio file not found at {os.path.abspath(audio_file_path)}")
        return
    os.makedirs(output_dir, exist_ok=True)

    # Generate output filename from text file
    text_basename = os.path.splitext(os.path.basename(text_file_path))[0]
    output_filename = f"{text_basename}.wav"
    print(f"✓ Will save audio as: {output_filename}")

    # Read text from file
    with open(text_file_path, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        print(f"✗ Error: Text file is empty: {os.path.abspath(text_file_path)}")
        return
    
    overall_start = datetime.now()
    gen_start = None
    gen_end = None

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=False)  # Set to True for headless
            except Exception as e:
                msg = str(e)
                if "Executable doesn't exist" in msg:
                    print("✗ Playwright Chromium 未安装，尝试使用本机 Chrome 作为兜底...")
                    try:
                        browser = p.chromium.launch(channel="chrome", headless=False)
                    except Exception as e2:
                        print("✗ 启动浏览器失败。请先安装 Playwright 浏览器：")
                        print("  python -m playwright install")
                        print(f"  详细错误: {e2}")
                        return
                else:
                    print(f"✗ 启动浏览器失败: {e}")
                    return

            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.goto(url)

            # Wait for page to load
            page.wait_for_load_state('networkidle')

            # Find and fill text input
            textarea = page.wait_for_selector("textarea")
            textarea.fill(text)

            # Find and upload audio file
            audio_input = page.locator("#component-4 input[type='file']")
            if audio_input.count() > 0:
                audio_input.set_input_files(os.path.abspath(audio_file_path))
            else:
                # Fallback: try file chooser by clicking upload button
                upload_button = page.locator("#component-4 button[aria-label='Upload file']")
                if upload_button.count() == 0:
                    upload_button = page.locator("#component-4 button:has(svg)").first
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
            generate_button = page.locator("button:has-text('生成语音')").first
            if not generate_button.is_enabled():
                print("⚠ 生成语音按钮不可用，可能上传尚未完成")
            gen_start = datetime.now()
            print(f"生成开始时间: {gen_start.strftime('%Y-%m-%d %H:%M:%S')}")
            generate_button.click(force=True)

            # Wait for output audio or download link to appear with progress
            max_wait_sec = 600
            max_cycles = 3
            cycle = 0
            start_time = time.time()
            spinner = "|/-\\"
            ready_src = None
            ready_link = None
            while True:
                elapsed = time.time() - start_time
                spin = spinner[int(elapsed) % len(spinner)]
                sys.stdout.write(f"\r生成中 {spin} 已等待 {int(elapsed)} 秒")
                sys.stdout.flush()

                result = page.evaluate(
                    """
                    () => {
                        const outAudio = document.querySelector('#component-9 audio');
                        const audioSrc = outAudio && outAudio.src ? outAudio.src : null;
                        const linkEl = document.querySelector("a[href*='/gradio_api/file=']");
                        const linkHref = linkEl ? linkEl.getAttribute('href') : null;
                        return { audioSrc, linkHref };
                    }
                    """
                )
                if result:
                    ready_src = result.get("audioSrc")
                    ready_link = result.get("linkHref")
                if ready_src or ready_link:
                    sys.stdout.write("\n")
                    break
                if elapsed >= max_wait_sec:
                    cycle += 1
                    sys.stdout.write("\n")
                    if cycle < max_cycles:
                        print(f"⚠ 仍在生成中，继续等待（第 {cycle + 1}/{max_cycles} 轮）")
                        start_time = time.time()
                    else:
                        print("⚠ 等待超时，继续尝试下载或保存诊断信息")
                        break
                page.wait_for_timeout(1000)

            gen_end = datetime.now()
            print(f"生成结束时间: {gen_end.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"生成耗时: {gen_end - gen_start}")

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
            audios = page.locator("#component-9 audio")
            print("Output audio elements:")
            for i in range(audios.count()):
                src = audios.nth(i).get_attribute('src')
                print(f"Output audio {i}: src='{src}'")

            # If there is an audio or link, download
            output_path = os.path.join(output_dir, output_filename)
            print(f"\n准备下载音频到: {output_path}")
            src = ready_src
            if not src and audios.count() > 0:
                for i in range(audios.count()):
                    s = audios.nth(i).get_attribute('src')
                    if s:
                        src = s
                        break
            if src:
                if src.startswith("blob:"):
                    if download_blob_audio(page, src, output_path):
                        file_size = os.path.getsize(output_path)
                        duration = get_wav_duration_seconds(output_path)
                        print(f"Downloaded audio to {output_path}")
                        print(f"音频大小: {file_size} bytes")
                        if duration is not None:
                            print(f"音频时长: {duration:.2f} 秒")
                        browser.close()
                        print("Automation completed")
                        return
                elif src.startswith("http"):
                    response = page.request.get(src)
                    with open(output_path, "wb") as f:
                        f.write(response.body())
                    file_size = os.path.getsize(output_path)
                    duration = get_wav_duration_seconds(output_path)
                    print(f"Downloaded audio to {output_path}")
                    print(f"音频大小: {file_size} bytes")
                    if duration is not None:
                        print(f"音频时长: {duration:.2f} 秒")
                    browser.close()
                    print("Automation completed")
                    return
            # Fallback: try link download
            if ready_link or download_from_link(page, output_path):
                if ready_link:
                    response = page.request.get(ready_link)
                    with open(output_path, "wb") as f:
                        f.write(response.body())
                file_size = os.path.getsize(output_path)
                duration = get_wav_duration_seconds(output_path)
                print(f"Downloaded audio to {output_path}")
                print(f"音频大小: {file_size} bytes")
                if duration is not None:
                    print(f"音频时长: {duration:.2f} 秒")
                browser.close()
                print("Automation completed")
                return

            # Save diagnostics if audio src is empty
            diag_html = os.path.join(output_dir, "debug_page.html")
            with open(diag_html, "w", encoding="utf-8") as f:
                f.write(page.content())
            diag_png = os.path.join(output_dir, "debug_page.png")
            page.screenshot(path=diag_png, full_page=True)
            print(f"⚠ 未检测到音频或下载链接，已保存诊断文件：{diag_html} 和 {diag_png}")

            browser.close()
            print("Automation completed")
    finally:
        overall_end = datetime.now()
        print(f"总开始时间: {overall_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总结束时间: {overall_end.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {overall_end - overall_start}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate TTS generation on localhost:7866")
    parser.add_argument("text_file", help="Path to the text file")
    parser.add_argument("audio_file", help="Path to the reference audio file")
    parser.add_argument("output_dir", help="Directory to save downloaded TTS")
    parser.add_argument("--url", default="http://localhost:7866", help="URL of the Gradio interface")
    
    args = parser.parse_args()
    
    automate_tts(args.text_file, args.audio_file, args.output_dir, args.url)