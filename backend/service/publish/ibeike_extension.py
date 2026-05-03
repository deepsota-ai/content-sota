import subprocess
import os
import json
import time
from dotenv import load_dotenv
from DrissionPage import ChromiumPage, ChromiumOptions

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
load_dotenv(os.path.join(_root, '.env'))

DEPLOY_MODE = os.getenv('DEPLOY_MODE', 'local')

# Cloud: unpacked extension directory mounted into container
EXTENSION_DIR = os.path.join(_root, 'extensions', 'ibeike')


def _get_config():
    chrome_path      = os.getenv("CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    default_data_dir = os.path.join(os.path.expanduser("~"), "ChromeAutomationProfile")
    user_data_dir    = os.getenv("CHROME_USER_DATA_DIR", default_data_dir)
    extension_id     = os.getenv("IBEIKE_EXTENSION_ID", "jejejajkcbhejfiocemmddgbkdlhhngm")
    return chrome_path, user_data_dir, extension_id


# ── Xvfb helpers (cloud only) ────────────────────────────────────────────────

def _allocate_xvfb_display() -> str:
    """Find an unused Xvfb display number (:99 .. :199)."""
    import glob
    used = set()
    for p in glob.glob('/tmp/.X*-lock'):
        try:
            used.add(int(p.split('.X')[1].split('-')[0]))
        except (IndexError, ValueError):
            pass
    for n in range(99, 200):
        if n not in used:
            return f':{n}'
    raise RuntimeError('No available Xvfb display number')


def _start_xvfb(display: str):
    """Start Xvfb on the given display and return the process."""
    proc = subprocess.Popen(
        ['Xvfb', display, '-screen', '0', '1920x1080x24'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(1)
    return proc


# ── Cookie injection ─────────────────────────────────────────────────────────

def inject_cookies(page: ChromiumPage, cookies_json: str):
    """
    Inject XHS session cookies into an already-open DrissionPage tab.
    The page should be on a xiaohongshu.com URL before calling this.
    """
    cookies = json.loads(cookies_json) if isinstance(cookies_json, str) else cookies_json
    for cookie in cookies:
        try:
            page.set_cookies(cookie)
        except Exception:
            pass


# ── Chrome launch ────────────────────────────────────────────────────────────

def start_chrome_with_extension(user_data_dir: str | None = None, display: str | None = None):
    """
    Start Chrome with the iBeike extension.

    Local mode: launches Chrome as a subprocess (Windows), returns True/False.
    Cloud mode: launches Chrome under Xvfb, returns the subprocess.Popen object.
    """
    chrome_path, default_data_dir, extension_id = _get_config()
    effective_dir = user_data_dir or default_data_dir

    try:
        os.makedirs(effective_dir, exist_ok=True)
    except Exception as e:
        print(f"❌ 无法创建用户数据目录 {effective_dir}：{e}")
        return False

    if DEPLOY_MODE == 'cloud':
        if display is None:
            raise ValueError('display is required in cloud mode')
        extension_url = f"chrome-extension://{extension_id}/options.html"
        env = {**os.environ, 'DISPLAY': display}
        command = [
            chrome_path,
            '--remote-debugging-port=9223',
            f'--user-data-dir={effective_dir}',
            '--no-first-run',
            '--no-default-browser-check',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            f'--load-extension={EXTENSION_DIR}',
            extension_url,
        ]
        print(f"🚀 [cloud] 启动Chrome on display {display}...")
        proc = subprocess.Popen(command, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ Chrome已启动，PID={proc.pid}")
        return proc
    else:
        # ── local mode (original behaviour) ──────────────────────────────
        if not os.path.exists(chrome_path):
            print(f"❌ 未找到Chrome浏览器：{chrome_path}")
            return False
        extension_url = f"chrome-extension://{extension_id}/options.html"
        command = [
            chrome_path,
            '--remote-debugging-port=9223',
            f'--user-data-dir={effective_dir}',
            '--no-first-run',
            '--no-default-browser-check',
            extension_url,
        ]
        print(f"🚀 [local] 正在启动Chrome...")
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Chrome已启动，插件页：{extension_url}")
        return True


# ── Extension automation ─────────────────────────────────────────────────────

def connect_to_extension(folder_name, mode='video'):
    """连接到已打开的Chrome扩展页面并完成上传操作。"""
    co = ChromiumOptions()
    co.set_local_port(9223)
    page = ChromiumPage(addr_or_opts=co)

    _, _, target_extension_id = _get_config()
    target_url_fragment = f"chrome-extension://{target_extension_id}"

    target_tab = None
    tabs = page.get_tabs()
    for tab in tabs:
        if target_url_fragment in tab.url:
            target_tab = tab
            print(f"✅ 找到插件页: {tab.title}")
            page.activate_tab(tab.tab_id)
            break

    if not target_tab:
        print("❌ 未找到插件页")
        return False

    print("开始操作...")

    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    base_path = os.path.join(script_dir, 'data', 'publish', folder_name)

    content_file = f"{base_path}/1.txt"
    video_file = None

    if mode == 'video':
        for file in os.listdir(base_path):
            if file.lower().endswith('.mov'):
                video_file = f"{base_path}/{file}"
                break
        if not video_file:
            print(f"❌ 未找到视频文件：{base_path}")
            return False

    cover_file = f"{base_path}/1.jpg"

    if not os.path.exists(content_file):
        print(f"❌ 未找到内容文件：{content_file}")
        return False
    if not os.path.exists(cover_file):
        print(f"❌ 未找到封面文件：{base_path}")
        return False

    print(f"📁 使用文件夹：{folder_name}")
    print(f"📄 内容文件：{content_file}")
    if mode == 'video':
        print(f"🎬 视频文件：{video_file}")
    print(f"🖼️ 封面文件：{cover_file}")

    title = ""
    desc = ""
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            full_content = f.read()
            if 'title: ' in full_content:
                start_title = full_content.find('title: ') + 7
                end_title = full_content.find('\ndesc: ')
                if end_title != -1:
                    title = full_content[start_title:end_title].strip()
                    desc = full_content[end_title + 7:].strip()
                else:
                    title = full_content[start_title:].strip()
    except Exception as e:
        print(f"❌ 解析内容文件失败: {e}")

    print(f"📝 标题='{title}', 描述='{desc[:30]}...'")

    print("📝 填写视频标题...")
    title_input = page.ele('css:input[placeholder="输入视频标题"]')
    title_input.input(title)

    print("📝 填写视频描述...")
    desc_textarea = page.ele('css:textarea[placeholder="输入视频描述"]')
    desc_textarea.input(desc)

    if mode == 'video':
        print("📤 上传视频文件...")
        video_upload_input = page.ele('css:input[type="file"][accept="video/*"]')
        video_upload_input.input(video_file)

    print("📤 正在上传封面图片...")
    cover_inputs = page.eles('css:input[type="file"][accept="image/*"]')

    if len(cover_inputs) < 2:
        containers = page.eles('.border-dashed.cursor-pointer')
        if containers:
            inputs_in_containers = []
            for c in containers:
                inp = c.ele('css:input[type="file"]', timeout=1)
                if inp:
                    inputs_in_containers.append(inp)
            if inputs_in_containers:
                cover_inputs = inputs_in_containers

    if len(cover_inputs) >= 2:
        print(f"✅ 找到 {len(cover_inputs)} 个图片上传点...")
        for cover_input in cover_inputs:
            cover_input.input(cover_file)
            time.sleep(3)
    elif len(cover_inputs) == 1:
        print("⚠️ 仅找到1个图片上传点...")
        cover_inputs[0].input(cover_file)
    else:
        print("❌ 未找到任何封面上传点")

    print("⏳ 等待文件上传完成...")
    time.sleep(5)
    return True


def xhs_perfect_cover(folder_name):
    """小红书封面自动完善"""
    co = ChromiumOptions()
    co.set_local_port(9223)
    page = ChromiumPage(addr_or_opts=co)

    target_url = "https://creator.xiaohongshu.com/publish/publish?from=menu&target=video"
    xhs_tab = None
    tabs = page.get_tabs()
    for tab in tabs:
        if "creator.xiaohongshu.com" in tab.url:
            xhs_tab = tab
            page.activate_tab(tab.tab_id)
            break

    if not xhs_tab:
        print("🚀 未找到小红书页面，正在打开...")
        xhs_tab = page.new_tab(target_url)
    elif target_url not in xhs_tab.url:
        print("🚀 正在跳转到小红书发布页...")
        xhs_tab.get(target_url)

    time.sleep(2)

    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cover_file = os.path.join(script_dir, 'data', 'publish', folder_name, '1.jpg')

    if not os.path.exists(cover_file):
        print(f"❌ 未找到封面文件：{cover_file}")
        return False

    try:
        upload_btn = xhs_tab.ele('.upload-cover')
        if not upload_btn:
            upload_btn = xhs_tab.ele('text=设置封面')

        if upload_btn:
            print('📤 点击"设置封面"按钮...')
            upload_btn.click()
            time.sleep(5)

            file_input = xhs_tab.ele('css:input[type="file"][accept*="image"]')
            if file_input:
                file_input.input(cover_file)
                time.sleep(3)
                return True
            else:
                upload_btn.click()
                time.sleep(1)
                backup_input = xhs_tab.ele('css:input[type="file"][accept*="image"]')
                if backup_input:
                    backup_input.input(cover_file)
                    return True
                return False
        else:
            print("❌ 未找到'设置封面'按钮")
            return False

    except Exception as e:
        print(f"❌ XHS 完善操作失败: {e}")
        return False


if __name__ == "__main__":
    start_chrome_with_extension()
    time.sleep(3)
    connect_to_extension("1")
