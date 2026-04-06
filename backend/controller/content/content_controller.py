from backend.service.content.content_generate import ContentCreatorService

class ContentController:
    def __init__(self):
        self.service = ContentCreatorService()
    
    def generate_content(self, material_content=None, generate_type="both", model_name=None):
        """
        生成内容（标题和钩子）

        Args:
            material_content: 素材内容字符串
            generate_type: 生成类型，可选值："both"（生成标题和钩子）、"title"（只生成标题）、"hook"（只生成钩子）
            model_name: 可选，指定使用的 Gemini 模型 ID

        Returns:
            tuple: (成功标志, 数据/错误信息)
        """
        try:
            result = self.service.create_content(material_content, generate_type=generate_type, model_name=model_name)
            if result:
                return True, {
                    'success': True,
                    'data': result
                }
            else:
                return False, {
                    'success': False,
                    'error': '生成内容失败'
                }
        except Exception as e:
            return False, {
                'success': False,
                'error': str(e)
            }