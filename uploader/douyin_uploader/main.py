# -*- coding: utf-8 -*-
from datetime import datetime

from playwright.async_api import Playwright, async_playwright, Page
import os
import asyncio

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import douyin_logger
from utils.video_utils import extract_video_frame


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def douyin_setup(account_file, handle=False):
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        douyin_logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await douyin_cookie_gen(account_file)
    return True


async def douyin_cookie_gen(account_file):
    async with async_playwright() as playwright:
        options = {
            'headless': LOCAL_CHROME_HEADLESS
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class DouYinVideo(object):
    def __init__(self, title, file_path, tags, publish_date: datetime, account_file, thumbnail_path=None, productLink='', productTitle=''):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.thumbnail_path = thumbnail_path
        self.productLink = productLink
        self.productTitle = productTitle

    async def set_schedule_time_douyin(self, page, publish_date):
        # 选择包含特定文本内容的 label 元素
        label_element = page.locator("[class^='radio']:has-text('定时发布')")
        # 在选中的 label 元素下点击 checkbox
        await label_element.click()
        await asyncio.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")

        await asyncio.sleep(1)
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_hour))
        await page.keyboard.press("Enter")

        await asyncio.sleep(1)

    async def handle_upload_error(self, page):
        douyin_logger.info('视频出错了，重新上传中')
        await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        # 使用 Chromium 浏览器启动一个浏览器实例
        if self.local_executable_path:
            browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=self.headless)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        douyin_logger.info(f'[+]正在上传-------{self.title}.mp4')
        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        douyin_logger.info(f'[-] 正在打开主页...')
        
        # 处理可能出现的位置权限弹窗
        try:
            await asyncio.sleep(2)  # 等待弹窗出现
            # 尝试多种方式查找并点击"一律不允许"按钮
            deny_button = page.locator("button:has-text('一律不允许')")
            if await deny_button.count() > 0:
                await deny_button.first.click()
                douyin_logger.info("  [-] 已关闭位置权限弹窗")
                await asyncio.sleep(1)
            else:
                douyin_logger.debug("  [-] 未检测到位置权限弹窗")
        except Exception as e:
            douyin_logger.debug(f"  [-] 位置权限弹窗处理异常: {e}")
        
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload")
        # 点击 "上传视频" 按钮
        await page.locator("div[class^='container'] input").set_input_files(self.file_path)

        # 等待页面跳转到指定的 URL 2025.01.08修改在原有基础上兼容两种页面
        while True:
            try:
                # 尝试等待第一个 URL
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page", timeout=3000)
                douyin_logger.info("[+] 成功进入version_1发布页面!")
                break  # 成功进入页面后跳出循环
            except Exception:
                try:
                    # 如果第一个 URL 超时，再尝试等待第二个 URL
                    await page.wait_for_url(
                        "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page",
                        timeout=3000)
                    douyin_logger.info("[+] 成功进入version_2发布页面!")

                    break  # 成功进入页面后跳出循环
                except:
                    print("  [-] 超时未进入视频发布页面，重新尝试...")
                    await asyncio.sleep(0.5)  # 等待 0.5 秒后重新尝试
        
        # 处理可能出现的新功能通知弹窗
        try:
            await asyncio.sleep(1)  # 等待弹窗出现
            # 查找"我知道了"按钮并点击
            know_button = page.locator("button:has-text('我知道了')")
            if await know_button.count() > 0 and await know_button.is_visible():
                await know_button.click()
                douyin_logger.debug("  [-] 已关闭新功能通知弹窗")
                await asyncio.sleep(0.5)
        except Exception as e:
            douyin_logger.debug(f"  [-] 未检测到新功能通知弹窗")
        
        # 填充标题和话题
        # 检查是否存在包含输入框的元素
        # 这里为了避免页面变化，故使用相对位置定位：作品标题父级右侧第一个元素的input子元素
        await asyncio.sleep(1)
        douyin_logger.info(f'  [-] 正在填充标题和话题...')
        
        # 方式1: 尝试通过"作品标题"文本定位
        title_container = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
        
        # 方式2: 如果找不到"作品标题"，尝试通过"作品描述"文本定位
        if await title_container.count() == 0:
            douyin_logger.info(f'  [-] 未找到"作品标题"，尝试通过"作品描述"定位...')
            title_container = page.get_by_text('作品描述').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
        
        # 方式3: 如果还是找不到，尝试通过 placeholder 文本定位
        if await title_container.count() == 0:
            douyin_logger.info(f'  [-] 尝试通过 placeholder 定位标题输入框...')
            title_container = page.locator('input[placeholder*="填写作品标题"]')
        
        # 填写标题
        if await title_container.count():
            await title_container.fill(self.title[:30])
            douyin_logger.info(f'  [-] 已填写标题: {self.title[:30]}')
        else:
            # 备用方案：使用 .notranslate 类定位
            douyin_logger.info(f'  [-] 使用备用方案定位标题输入框...')
            titlecontainer = page.locator(".notranslate")
            await titlecontainer.click()
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            await page.keyboard.type(self.title)
            await page.keyboard.press("Enter")
            douyin_logger.info(f'  [-] 已填写标题（备用方案）: {self.title}')
        
        css_selector = ".zone-container"
        for index, tag in enumerate(self.tags, start=1):
            await page.type(css_selector, "#" + tag)
            await page.press(css_selector, "Space")
        douyin_logger.info(f'总共添加{len(self.tags)}个话题')
        while True:
            # 判断重新上传按钮是否存在，如果不存在，代表视频正在上传，则等待
            try:
                #  新版：定位重新上传
                number = await page.locator('[class^="long-card"] div:has-text("重新上传")').count()
                if number > 0:
                    douyin_logger.success("  [-]视频上传完毕")
                    break
                else:
                    douyin_logger.info("  [-] 正在上传视频中...")
                    await asyncio.sleep(2)

                    if await page.locator('div.progress-div > div:has-text("上传失败")').count():
                        douyin_logger.error("  [-] 发现上传出错了... 准备重试")
                        await self.handle_upload_error(page)
            except:
                douyin_logger.info("  [-] 正在上传视频中...")
                await asyncio.sleep(2)

        if self.productLink and self.productTitle:
            douyin_logger.info(f'  [-] 正在设置商品链接...')
            await self.set_product_link(page, self.productLink, self.productTitle)
            douyin_logger.info(f'  [+] 完成设置商品链接...')
        
        #上传视频封面
        await self.set_thumbnail(page, self.thumbnail_path)

        # 更换可见元素
        await self.set_location(page, "")


        # 頭條/西瓜
        third_part_element = '[class^="info"] > [class^="first-part"] div div.semi-switch'
        # 定位是否有第三方平台
        if await page.locator(third_part_element).count():
            # 检测是否是已选中状态
            if 'semi-switch-checked' not in await page.eval_on_selector(third_part_element, 'div => div.className'):
                await page.locator(third_part_element).locator('input.semi-switch-native-control').click()

        if self.publish_date != 0:
            await self.set_schedule_time_douyin(page, self.publish_date)

        # 判断视频是否发布成功
        max_retries = 10
        retry_count = 0
        cover_handled = False  # 标记封面是否已处理
        
        while retry_count < max_retries:
            # 判断视频是否发布成功
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.click()
                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/manage**",
                                        timeout=3000)  # 如果自动跳转到作品页面，则代表发布成功
                douyin_logger.success("  [-]视频发布成功")
                break
            except:
                retry_count += 1
                douyin_logger.info(f"  [-] 视频正在发布中... (尝试 {retry_count}/{max_retries})")
                
                # 只在前几次尝试处理封面问题
                if not cover_handled and retry_count <= 3:
                    cover_result = await self.handle_auto_video_cover(page)
                    if cover_result:
                        cover_handled = True
                        douyin_logger.success("  [+] 封面已成功设置")
                
                await page.screenshot(full_page=True)
                await asyncio.sleep(0.5)
                
                if retry_count >= max_retries:
                    douyin_logger.error(f"  [-] 发布失败，已达到最大重试次数 {max_retries}")
                    raise Exception(f"视频发布失败，重试{max_retries}次后仍未成功")

        await context.storage_state(path=self.account_file)  # 保存cookie
        douyin_logger.success('  [-]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()

    async def handle_auto_video_cover(self, page):
        """
        处理必须设置封面的情况，从视频提取封面并上传
        """
        # 1. 判断是否出现 "请设置封面后再发布" 的提示
        # 必须确保提示是可见的 (is_visible)，因为 DOM 中可能存在隐藏的历史提示
        if await page.get_by_text("请设置封面后再发布").first.is_visible():
            douyin_logger.info("  [-] 检测到需要设置封面提示，将从视频提取封面...")

            try:
                # 从视频中提取封面
                cover_path = extract_video_frame(self.file_path, time="00:00:01")
                douyin_logger.info(f"  [-] 封面提取成功: {cover_path}")
                
                # 上传封面
                await self.set_thumbnail(page, cover_path)
                douyin_logger.success("  [+] 封面上传成功")
                
                # 清理临时封面文件
                try:
                    if os.path.exists(cover_path):
                        os.remove(cover_path)
                        douyin_logger.debug(f"  [-] 已清理临时封面文件: {cover_path}")
                except Exception as e:
                    douyin_logger.warning(f"  [-] 清理临时文件失败: {e}")
                
                return True
            except Exception as e:
                douyin_logger.error(f"  [-] 提取并上传封面失败: {e}")
                # 如果提取失败，尝试原来的方法：点击推荐封面
                douyin_logger.info("  [-] 尝试使用备用方案：点击推荐封面...")
                
                recommend_cover = page.locator('[class^="recommendCover-"]').first
                if await recommend_cover.count():
                    print("  [-] 正在选择第一个推荐封面...")
                    try:
                        await recommend_cover.click()
                        await asyncio.sleep(1)  # 等待选中生效

                        # 3. 处理可能的确认弹窗 "是否确认应用此封面？"
                        # 并不一定每次都会出现，健壮性判断：如果出现弹窗，则点击确定
                        confirm_text = "是否确认应用此封面？"
                        if await page.get_by_text(confirm_text).first.is_visible():
                            print(f"  [-] 检测到确认弹窗: {confirm_text}")
                            # 直接点击"确定"按钮，不依赖脆弱的 CSS 类名
                            await page.get_by_role("button", name="确定").click()
                            print("  [-] 已点击确认应用封面")
                            await asyncio.sleep(1)

                        print("  [-] 已完成封面选择流程")
                        return True
                    except Exception as e:
                        print(f"  [-] 选择封面失败: {e}")

        return False

    async def set_thumbnail(self, page: Page, thumbnail_path: str):
        if thumbnail_path:
            douyin_logger.info('  [-] 正在设置视频封面...')
            
            # 在点击封面按钮前，再次检查并关闭位置权限弹窗
            try:
                await asyncio.sleep(0.5)
                deny_button = page.locator("button:has-text('一律不允许'):visible")
                if await deny_button.count() > 0:
                    await deny_button.first.click()
                    douyin_logger.info("  [-] 已关闭位置权限弹窗（封面设置前）")
                    await asyncio.sleep(1)
            except:
                pass
            
            await page.click('text="选择封面"')
            await page.wait_for_selector("div.dy-creator-content-modal", timeout=5000)
            douyin_logger.debug('  [-] 封面设置对话框已打开')
            
            # 点击顶部的"设置竖封面"标签（作为tab切换）
            await page.wait_for_timeout(1000)
            try:
                # 尝试通过文本查找并点击"设置竖封面"标签
                vertical_cover_tab = page.locator('text="设置竖封面"').first
                if await vertical_cover_tab.is_visible():
                    await vertical_cover_tab.click()
                    douyin_logger.debug('  [-] 已切换到"设置竖封面"标签')
            except:
                douyin_logger.debug('  [-] 默认已在竖封面标签')
            
            await page.wait_for_timeout(1000)
            
            # 定位到上传区域并上传文件
            await page.locator("div[class^='semi-upload upload'] >> input.semi-upload-hidden-input").set_input_files(thumbnail_path)
            douyin_logger.debug(f'  [-] 已选择封面文件: {thumbnail_path}')
            
            # 等待图片上传和处理完成，确保"完成"按钮变为可用状态
            douyin_logger.debug('  [-] 等待封面图片处理完成...')
            try:
                # 等待"完成"按钮从disabled变为enabled（最多等待10秒）
                complete_btn = page.locator("button:has-text('完成'):visible")
                await complete_btn.first.wait_for(state="visible", timeout=10000)
                # 额外等待确保按钮可点击
                await page.wait_for_timeout(2000)
                douyin_logger.debug('  [-] 封面处理完成，按钮已就绪')
            except:
                douyin_logger.warning('  [-] 等待"完成"按钮超时，继续尝试点击')
                await page.wait_for_timeout(2000)
            
            # 点击"完成"按钮关闭封面编辑器（可能需要点击多次）
            try:
                # 第1次点击：关闭封面裁剪/编辑界面
                douyin_logger.debug('  [-] 尝试关闭封面编辑界面...')
                
                # 在弹窗内查找所有可见的"完成"按钮
                complete_buttons = page.locator("button:has-text('完成'):visible:not([disabled])")
                button_count = await complete_buttons.count()
                douyin_logger.debug(f'  [-] 找到 {button_count} 个可用的"完成"按钮')
                
                if button_count > 0:
                    # 第一次点击 - 通常是编辑界面的完成
                    await complete_buttons.first.click()
                    douyin_logger.success('  [-] 第1次点击"完成"按钮（关闭编辑界面）')
                    
                    # 关键：第一次点击后必定会弹出"设置横封面获更多流量"对话框
                    # 需要等待该对话框出现并处理
                    await page.wait_for_timeout(800)
                    douyin_logger.debug('  [-] 等待横封面推荐弹窗出现...')
                    
                    # 等待并处理横封面推荐弹窗（最常见的情况）
                    try:
                        # 使用更精确的定位器，等待弹窗出现
                        await page.wait_for_selector("button:has-text('暂不设置')", state="visible", timeout=3000)
                        
                        skip_horizontal_btn = page.locator("button:has-text('暂不设置'):visible")
                        skip_count = await skip_horizontal_btn.count()
                        douyin_logger.debug(f'  [-] 找到 {skip_count} 个"暂不设置"按钮')
                        
                        if skip_count > 0:
                            await skip_horizontal_btn.first.click()
                            douyin_logger.success("  [-] ✓ 已点击'暂不设置'关闭横封面推荐弹窗")
                            await page.wait_for_timeout(1000)
                        
                    except Exception as e:
                        douyin_logger.warning(f"  [-] 等待横封面弹窗超时，尝试其他方式: {e}")
                        
                        # 备用方案：直接查找并点击
                        try:
                            skip_btn2 = page.locator("button:has-text('暂不设置'):visible")
                            if await skip_btn2.count() > 0:
                                await skip_btn2.first.click()
                                douyin_logger.info("  [-] ✓ 备用方案：已点击'暂不设置'")
                                await page.wait_for_timeout(1000)
                        except:
                            pass
                    
                    # 额外检查位置权限弹窗
                    try:
                        deny_btn = page.locator("button:has-text('一律不允许'):visible")
                        if await deny_btn.count() > 0:
                            await deny_btn.first.click()
                            douyin_logger.info("  [-] ✓ 已关闭位置权限弹窗")
                            await page.wait_for_timeout(500)
                    except:
                        pass
                    
                    # 现在应该没有弹窗了，检查是否还有第二个"完成"按钮
                    await page.wait_for_timeout(500)
                    complete_buttons2 = page.locator("button:has-text('完成'):visible:not([disabled])")
                    button_count2 = await complete_buttons2.count()
                    douyin_logger.debug(f'  [-] 检查是否有第二个"完成"按钮: 找到 {button_count2} 个')
                    
                    if button_count2 > 0:
                        # 有第二个完成按钮，说明还需要确认
                        await complete_buttons2.first.click()
                        douyin_logger.success('  [-] 第2次点击"完成"按钮（最终确认）')
                        await page.wait_for_timeout(1000)
                    else:
                        douyin_logger.info('  [-] 没有第二个"完成"按钮，封面设置已完成')
                    
                    douyin_logger.success('  [+] 封面设置流程完成')
                else:
                    # 如果没找到"完成"，尝试找"设置竖封面"按钮
                    set_cover_btn = page.locator("button:has-text('设置竖封面'):visible")
                    if await set_cover_btn.count() > 0:
                        await set_cover_btn.first.click()
                        douyin_logger.debug('  [-] 点击"设置竖封面"按钮')
                        await page.wait_for_timeout(1500)
                    else:
                        douyin_logger.warning('  [-] 未找到任何确认按钮')
                    
            except Exception as e:
                douyin_logger.error(f'  [-] 点击确认按钮过程出错: {e}')
                
            douyin_logger.info('  [+] 视频封面设置完成！')
            
            # 等待封面设置对话框关闭
            try:
                # 等待整个模态对话框消失
                await page.wait_for_selector("div.dy-creator-content-modal", state='detached', timeout=5000)
                douyin_logger.debug('  [-] 封面对话框已关闭')
            except:
                douyin_logger.warning('  [-] 封面对话框关闭超时，尝试多种方式强制关闭')
                closed = False
                
                # 方法1：点击X关闭按钮
                try:
                    close_btn = page.locator("div.dy-creator-content-modal button[aria-label='关闭']")
                    if await close_btn.count() > 0:
                        await close_btn.click()
                        await page.wait_for_timeout(1000)
                        closed = True
                        douyin_logger.debug('  [-] 已通过关闭按钮关闭对话框')
                except:
                    pass
                
                # 方法2：按ESC键
                if not closed:
                    try:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(1000)
                        douyin_logger.debug('  [-] 已通过ESC键关闭对话框')
                        closed = True
                    except:
                        pass
                
                # 方法3：点击对话框外的遮罩层
                if not closed:
                    try:
                        mask = page.locator("div.dy-creator-content-modal-wrap")
                        if await mask.count() > 0:
                            # 点击遮罩层边缘（不在对话框内容区域）
                            await mask.click(position={"x": 10, "y": 10})
                            await page.wait_for_timeout(1000)
                            douyin_logger.debug('  [-] 已通过点击遮罩层关闭对话框')
                    except:
                        pass
            
            # 处理"设置横封面获更多流量"弹窗
            try:
                await asyncio.sleep(1)
                # 查找"暂不设置"按钮
                skip_horizontal_cover_btn = page.locator("button:has-text('暂不设置'):visible")
                if await skip_horizontal_cover_btn.count() > 0:
                    await skip_horizontal_cover_btn.first.click()
                    douyin_logger.info("  [-] 已关闭横封面推荐弹窗（点击'暂不设置'）")
                    await asyncio.sleep(1)
            except Exception as e:
                douyin_logger.debug(f"  [-] 未检测到横封面推荐弹窗: {e}")
            
            # 额外检查：确保封面编辑工具界面也关闭了
            await page.wait_for_timeout(1000)
            try:
                # 查找并关闭可能存在的封面编辑工具界面
                portal = page.locator("div.dy-creator-content-portal")
                if await portal.count() > 0 and await portal.is_visible():
                    douyin_logger.debug('  [-] 检测到封面编辑界面仍存在，尝试关闭...')
                    # 多次按ESC确保所有弹窗都关闭
                    for i in range(3):
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)
                    douyin_logger.debug('  [-] 已关闭封面编辑界面')
            except:
                pass
            

    async def set_location(self, page: Page, location: str = ""):
        if not location:
            return
        # todo supoort location later
        # await page.get_by_text('添加标签').locator("..").locator("..").locator("xpath=following-sibling::div").locator(
        #     "div.semi-select-single").nth(0).click()
        await page.locator('div.semi-select span:has-text("输入地理位置")').click()
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(2000)
        await page.keyboard.type(location)
        await page.wait_for_selector('div[role="listbox"] [role="option"]', timeout=5000)
        await page.locator('div[role="listbox"] [role="option"]').first.click()

    async def handle_product_dialog(self, page: Page, product_title: str):
        """处理商品编辑弹窗"""

        await page.wait_for_timeout(2000)
        await page.wait_for_selector('input[placeholder="请输入商品短标题"]', timeout=10000)
        short_title_input = page.locator('input[placeholder="请输入商品短标题"]')
        if not await short_title_input.count():
            douyin_logger.error("[-] 未找到商品短标题输入框")
            return False
        product_title = product_title[:10]
        await short_title_input.fill(product_title)
        # 等待一下让界面响应
        await page.wait_for_timeout(1000)

        finish_button = page.locator('button:has-text("完成编辑")')
        if 'disabled' not in await finish_button.get_attribute('class'):
            await finish_button.click()
            douyin_logger.debug("[+] 成功点击'完成编辑'按钮")
            
            # 等待对话框关闭
            await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
            return True
        else:
            douyin_logger.error("[-] '完成编辑'按钮处于禁用状态，尝试直接关闭对话框")
            # 如果按钮禁用，尝试点击取消或关闭按钮
            cancel_button = page.locator('button:has-text("取消")')
            if await cancel_button.count():
                await cancel_button.click()
            else:
                # 点击右上角的关闭按钮
                close_button = page.locator('.semi-modal-close')
                await close_button.click()
            
            await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
            return False
        
    async def set_product_link(self, page: Page, product_link: str, product_title: str):
        """设置商品链接功能"""
        await page.wait_for_timeout(2000)  # 等待2秒
        try:
            # 定位"添加标签"文本，然后向上导航到容器，再找到下拉框
            await page.wait_for_selector('text=添加标签', timeout=10000)
            dropdown = page.get_by_text('添加标签').locator("..").locator("..").locator("..").locator(".semi-select").first
            if not await dropdown.count():
                douyin_logger.error("[-] 未找到标签下拉框")
                return False
            douyin_logger.debug("[-] 找到标签下拉框，准备选择'购物车'")
            await dropdown.click()
            ## 等待下拉选项出现
            await page.wait_for_selector('[role="listbox"]', timeout=5000)
            ## 选择"购物车"选项
            await page.locator('[role="option"]:has-text("购物车")').click()
            douyin_logger.debug("[+] 成功选择'购物车'")
            
            # 输入商品链接
            ## 等待商品链接输入框出现
            await page.wait_for_selector('input[placeholder="粘贴商品链接"]', timeout=5000)
            # 输入
            input_field = page.locator('input[placeholder="粘贴商品链接"]')
            await input_field.fill(product_link)
            douyin_logger.debug(f"[+] 已输入商品链接: {product_link}")
            
            # 点击"添加链接"按钮
            add_button = page.locator('span:has-text("添加链接")')
            ## 检查按钮是否可用（没有disable类）
            button_class = await add_button.get_attribute('class')
            if 'disable' in button_class:
                douyin_logger.error("[-] '添加链接'按钮不可用")
                return False
            await add_button.click()
            douyin_logger.debug("[+] 成功点击'添加链接'按钮")
            ## 如果链接不可用
            await page.wait_for_timeout(2000)
            error_modal = page.locator('text=未搜索到对应商品')
            if await error_modal.count():
                confirm_button = page.locator('button:has-text("确定")')
                await confirm_button.click()
                # await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
                douyin_logger.error("[-] 商品链接无效")
                return False

            # 填写商品短标题
            if not await self.handle_product_dialog(page, product_title):
                return False
            
            # 等待链接添加完成
            douyin_logger.debug("[+] 成功设置商品链接")
            return True
        except Exception as e:
            douyin_logger.error(f"[-] 设置商品链接时出错: {str(e)}")
            return False

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)


