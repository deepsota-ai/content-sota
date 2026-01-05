import os
import shutil

class CleanController:
    def __init__(self):
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.data_dir = os.path.join(self.project_root, "data")
        
        # 定义需要清理的目录路径
        self.tip_dir = os.path.join(self.data_dir, "contentGeneration", "tip")
        self.cover_gen_dir = os.path.join(self.data_dir, "coverGeneration")
        self.publish_dir = os.path.join(self.data_dir, "publish")

    def clean_all(self):
        """执行所有清理操作"""
        results = {
            # "tip": self._clean_tip_txt(), # 用户要求取消清理 tip 目录
            "cover": self._clean_cover_images(),
            "publish": self._clean_publish_folder()
        }
        return True, results

    def _clean_tip_txt(self):
        """清理 data/contentGeneration/tip 下的 txt 文件"""
        if not os.path.exists(self.tip_dir):
            return "Directory not found"
        
        count = 0
        try:
            for filename in os.listdir(self.tip_dir):
                if filename.lower().endswith('.txt'):
                    file_path = os.path.join(self.tip_dir, filename)
                    os.remove(file_path)
                    count += 1
            
            # 清理后重新创建必要的文件
            title_file = os.path.join(self.tip_dir, 'title.txt')
            hook_file = os.path.join(self.tip_dir, 'hook.txt')
            
            if not os.path.exists(title_file):
                with open(title_file, 'w', encoding='utf-8') as f:
                    f.write("") # 创建空文件
            
            if not os.path.exists(hook_file):
                with open(hook_file, 'w', encoding='utf-8') as f:
                    f.write("") # 创建空文件
                    
            return f"Deleted {count} txt files. Recreated title.txt and hook.txt"
        except Exception as e:
            return f"Error: {str(e)}"

    def _clean_cover_images(self):
        """清理 data/coverGeneration 下（包括子文件夹）的所有图片"""
        if not os.path.exists(self.cover_gen_dir):
            return "Directory not found"
        
        count = 0
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.psd', '.webp'}
        
        try:
            for root, dirs, files in os.walk(self.cover_gen_dir):
                for filename in files:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in image_exts:
                        file_path = os.path.join(root, filename)
                        os.remove(file_path)
                        count += 1
            return f"Deleted {count} images"
        except Exception as e:
            return f"Error: {str(e)}"

    def _clean_publish_folder(self):
        """清理 publish 下的所有文件夹和文件"""
        if not os.path.exists(self.publish_dir):
            return "Directory not found"
        
        deleted_files = 0
        deleted_dirs = 0
        
        try:
            # 清空目录但不删除目录本身（或者删除内容后保留空目录）
            # 用户要求 "publish下的所有文件夹"，通常意味着清空
            for item in os.listdir(self.publish_dir):
                item_path = os.path.join(self.publish_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    deleted_files += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    deleted_dirs += 1
            return f"Deleted {deleted_dirs} folders and {deleted_files} files"
        except Exception as e:
            return f"Error: {str(e)}"
