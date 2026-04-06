import subprocess
import os
import time
from dotenv import load_dotenv
from DrissionPage import ChromiumPage, ChromiumOptions

# 加载 .env（从项目根目录）
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(os.path.dirname(_here)))
load_dotenv(os.path.join(_root, '.env'))

def _get_config():
    """读取发布相关环境变量，缺失时给出明确提示"""
    chrome_path      = os.getenv("CHROME_PATH",          r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    user_data_dir    = os.getenv("CHROME_USER_DATA_DIR", r"D:\Users\ChromeAutomationProfile")
    extension_id     = os.getenv("IBEIKE_EXTENSION_ID",  "jejejajkcbhejfiocemmddgbkdlhhngm")
    return chrome_path, user_data_dir, extension_id

def start_chrome_with_extension():
    """启动Chrome并直接打开扩展页面"""
    chrome_path, user_data_dir, target_extension_id = _get_config()
    extension_url = f"chrome-extension://{target_extension_id}/options.html"
    
    if not os.path.exists(chrome_path):
        print(f"❌ 未找到Chrome浏览器：{chrome_path}")
        return False
    
    # 检查用户数据目录是否存在，不存在则创建
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
        print(f"✅ 创建用户数据目录：{user_data_dir}")
    
    command = [
        chrome_path,
        "--remote-debugging-port=9223",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",             # ✅ 关键：禁止首运行欢迎页
        "--no-default-browser-check", # ✅ 关键：禁止询问是否设为默认浏览器
        extension_url
    ]
    
    print(f"🚀 正在启动Chrome远程调试...")
    print(f"命令：{' '.join(command)}")
    
    try:
        # 启动Chrome进程，不等待其结束
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✅ Chrome已启动，直接打开插件页：{extension_url}")
        print(f"✅ 远程调试端口：9223")
        print(f"✅ 用户数据目录：{user_data_dir}")
        return True
    except Exception as e:
        print(f"❌ 启动Chrome失败：{e}")
        return False

def connect_to_extension(folder_name):
    """连接到已打开的Chrome扩展页面

    Args:
        folder_name: 发布文件夹名称，用于动态生成文件路径
    """
    # 1. 配置连接到 9223 端口
    co = ChromiumOptions()
    co.set_local_port(9223) # 指定连接端口为 9223

    # 2. 初始化页面对象
    page = ChromiumPage(addr_or_opts=co)

    # 3. 定义目标插件信息
    _, _, target_extension_id = _get_config()
    target_url_fragment = f"chrome-extension://{target_extension_id}"
    
    # 4. 查找插件页
    target_tab = None
    tabs = page.get_tabs()
    
    for tab in tabs:
        if target_url_fragment in tab.url:
            target_tab = tab
            print(f"✅ 在 9223 端口浏览器中找到插件页: {tab.title}")
            page.activate_tab(tab.tab_id)
            break
    
    # 5. 执行上传操作
    if target_tab:
        print("开始操作...")
        
        # 构建相对路径，查找运行的data文件夹
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        base_path = os.path.join(script_dir, 'data', 'publish', folder_name)
        
        # 动态获取文件路径
        content_file = f"{base_path}/1.txt"
        
        # 查找视频文件（支持 .MOV 和 .mov 后缀）
        video_file = None
        for file in os.listdir(base_path):
            if file.endswith('.MOV') or file.endswith('.mov'):
                video_file = f"{base_path}/{file}"
                break
        
        # 如果没有找到视频文件，返回错误
        if not video_file:
            print(f"❌ 未找到视频文件，请检查 {base_path} 目录")
            return False
        
        # 封面图片路径
        cover_file = f"{base_path}/1.jpg"
        
        # 检查文件是否存在
        if not os.path.exists(content_file):
            print(f"❌ 未找到内容文件：{content_file}")
            return False
        
        if not os.path.exists(cover_file):
            print(f"❌ 未找到封面文件 (1.jpg 或 1.png)：{base_path}")
            return False
        
        print(f"📁 使用文件夹：{folder_name}")
        print(f"📄 内容文件：{content_file}")
        print(f"🎬 视频文件：{video_file}")
        print(f"🖼️ 封面文件：{cover_file}")
        
        # 解析 content.txt 获取标题和描述（支持多行标题）
        title = ""
        desc = ""
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                full_content = f.read()
                
                # 提取标题
                if 'title: ' in full_content:
                    start_title = full_content.find('title: ') + 7
                    end_title = full_content.find('\ndesc: ')
                    
                    if end_title != -1:
                        title = full_content[start_title:end_title].strip()
                        # 提取描述 (从 desc: 之后开始)
                        desc = full_content[end_title + 7:].strip()
                    else:
                        title = full_content[start_title:].strip()
        except Exception as e:
            print(f"❌ 解析内容文件失败: {e}")
        
        print(f"📝 读取到内容：标题='{title}', 描述='{desc}'")
        
        # 填写视频标题
        print("📝 填写视频标题...")
        title_input = page.ele('css:input[placeholder="输入视频标题"]')
        title_input.input(title)
        
        # 填写视频描述
        print("📝 填写视频描述...")
        desc_textarea = page.ele('css:textarea[placeholder="输入视频描述"]')
        desc_textarea.input(desc)
        
        # 上传视频文件
        print("📤 上传视频文件...")
        video_upload_input = page.ele('css:input[type="file"][accept="video/*"]')
        video_upload_input.input(video_file)  # 在DrissionPage中，使用input()方法上传文件
        
        # 上传封面图片 (横版和竖版封面一起上传)
        print("📤 正在上传封面图片 (同时适配横版和竖版)...")
        # 根据用户提供的 HTML，封面上传点通常具有特定的类名
        cover_inputs = page.eles('css:input[type="file"][accept="image/*"]')
        
        # 备选：如果直接找 input 有干扰，可以先找到容器 div 再找里面的 input
        if len(cover_inputs) < 2:
            containers = page.eles('.border-dashed.cursor-pointer')
            if containers:
                inputs_in_containers = []
                for c in containers:
                    inp = c.ele('css:input[type="file"]', timeout=1)
                    if inp: inputs_in_containers.append(inp)
                if inputs_in_containers:
                    cover_inputs = inputs_in_containers

        if len(cover_inputs) >= 2:
            print(f"✅ 找到 {len(cover_inputs)} 个图片上传点，正在逐个上传...")
            for cover_input in cover_inputs:
                cover_input.input(cover_file)
                time.sleep(3)
        elif len(cover_inputs) == 1:
            print("⚠️ 仅找到 1 个图片上传点，正在上传...")
            cover_inputs[0].input(cover_file)
        else:
            print("❌ 未找到任何封面上传点")
        
        # 等待上传完成
        print("⏳ 等待文件上传完成...")
        time.sleep(5)  # 等待5秒，确保文件上传完成
        
    else:
        print("❌ 未找到插件页，请检查：\n1. 9223端口的Chrome是否已开启\n2. Chrome是否已正确打开插件页")
        return False
    
    return True

def xhs_perfect_cover(folder_name):
    """小红书封面自动完善
    
    Args:
        folder_name: 素材文件夹名称
    """
    # 1. 配置连接到 9223 端口
    co = ChromiumOptions()
    co.set_local_port(9223)
    
    # 2. 初始化页面对象
    page = ChromiumPage(addr_or_opts=co)
    
    # 3. 查找或打开小红书发布页
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
    
    # 等待页面加载
    time.sleep(2)
    
    # 4. 执行封面上传操作
    print(f"🎬 准备完善素材 {folder_name} 的小红书封面...")
    
    # 构建图片路径
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    cover_file = os.path.join(script_dir, 'data', 'publish', folder_name, '1.jpg')
    
    if not os.path.exists(cover_file):
        print(f"❌ 未找到封面文件：{cover_file}")
        return False
        
    try:
        # 查找“设置封面”元素
        # 根据用户提供的 class: upload-cover
        upload_btn = xhs_tab.ele('.upload-cover')
        if not upload_btn:
            # 备选：查找包含“设置封面”文字的元素
            upload_btn = xhs_tab.ele('text=设置封面')
            
        if upload_btn:
            print("📤 点击“设置封面”按钮以打开对话框...")
            upload_btn.click()
            time.sleep(5) # 等待弹窗出现
            
            print("📤 正在精准定位封面上传控件...")

            # 根据终端反馈，第二个 input 具有 accept="image/png, image/jpeg, image/*"
            # 我们直接使用 accept 属性作为特征选择器，这样更稳健，不受顺序影响
            file_input = xhs_tab.ele('css:input[type="file"][accept*="image"]')

            if file_input:
                print(f"✅ 找到封面上传控件 (ID: {file_input.attr('data-v-29a4ce9a') or 'unknown'})，正在上传...")
                file_input.input(cover_file)
                time.sleep(3) # 等待上传进度条
                return True
            else:
                print("❌ 未精准定位到封面 input[type='file'][accept*='image']")
                # 最后的兜底：如果属性匹配不到，尝试点击后再找
                upload_btn.click() 
                time.sleep(1)
                backup_input = xhs_tab.ele('css:input[type="file"][accept*="image"]')
                if backup_input:
                    backup_input.input(cover_file)
                    return True
                return False
        else:
            print("❌ 未找到‘设置封面’按钮，请确认已进入发布编辑页面")
            return False
            
    except Exception as e:
        print(f"❌ XHS 完善操作失败: {e}")
        return False

if __name__ == "__main__":
    # 启动Chrome并直接打开扩展页面
    start_chrome_with_extension()
    time.sleep(3)
    # 连接到扩展页面，默认使用文件夹"1"
    connect_to_extension("1")