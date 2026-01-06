import os
from backend.service.publish.ibeike_extension import start_chrome_with_extension, connect_to_extension

class PublishController:
    def __init__(self):
        # 构建正确的 base_path，指向项目根目录下的 data/publish
        self.base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '..', 'data', 'publish')
    
    def get_publish_folders(self, date_folder=None):
        """
        获取发布文件夹列表
        
        Args:
            date_folder: 可选，日期文件夹名称。
                         如果为空，返回日期目录列表 (如 ["2026.1.6", ...])
                         如果不为空，返回该日期下的素材列表
        
        Returns:
            tuple: (成功标志, 数据/错误信息)
        """
        try:
            # 检查base_path是否存在
            if not os.path.exists(self.base_path):
                return True, {
                    'success': True,
                    'folders': []
                }
            
            # 确定要扫描的目标路径
            target_path = self.base_path
            if date_folder:
                target_path = os.path.join(self.base_path, date_folder)
                
            if not os.path.exists(target_path):
                 return True, {
                    'success': True,
                    'folders': []
                }
            
            # 获取所有文件和文件夹
            all_items = os.listdir(target_path)
            
            # 获取所有文件夹
            folders = []
            
            # 如果没有指定日期且不在日期目录下，我们列出的是日期文件夹
            # 这里的判断逻辑是：如果是 date_folder=None，我们期望列出YYYY.M.D格式的文件夹
            # 如果指定了 date_folder，我们期望列出 素材_i 格式的文件夹
            
            # 按修改时间逆序排序
            all_items.sort(key=lambda x: os.path.getmtime(os.path.join(target_path, x)), reverse=True)

            for item in all_items:
                item_path = os.path.join(target_path, item)
                if os.path.isdir(item_path):
                    # 统计文件夹中的文件数量
                    files = os.listdir(item_path)
                    file_count = len(files)
                    
                    title = ""
                    
                    # 如果指定了date_folder，说明我们在看素材列表，需要读取标题
                    if date_folder:
                        # 尝试读取 1.txt 获取标题（支持多行）
                        content_file = os.path.join(item_path, '1.txt')
                        if os.path.exists(content_file):
                            try:
                                with open(content_file, 'r', encoding='utf-8') as f:
                                    full_content = f.read()
                                    if 'title: ' in full_content:
                                        # 提取 title: 到 desc: 之间的内容
                                        start_idx = full_content.find('title: ') + 7
                                        end_idx = full_content.find('\ndesc: ')
                                        
                                        if end_idx != -1:
                                            title = full_content[start_idx:end_idx].strip()
                                        else:
                                            # 如果没有 desc:，则取到最后
                                            title = full_content[start_idx:].strip()
                            except Exception as e:
                                print(f"读取多行标题失败: {e}")
                    
                    folders.append({
                        'name': item,
                        'fileCount': file_count,
                        'title': title
                    })
            
            
            return True, {
                'success': True,
                'folders': folders
            }
        except Exception as e:
            return False, {
                'success': False,
                'message': str(e)
            }
    
    def organize_content(self, materials):
        """
        整理内容，在data/publish/{date}目录下创建文件夹和文件
        
        Args:
            materials: 包含标题和描述的素材列表
            
        Returns:
            tuple: (成功标志, 数据/错误信息)
        """
        try:
            # 检查base_path是否存在，不存在则创建
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
            
            # 获取当前日期 YYYY.M.D
            from datetime import datetime
            now = datetime.now()
            # 注意：用户要求 2026.1.6 这种格式（单数月日不补0），strftime %Y.%-m.%-d 在Windows上可能不支持 %-
            # 手动拼接
            date_str = f"{now.year}.{now.month}.{now.day}"
            
            # 创建日期文件夹路径
            date_folder_path = os.path.join(self.base_path, date_str)
            if not os.path.exists(date_folder_path):
                os.makedirs(date_folder_path)
            
            # 遍历每个素材，创建文件夹和文件
            for i, material in enumerate(materials):
                # 使用标题作为文件夹名称，如果标题为空则使用默认名称
                folder_name = f'素材_{i+1}'
                
                # 创建文件夹
                folder_path = os.path.join(date_folder_path, folder_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                
                # 创建文件内容
                title = material.get('title', '')
                desc = material.get('desc', '')
                
                # 创建{标题}.txt文件，使用示例格式
                # 明确指定文件名为 1.txt
                file_name = f'1.txt'
                file_path = os.path.join(folder_path, file_name)
                
                # 写入文件内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f'title: {title}\n')
                    f.write(f'desc: {desc}\n')
            
            return True, {
                'success': True,
                'message': f'内容整理成功，已保存至 {date_str} 文件夹'
            }
        except Exception as e:
            return False, {
                'success': False,
                'message': str(e)
            }
    
    def publish_content(self, folder_name):
        """
        发布内容
        
        Args:
            folder_name: 发布文件夹名称
            
        Returns:
            tuple: (成功标志, 数据/错误信息)
        """
        try:
            # 检查文件夹是否存在
            folder_path = os.path.join(self.base_path, folder_name)
            if not os.path.exists(folder_path):
                return False, {
                    'success': False,
                    'message': f'文件夹 {folder_name} 不存在'
                }
            
            # 检查文件夹中是否有必要的文件
            content_file = os.path.join(folder_path, '1.txt')
            if not os.path.exists(content_file):
                return False, {
                    'success': False,
                    'message': f'文件夹 {folder_name} 中缺少 1.txt 文件'
                }
            
            # 检查是否有视频文件
            has_video = False
            for file in os.listdir(folder_path):
                if file.endswith('.MOV') or file.endswith('.mov'):
                    has_video = True
                    break
            
            if not has_video:
                return False, {
                    'success': False,
                    'message': f'文件夹 {folder_name} 中缺少视频文件'
                }
            
            # 检查是否有封面文件
            cover_file = os.path.join(folder_path, '1.jpg')
            if not os.path.exists(cover_file):
                return False, {
                    'success': False,
                    'message': f'文件夹 {folder_name} 中缺少 1.jpg 封面文件'
                }
            
            # 启动Chrome并打开扩展页面
            print(f"🚀 开始发布文件夹：{folder_name}")
            
            # 启动Chrome并打开扩展页面
            start_chrome_with_extension()
            
            # 等待Chrome启动完成
            import time
            time.sleep(3)
            
            # 连接到扩展页面并执行发布操作
            success = connect_to_extension(folder_name)
            
            if success:
                return True, {
                    'success': True,
                    'message': f'文件夹 {folder_name} 发布成功'
                }
            else:
                return False, {
                    'success': False,
                    'message': f'文件夹 {folder_name} 发布失败'
                }
        except Exception as e:
            return False, {
                'success': False,
                'message': str(e)
            }