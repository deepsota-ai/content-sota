from PIL import Image
import os

class CoverGenerator:
    def __init__(self):
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))        
        self.data_dir = os.path.join(self.project_root, "data")
        self.cover_generation_dir = os.path.join(self.data_dir, "coverGeneration")
        self.to_ps_dir = os.path.join(self.cover_generation_dir, "toPs")
        self.mask_output_dir = os.path.join(self.cover_generation_dir, "cover", "mask")
        self.input_image_path = os.path.join(self.data_dir, "1.jpg")
        self.output_image_path = os.path.join(self.mask_output_dir, "output_with_mask.jpg")
    
    def open_image(self, image_path):
        """打开图片"""
        try:
            return Image.open(image_path)
        except Exception as e:
            print(f"打开图片失败: {str(e)}")
            return None
    
    def create_solid_mask(self, width, height, alpha=153, color=(0, 0, 0)):
        """创建纯色蒙版
        
        Args:
            width: 蒙版宽度
            height: 蒙版高度
            alpha: 透明度 (0-255)，默认60%透明度即153
            color: 颜色 (RGB)，默认黑色
            
        Returns:
            纯色蒙版图像
        """
        return Image.new("RGBA", (width, height), (*color, alpha))
    
    def apply_mask(self, image, mask):
        """将蒙版应用到图片上
        
        Args:
            image: 原始图片
            mask: 蒙版图片
            
        Returns:
            应用蒙版后的图片
        """
        # 确保蒙版和图片尺寸一致
        if image.size != mask.size:
            mask = mask.resize(image.size)
        
        # 如果原始图片不是RGBA格式，转换为RGBA
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # 将原始图片和蒙版合并
        result = Image.alpha_composite(image, mask)
        
        return result
    
    def save_image(self, image, output_path):
        """保存图片"""
        try:
            # 保存为PNG格式以保留透明度
            image.save(output_path, "PNG")
            print(f"图片已保存到: {output_path}")
            return True
        except Exception as e:
            print(f"保存图片失败: {str(e)}")
            return False
    
    def generate_cover_with_mask(self, image_name=None):
        """生成带有60%透明度蒙版的封面
        
        Args:
            image_name: 可选，指定要处理的图片名称（来自data/toPs目录）
            如果不指定，则使用默认图片
        """
        # 确定要处理的图片路径
        if image_name:
            # 使用指定的图片（来自data/toPs目录）
            image_path = os.path.join(self.to_ps_dir, image_name)
        else:
            # 使用默认图片
            image_path = self.input_image_path
        
        # 打开原始图片
        image = self.open_image(image_path)
        if not image:
            return None
        
        # 创建60%透明度的黑色蒙版（255*0.6=153）
        mask = self.create_solid_mask(image.width, image.height, alpha=153)
        
        # 应用蒙版
        result = self.apply_mask(image, mask)
        
        # 保存结果（如果是指定图片，则使用不同的输出文件名）
        if image_name:
            output_path = os.path.join(self.mask_output_dir, image_name)
        else:
            output_path = self.output_image_path
        
        self.save_image(result, output_path)
        
        return result

# 测试代码
if __name__ == "__main__":
    generator = CoverGenerator()
    
    # 生成带有60%透明度蒙版的封面
    print("正在生成带有60%透明度蒙版的封面...")
    generator.generate_cover_with_mask()