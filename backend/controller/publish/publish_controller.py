import os
import time
import uuid
import threading
from backend.service.publish.ibeike_extension import (
    start_chrome_with_extension, connect_to_extension, DEPLOY_MODE
)

# In-memory job status store for async cloud publishes
_job_status: dict = {}
_publish_semaphore = threading.Semaphore(1)  # one publish at a time


class PublishController:
    def __init__(self):
        self.base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '..', 'data', 'publish'
        )

    def get_publish_folders(self, date_folder=None):
        try:
            if not os.path.exists(self.base_path):
                return True, {'success': True, 'folders': []}

            target_path = self.base_path
            if date_folder:
                target_path = os.path.join(self.base_path, date_folder)

            if not os.path.exists(target_path):
                return True, {'success': True, 'folders': []}

            all_items = os.listdir(target_path)
            all_items.sort(
                key=lambda x: os.path.getmtime(os.path.join(target_path, x)),
                reverse=False
            )

            folders = []
            for item in all_items:
                item_path = os.path.join(target_path, item)
                if not os.path.isdir(item_path):
                    continue
                files = os.listdir(item_path)
                title = ""
                if date_folder:
                    content_file = os.path.join(item_path, '1.txt')
                    if os.path.exists(content_file):
                        try:
                            with open(content_file, 'r', encoding='utf-8') as f:
                                full_content = f.read()
                                if 'title: ' in full_content:
                                    start_idx = full_content.find('title: ') + 7
                                    end_idx = full_content.find('\ndesc: ')
                                    if end_idx != -1:
                                        title = full_content[start_idx:end_idx].strip()
                                    else:
                                        title = full_content[start_idx:].strip()
                        except Exception as e:
                            print(f"读取标题失败: {e}")
                folders.append({'name': item, 'fileCount': len(files), 'title': title})

            return True, {'success': True, 'folders': folders}
        except Exception as e:
            return False, {'success': False, 'message': str(e)}

    def _read_hashtags(self):
        hashtag_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '..', 'data', 'contentGeneration', 'tip', 'hashtag.txt'
        )
        try:
            with open(hashtag_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content if content else ""
        except Exception:
            return ""

    def organize_content(self, materials):
        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)

            from datetime import datetime
            now = datetime.now()
            date_str = f"{now.year}.{now.month}.{now.day}"
            date_folder_path = os.path.join(self.base_path, date_str)
            if not os.path.exists(date_folder_path):
                os.makedirs(date_folder_path)

            for i, material in enumerate(materials):
                folder_name = f'素材_{i+1}'
                folder_path = os.path.join(date_folder_path, folder_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                title = material.get('title', '')
                desc = material.get('desc', '')
                with open(os.path.join(folder_path, '1.txt'), 'w', encoding='utf-8') as f:
                    f.write(f'title: {title}\n')
                    f.write(f'desc: {desc}\n')

            hashtags = self._read_hashtags()
            return True, {
                'success': True,
                'message': f'内容整理成功，已保存至 {date_str} 文件夹',
                'hashtags': hashtags,
                'date': date_str,
            }
        except Exception as e:
            return False, {'success': False, 'message': str(e)}

    def publish_content(self, folder_name, account_id=None):
        """
        Publish a folder's content.
        - account_id: optional; if omitted uses the default Chrome profile from env.
        - Returns async job info when DEPLOY_MODE=cloud.
        """
        try:
            folder_path = os.path.join(self.base_path, folder_name)
            if not os.path.exists(folder_path):
                return False, {'success': False, 'message': f'文件夹 {folder_name} 不存在'}

            content_file = os.path.join(folder_path, '1.txt')
            if not os.path.exists(content_file):
                return False, {'success': False, 'message': f'文件夹 {folder_name} 中缺少 1.txt 文件'}

            has_video = any(f.lower().endswith('.mov') for f in os.listdir(folder_path))
            publish_mode = 'video' if has_video else 'image'

            if publish_mode == 'image':
                if not os.path.exists(os.path.join(folder_path, '1.jpg')):
                    return False, {
                        'success': False,
                        'message': f'文件夹 {folder_name} 中缺少 1.jpg 图片文件'
                    }
            else:
                if not os.path.exists(os.path.join(folder_path, '1.jpg')):
                    return False, {
                        'success': False,
                        'message': f'文件夹 {folder_name} 中缺少 1.jpg 封面文件'
                    }

            # Resolve account profile/cookies
            user_data_dir = None
            account = None
            if account_id:
                from backend.controller.account.account_controller import AccountController
                account = AccountController().get_account_by_id(account_id)
                if account and account.get('mode') == 'local':
                    user_data_dir = account.get('profile_dir')

            print(f"🚀 开始发布文件夹：{folder_name}（{publish_mode}模式）")

            if DEPLOY_MODE == 'cloud':
                job_id = str(uuid.uuid4())[:12]
                _job_status[job_id] = 'running'
                t = threading.Thread(
                    target=self._publish_cloud,
                    args=(folder_name, publish_mode, account, job_id),
                    daemon=True,
                )
                t.start()
                return True, {
                    'success': True,
                    'async': True,
                    'job_id': job_id,
                    'message': f'发布任务已提交（{publish_mode}模式）',
                }
            else:
                # Local synchronous publish
                start_chrome_with_extension(user_data_dir=user_data_dir)
                time.sleep(3)
                success = connect_to_extension(folder_name, mode=publish_mode)
                if success:
                    return True, {'success': True, 'message': f'文件夹 {folder_name} 发布成功'}
                else:
                    return False, {'success': False, 'message': f'文件夹 {folder_name} 发布失败'}

        except Exception as e:
            return False, {'success': False, 'message': str(e)}

    def _publish_cloud(self, folder_name, publish_mode, account, job_id):
        """Background cloud publish: Xvfb + Chrome + cookie injection + iBeike."""
        import tempfile, shutil
        from backend.service.publish.ibeike_extension import (
            _allocate_xvfb_display, _start_xvfb, inject_cookies
        )
        from DrissionPage import ChromiumPage, ChromiumOptions

        user_data_dir = tempfile.mkdtemp(prefix='xhs_pub_')
        xvfb_proc = None
        chrome_proc = None
        display = None

        with _publish_semaphore:
            try:
                display = _allocate_xvfb_display()
                xvfb_proc = _start_xvfb(display)
                time.sleep(2)

                chrome_proc = start_chrome_with_extension(
                    user_data_dir=user_data_dir, display=display
                )
                time.sleep(4)

                # If we have cloud account cookies, inject them
                if account and account.get('mode') == 'cloud' and account.get('cookies_decrypted'):
                    co = ChromiumOptions()
                    co.set_local_port(9223)
                    page = ChromiumPage(addr_or_opts=co)
                    # Navigate to XHS domain to establish cookie context
                    page.get('https://www.xiaohongshu.com')
                    time.sleep(2)
                    inject_cookies(page, account['cookies_decrypted'])
                    time.sleep(1)

                success = connect_to_extension(folder_name, mode=publish_mode)
                _job_status[job_id] = 'done' if success else 'error:发布失败'

            except Exception as e:
                _job_status[job_id] = f'error:{e}'
            finally:
                if chrome_proc:
                    try:
                        chrome_proc.terminate()
                    except Exception:
                        pass
                if xvfb_proc:
                    try:
                        xvfb_proc.terminate()
                    except Exception:
                        pass
                shutil.rmtree(user_data_dir, ignore_errors=True)

    def get_job_status(self, job_id: str):
        status = _job_status.get(job_id)
        if status is None:
            return False, {'success': False, 'message': '任务不存在'}
        if status == 'done':
            return True, {'success': True, 'status': 'done'}
        if status.startswith('error:'):
            return False, {'success': False, 'status': 'error', 'message': status[6:]}
        return True, {'success': True, 'status': 'running'}

    def get_content(self, folder_name):
        try:
            content_file = os.path.join(self.base_path, folder_name, '1.txt')
            if not os.path.exists(content_file):
                return False, {'success': False, 'message': '未找到 1.txt 文件'}
            with open(content_file, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            title = ''
            desc_lines = []
            in_desc = False
            for line in lines:
                if line.startswith('title:') and not in_desc:
                    title = line[len('title:'):].strip()
                elif line.startswith('desc:'):
                    desc_lines.append(line[len('desc:'):].strip())
                    in_desc = True
                elif in_desc:
                    desc_lines.append(line)
            return True, {'success': True, 'title': title, 'desc': '\n'.join(desc_lines)}
        except Exception as e:
            return False, {'success': False, 'message': str(e)}

    def update_content(self, folder_name, title, desc):
        try:
            folder_path = os.path.join(self.base_path, folder_name)
            if not os.path.exists(folder_path):
                return False, {'success': False, 'message': f'文件夹 {folder_name} 不存在'}
            with open(os.path.join(folder_path, '1.txt'), 'w', encoding='utf-8') as f:
                f.write(f'title: {title}\n')
                f.write(f'desc: {desc}\n')
            return True, {'success': True}
        except Exception as e:
            return False, {'success': False, 'message': str(e)}
