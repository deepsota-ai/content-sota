import os
import re
import json
from dotenv import load_dotenv

# 加载环境变量
# 计算项目根目录，确保能找到 .env 文件
current_dir = os.path.dirname(os.path.abspath(__file__))
# math: content_generate.py -> content -> service -> backend -> root (4 levels)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

# 尝试导入Google Gemini API
from google import genai

class ContentCreatorService:
    def __init__(self):
        # 初始化Google Gemini客户端
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-pro-preview"
        
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        # 文件路径
        self.data_dir = os.path.join(self.project_root, "data")
        self.content_gen_dir = os.path.join(self.data_dir, "contentGeneration")
        self.material_file = os.path.join(self.content_gen_dir, "material.txt")
        self.title_tips_file = os.path.join(self.content_gen_dir, "tip", "title.txt")
        self.hook_tips_file = os.path.join(self.content_gen_dir, "tip", "hook.txt")
    
    def read_file(self, file_path):
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件 {file_path} 失败: {str(e)}")
            return None

    def _parse_json_response(self, response_text):
        """解析可能包含Markdown格式的JSON响应"""
        content = response_text.strip()
        # 清理Markdown代码块标记
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
    
    def generate_title(self, material_content, title_tips):
        """根据素材和标题技巧生成标题"""
        try:
            prompt = f"""作为一名专业的小红书内容创作者，请根据以下素材和标题创作技巧，为一家提供美甲、精油推背、纹眉、面部轻医美（如水光针）服务的美业门店生成3-5个吸引人的小红书标题：

                    【素材内容】
                    {material_content}

                    【标题创作技巧】
                    {title_tips}

                    请确保生成的标题：
                    1. 符合提供的技巧
                    2. 有情绪共鸣、有痛点或有好奇心驱动
                    3. 与素材对应的具体业务（美甲/精油推背/纹眉/轻医美）紧密相关
                    4. 不要说教，要真实有温度，像女生闺蜜分享
                    5. 适合小红书平台风格，可以带emoji

                    请严格按照以下格式返回结果：
                    - 必须是JSON格式
                    - 必须返回一个纯字符串数组，数组名为"titles"
                    - 每个标题必须是字符串，不能是对象或其他类型
                    - 不要包含任何额外的解释或说明
                    - 示例格式：{{"titles": ["标题1", "标题2", "标题3"]}}
                    """
            
            # 使用Google Gemini API生成内容
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # 解析响应
            result = self._parse_json_response(response.text)
            
            # 检查返回结果类型
            if isinstance(result, list):
                return result
            return result.get("titles", [])
            
        except Exception as e:
            print(f"生成标题失败: {str(e)}")
            return []
    
    def generate_hook(self, material_content, hook_tips):
        """根据素材和钩子技巧生成钩子"""
        try:
            prompt = f"""作为一名专业的小红书内容创作者，请根据以下素材和钩子创作技巧，为一家提供美甲、精油推背、纹眉、面部轻医美（如水光针）服务的美业门店生成3-5个吸引人的开头钩子：

                        【素材内容】
                        {material_content}

                        【钩子创作技巧】
                        {hook_tips}

                        请确保生成的钩子：
                        1. 符合提供的技巧，但要尽量使用不同的技巧模板，避免重复使用相同结构
                        2. 吸引人且戳中对应业务的痛点（如指甲问题、身体疲劳、眉毛焦虑、皮肤状态等）
                        3. 与素材对应的具体业务（美甲/精油推背/纹眉/轻医美）紧密相关
                        4. 能够让目标客群（爱美女生）忍不住继续看
                        5. 确保每个钩子的结构和表达方式都有明显差异，避免内容重合

                        请严格按照以下格式返回结果：
                        - 必须是JSON格式
                        - 必须返回一个纯字符串数组，数组名为"hooks"
                        - 每个钩子必须是字符串，不能是对象或其他类型
                        - 不要包含任何额外的解释或说明
                        - 示例格式：{{"hooks": ["钩子1", "钩子2", "钩子3"]}}
                        """
            
            # 使用Google Gemini API生成内容
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # 解析响应
            result = self._parse_json_response(response.text)
            
            # 检查返回结果类型
            if isinstance(result, list):
                return result
            return result.get("hooks", [])
            
        except Exception as e:
            print(f"生成钩子失败: {str(e)}")
            return []
    
    def generate_optimized_content(self, material_content):
        """优化文案内容，调用AI生成有情绪、有画面、有代入感的文案"""
        try:
            prompt = f"""作为一名专业的小红书美业博主，请根据以下素材内容，生成相应的1条有情绪、有画面、有代入感的美业服务种草文案（业务范围：美甲、精油推背、纹眉、面部轻医美如水光针）：

                    【素材内容】
                    {material_content}

                    【优化要求】
                    1. 要有情绪：触发目标客群（爱美女生）的情感共鸣（疲惫、变美渴望、治愈感等）
                    2. 要有画面：让读者仿佛能感受到做完项目后的状态（放松、精致、自信）
                    3. 要有代入感：让读者感觉"这说的就是我！"
                    4. 被击中、想预约：激发读者想到店体验的欲望
                    5. 避免说教感：用闺蜜分享的口吻，真实自然
                    6. 要口语化，字数不用太多，和原文案相近或多一点即可
                    7. 适合小红书平台风格，可以适当加emoji

                    请严格按照以下格式返回结果：
                    - 必须是JSON格式
                    - 必须返回一个纯字符串数组，数组名为"contents"
                    - 每个文案必须是字符串，不能是对象或其他类型
                    - 不要包含任何额外的解释或说明
                    - 示例格式：{{"contents": ["内容1"]}}
                    """
            
            # 使用Google Gemini API生成内容
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # 解析AI返回的JSON内容
            result = self._parse_json_response(response.text)
            print(result)
            
            # 返回生成的内容数组
            return result.get("contents", [material_content])
        except Exception as e:
            print(f"优化文案失败: {str(e)}")
            return [material_content]
    
    def create_content(self, material_content=None, title_tips=None, hook_tips=None, generate_type="both", model_name=None):
        """主函数：生成标题、钩子或优化文案

        Args:
            material_content: 素材内容字符串或字符串数组
            title_tips: 标题技巧字符串
            hook_tips: 钩子技巧字符串
            generate_type: 生成类型，可选值："both"（生成标题和钩子）、"title"（只生成标题）、"hook"（只生成钩子）、"content"（优化文案）
            model_name: 可选，覆盖默认模型 ID

        Returns:
            包含titles、hooks和/或content的字典
        """
        # 如果传入了 model_name，本次调用使用该模型
        if model_name:
            self.model_name = model_name

        # 如果没有传入参数，从文件读取
        if not material_content:
            material_content = self.read_file(self.material_file)

        
        # 根据generate_type确定需要的参数
        if generate_type == "title":
            if not title_tips:
                title_tips = self.read_file(self.title_tips_file)
                
            if not all([material_content, title_tips]):
                print("无法获取必要的内容，生成标题失败")
                return None
            
            # 只生成标题
            titles = self.generate_title(material_content, title_tips)
            return {
                "titles": titles,
                "hooks": [],
                "content": ""
            }
        elif generate_type == "hook":
            if not hook_tips:
                hook_tips = self.read_file(self.hook_tips_file)
                
            if not all([material_content, hook_tips]):
                print("无法获取必要的内容，生成钩子失败")
                return None
            
            # 只生成钩子
            hooks = self.generate_hook(material_content, hook_tips)
            return {
                "titles": [],
                "hooks": hooks,
                "content": ""
            }
        elif generate_type == "content":
            # ... (content loading logic remains same)
            if not material_content:
                print("无法获取必要的内容，优化文案失败")
                return None
            
            # 优化文案
            if isinstance(material_content, list):
                # 多个素材，生成多个优化文案
                all_optimized_contents = []
                for content in material_content:
                    optimized_contents = self.generate_optimized_content(content)
                    all_optimized_contents.extend(optimized_contents)
                return {
                    "titles": [],
                    "hooks": [],
                    "content": all_optimized_contents
                }
            else:
                # 单个素材，生成单个优化文案
                optimized_content = self.generate_optimized_content(material_content)
                return {
                    "titles": [],
                    "hooks": [],
                    "content": optimized_content
                }
        else:  # 默认生成标题和钩子
            if not title_tips:
                title_tips = self.read_file(self.title_tips_file)
            if not hook_tips:
                hook_tips = self.read_file(self.hook_tips_file)
                
            if not all([material_content, title_tips, hook_tips]):
                print("无法获取必要的内容，生成内容失败")
                return None
            
            # 生成标题和钩子
            titles = self.generate_title(material_content, title_tips)
            hooks = self.generate_hook(material_content, hook_tips)
            
            return {
                "titles": titles,
                "hooks": hooks,
                "content": ""
            }

# 测试代码
if __name__ == "__main__":
    service = ContentCreatorService()
    result = service.create_content()
    if result:
        print("生成的标题：")
        for i, title in enumerate(result["titles"]):
            print(f"{i+1}. {title}")
        
        print("\n生成的钩子：")
        for i, hook in enumerate(result["hooks"]):
            print(f"{i+1}. {hook}")