from PIL import Image
import os

class ImageCutter:
    def __init__(self):
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))        
        self.data_dir = os.path.join(self.project_root, "data")
        self.cover_generation_dir = os.path.join(self.data_dir, "coverGeneration")
        self.input_image_path = os.path.join(self.data_dir, "1.jpg")
        self.output_dir = self.data_dir
        self.crop_output_dir = os.path.join(self.cover_generation_dir, "cover", "crop")
        
        # 确保输出目录存在
        if not os.path.exists(self.crop_output_dir):
            os.makedirs(self.crop_output_dir)
    
    def open_image(self, image_path):
        """打开图片"""
        try:
            return Image.open(image_path)
        except Exception as e:
            print(f"打开图片失败: {str(e)}")
            return None
    
    def calculate_crop_box(self, image_width, image_height, target_ratio):
        """计算裁剪区域
        
        Args:
            image_width: 原始图片宽度
            image_height: 原始图片高度
            target_ratio: 目标宽高比 (width/height)
            
        Returns:
            裁剪区域坐标 (left, top, right, bottom)
        """
        # 计算原始图片的宽高比
        original_ratio = image_width / image_height
        
        if original_ratio > target_ratio:
            # 原始图片更宽，需要裁剪宽度
            new_width = int(image_height * target_ratio)
            left = (image_width - new_width) // 2
            top = 0
            right = left + new_width
            bottom = image_height
        else:
            # 原始图片更高，需要裁剪高度
            new_height = int(image_width / target_ratio)
            left = 0
            top = (image_height - new_height) // 2
            right = image_width
            bottom = top + new_height
        
        return (left, top, right, bottom)
    
    def crop_image(self, image, target_ratio, output_filename):
        """裁剪图片
        
        Args:
            image: 原始图片
            target_ratio: 目标宽高比
            output_filename: 输出文件名
            
        Returns:
            裁剪后的图片
        """
        # 计算裁剪区域
        crop_box = self.calculate_crop_box(image.width, image.height, target_ratio)
        
        # 裁剪图片
        cropped_image = image.crop(crop_box)
        
        # 保存裁剪后的图片到指定目录
        output_path = os.path.join(self.crop_output_dir, output_filename)
        try:
            # 如果是RGBA模式，转换为RGB模式，因为JPEG不支持透明度
            if cropped_image.mode == 'RGBA':
                cropped_image = cropped_image.convert('RGB')
            
            cropped_image.save(output_path)
            print(f"裁剪后的图片已保存到: {output_path}")
            return cropped_image
        except Exception as e:
            print(f"保存裁剪后的图片失败: {str(e)}")
            return None
    
    def cut_to_3_4(self, output_filename=None):
        """将图片裁剪为3:4比例"""
        image = self.open_image(self.input_image_path)
        if not image:
            return None
        
        # 3:4比例的宽高比为0.75 (3/4)
        if output_filename:
            return self.crop_image(image, 3/4, output_filename)
        else:
            # 生成默认的输出文件名，将冒号替换为下划线，避免Windows文件名问题
            image_name = os.path.basename(self.input_image_path)
            output_filename = image_name
            return self.crop_image(image, 3/4, output_filename)

# 测试代码
if __name__ == "__main__":
    cutter = ImageCutter()
    