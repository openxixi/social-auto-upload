#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量删除抖音审核不通过的视频
"""

import os
import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# 设置标准输出编码为 UTF-8，解决 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from conf import BASE_DIR, LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script


async def delete_rejected_videos(account_file, dry_run=False, debug=False):
    """
    删除审核不通过的视频
    
    Args:
        account_file: 账号cookie文件路径
        dry_run: 是否为演练模式（只查看不删除）
        debug: 是否启用调试模式（保存页面截图和HTML）
    """
    browser = None
    context = None
    page = None
    
    try:
        async with async_playwright() as playwright:
            # 启动浏览器
            if LOCAL_CHROME_PATH and os.path.exists(LOCAL_CHROME_PATH):
                browser = await playwright.chromium.launch(
                    headless=LOCAL_CHROME_HEADLESS,
                    executable_path=LOCAL_CHROME_PATH
                )
            else:
                browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
            
            # 加载cookie
            if not os.path.exists(account_file):
                print(f"❌ Cookie文件不存在: {account_file}")
                print("请先运行登录脚本生成cookie")
                return
            
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            page = await context.new_page()
            
            print("\n" + "=" * 60)
            print("批量删除抖音审核不通过视频")
            print("=" * 60)
            
            # 1. 访问内容管理页面
            print("\n1. 访问内容管理页面...")
            await page.goto("https://creator.douyin.com/creator-micro/content/manage")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            if debug:
                await page.screenshot(path="debug_step1_page_loaded.png")
                print("  [调试] 已保存截图: debug_step1_page_loaded.png")
            
            # 检查是否需要登录
            if "login" in page.url.lower() or await page.get_by_text('扫码登录').count() > 0:
                print("❌ Cookie已失效，需要重新登录")
                return
            
            print("✓ 登录成功")
            print(f"  当前URL: {page.url}")
            
            # 2. 自动点击"未通过"选项卡
            print("\n2. 点击'未通过'选项卡...")
            
            try:
                # 等待页面加载
                await asyncio.sleep(2)
                
                # 查找并点击"未通过"选项卡
                rejected_tab = page.locator('text=未通过').first
                
                if await rejected_tab.count() > 0:
                    await rejected_tab.click()
                    await asyncio.sleep(2)
                    print("✓ 已切换到'未通过'选项卡")
                else:
                    print("⚠ 未找到'未通过'选项卡")
                    print("  尝试查找其他可能的标签...")
                    
                    # 尝试其他可能的文本
                    for text in ['审核不通过', '不通过', '未通过']:
                        tab = page.locator(f'text={text}').first
                        if await tab.count() > 0:
                            await tab.click()
                            await asyncio.sleep(2)
                            print(f"✓ 已切换到'{text}'选项卡")
                            break
                    else:
                        print("⚠ 未能自动切换，请确保已在正确的选项卡")
                        
            except Exception as e:
                print(f"⚠ 切换选项卡时出错: {e}")
            
            # 等待视频列表加载
            await asyncio.sleep(2)
            
            if debug:
                await page.screenshot(path="debug_step2_after_filter.png")
                print("  [调试] 已保存截图: debug_step2_after_filter.png")
            
            # 3. 获取所有视频项
            print("\n3. 正在查找视频...")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
            
            # 等待视频列表加载
            try:
                # 等待视频容器出现
                await page.wait_for_selector('article[class*="item-container"]', timeout=10000)
            except:
                print("  ⚠ 等待视频列表超时")
            
            # 使用抖音创作者中心的实际选择器
            selectors = [
                'article[class*="item-container"]',  # 视频卡片容器
 'div[class*="video-card"]',  # 视频卡片
                'div[class*="content-card"]',  # 内容卡片
            ]
            
            video_items = []
            used_selector = None
            
            for selector in selectors:
                items = await page.locator(selector).all()
                if len(items) > 0:
                    video_items = items
                    used_selector = selector
                    print(f"✓ 使用选择器: {selector}")
                    break
            
            print(f"✓ 找到 {len(video_items)} 个视频项")
            
            if debug and len(video_items) > 0:
                # 保存第一个视频项的HTML
                first_item_html = await video_items[0].inner_html()
                with open("debug_first_item.html", "w", encoding="utf-8") as f:
                    f.write(first_item_html)
                print("  [调试] 已保存第一个视频项HTML: debug_first_item.html")
            
            if len(video_items) == 0:
                print("\n❌ 没有找到视频项")
                print("可能的原因:")
                print("  1. 页面结构已更新，需要调整选择器")
                print("  2. 当前没有审核不通过的视频")
                print("  3. 页面未完全加载")
                
                if debug:
                    page_content = await page.content()
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(page_content)
                    print("\n[调试] 已保存完整页面HTML: debug_page.html")
                    print("请检查该文件，找到视频列表的实际HTML结构")
                
                return
            
            # 4. 删除视频
            deleted_count = 0
            failed_count = 0
            
            print(f"\n4. {'演练模式' if dry_run else '开始删除'}...")
            print("=" * 60)
            
            # 逐个处理视频
            for i in range(len(video_items)):
                try:
                    # 每次删除后重新获取视频列表
                    await asyncio.sleep(1)
                    
                    if used_selector:
                        current_items = await page.locator(used_selector).all()
                    else:
                        current_items = video_items
                    
                    if i >= len(current_items):
                        print(f"\n已处理所有视频")
                        break
                    
                    video_item = current_items[i]
                    
                    # 获取视频标题（用于显示）
                    try:
                        # 视频标题通常在 h4 或特定 class 中
                        title = None
                        title_selectors = [
                            'h4',
                            'div[class*="title"]',
                            'span[class*="title"]',
                        ]
                        
                        for ts in title_selectors:
                            title_elem = video_item.locator(ts).first
                            if await title_elem.count() > 0:
                                title_text = await title_elem.inner_text()
                                if title_text and title_text.strip():
                                    title = title_text.strip()
                                    break
                        
                        if not title:
                            title = f"视频 {i+1}"
                        
                        print(f"\n[{i+1}/{len(current_items)}] {title[:60]}...")
                    except:
                        print(f"\n[{i+1}/{len(current_items)}] 视频 {i+1}")
                    
                    if dry_run:
                        print("  [演练] 将会删除此视频")
                        deleted_count += 1
                        continue
                    
                    # 直接查找"删除作品"按钮（从截图看每个视频项都有这个按钮）
                    delete_btn_direct = video_item.locator('button:has-text("删除作品"), span:has-text("删除作品")').first
                    
                    if await delete_btn_direct.count() > 0:
                        # 直接点击删除按钮
                        await delete_btn_direct.scroll_into_view_if_needed()
                        await delete_btn_direct.click()
                        await asyncio.sleep(0.8)
                        
                        if debug and i == 0:
                            await page.screenshot(path="debug_confirm_dialog.png")
                            print("  [调试] 已保存确认对话框截图: debug_confirm_dialog.png")
                        
                        # 确认删除
                        confirm_selectors = [
                            'button:has-text("确定")',
                            'button:has-text("确认删除")',
                            'button[class*="confirm"]',
                            '.semi-button-primary:has-text("确")',
                        ]
                        
                        confirm_button = None
                        for cs in confirm_selectors:
                            btn = page.locator(cs).last
                            if await btn.count() > 0:
                                confirm_button = btn
                                break
                        
                        if confirm_button and await confirm_button.count() > 0:
                            await confirm_button.click()
                            await asyncio.sleep(1.5)
                            print("  ✓ 删除成功")
                            deleted_count += 1
                            
                            # 删除后等待页面更新
                            await asyncio.sleep(1)
                        else:
                            print("  ⚠ 未找到确认按钮")
                            # 尝试按ESC关闭弹窗
                            await page.keyboard.press('Escape')
                            failed_count += 1
                        
                        continue  # 跳过后面的"更多"按钮逻辑
                    
                    # 如果没有直接的删除按钮，尝试通过"更多"菜单
                    print("  未找到直接删除按钮，尝试更多菜单...")
                    
                    # 查找更多操作按钮（三个点）
                    more_selectors = [
                        'button:has-text("更多")',
                        'button[class*="more"]',
                        '[aria-label*="更多"]',
                        'button svg[class*="more"]',
                        'button:has([class*="icon"])',
                    ]
                    
                    more_button = None
                    for ms in more_selectors:
                        btn = video_item.locator(ms).first
                        if await btn.count() > 0:
                            more_button = btn
                            break
                    
                    if not more_button or await more_button.count() == 0:
                        # 尝试定位所有button，取最后一个（通常是更多按钮）
                        all_buttons = await video_item.locator('button').all()
                        if len(all_buttons) > 0:
                            more_button = all_buttons[-1]
                    
                    if more_button and await more_button.count() > 0:
                        # 点击更多按钮
                        await more_button.scroll_into_view_if_needed()
                        await more_button.click()
                        await asyncio.sleep(0.8)
                        
                        if debug and i == 0:
                            await page.screenshot(path="debug_menu_opened.png")
                            print("  [调试] 已保存菜单截图: debug_menu_opened.png")
                        
                        # 查找删除按钮
                        delete_button = page.locator('text=删除').last
                        
                        if await delete_button.count() > 0:
                            await delete_button.click()
                            await asyncio.sleep(0.8)
                            
                            # 确认删除（通常会有确认弹窗）
                            confirm_selectors = [
                                'button:has-text("确定")',
                                'button:has-text("确认")',
                                'button[class*="confirm"]',
                                'button.semi-button-primary',
                            ]
                            
                            confirm_button = None
                            for cs in confirm_selectors:
                                btn = page.locator(cs).last
                                if await btn.count() > 0:
                                    confirm_button = btn
                                    break
                            
                            if confirm_button and await confirm_button.count() > 0:
                                await confirm_button.click()
                                await asyncio.sleep(1.5)
                                print("  ✓ 删除成功")
                                deleted_count += 1
                                
                                # 删除后需要从头开始遍历（因为索引变了）
                                i = -1  # 下次循环会变成0
                            else:
                                print("  ⚠ 未找到确认按钮")
                                # 尝试按ESC关闭弹窗
                                await page.keyboard.press('Escape')
                                failed_count += 1
                        else:
                            print("  ⚠ 未找到删除按钮")
                            # 尝试按ESC关闭菜单
                            await page.keyboard.press('Escape')
                            failed_count += 1
                    else:
                        print("  ⚠ 未找到更多操作按钮")
                        failed_count += 1
                        
                except Exception as e:
                    print(f"  ✗ 删除失败: {e}")
                    failed_count += 1
                    # 尝试按ESC关闭可能打开的弹窗
                    try:
                        await page.keyboard.press('Escape')
                    except:
                        pass
                    continue
            
            # 5. 总结
            print("\n" + "=" * 60)
            print("处理完成！")
            print(f"  {'识别' if dry_run else '成功删除'}: {deleted_count} 个视频")
            if not dry_run and failed_count > 0:
                print(f"  失败: {failed_count} 个视频")
            print("=" * 60)
            
            # 保持浏览器打开一会儿，以便查看结果
            if not LOCAL_CHROME_HEADLESS:
                print("\n浏览器将在 5 秒后关闭...")
                await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 安全关闭
        if page:
            try:
                await page.close()
            except:
                pass
        if context:
            try:
                await context.close()
            except:
                pass
        if browser:
            try:
                await browser.close()
            except:
                pass


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量删除抖音审核不通过的视频")
    parser.add_argument('-a', '--account', 
                        default=str(BASE_DIR / "cookies" / "douyin_uploader" / "account.json"),
                        help='账号cookie文件路径')
    parser.add_argument('--dry-run', action='store_true',
                        help='演练模式：只查看要删除的视频，不实际删除')
    parser.add_argument('--debug', action='store_true',
                        help='调试模式：保存页面截图和HTML，用于排查问题')
    
    args = parser.parse_args()
    
    account_file = Path(args.account)
    
    if args.dry_run:
        print("\n⚠ 演练模式：只会显示要删除的视频，不会实际删除")
        print("要实际删除，请去掉 --dry-run 参数\n")
    
    if args.debug:
        print("\n🔍 调试模式已启用：将保存截图和HTML文件\n")
    
    await delete_rejected_videos(account_file, dry_run=args.dry_run, debug=args.debug)


if __name__ == '__main__':
    asyncio.run(main())
