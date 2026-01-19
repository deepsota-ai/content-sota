from backend.service.cover.mask import CoverGenerator
from backend.service.cover.cut import ImageCutter
import os

class CoverController:
    def __init__(self):
        # 获取项目根目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))        
        self.data_dir = os.path.join(self.project_root, "data")
        self.cover_generation_dir = os.path.join(self.data_dir, "coverGeneration")
        self.to_ps_dir = os.path.join(self.cover_generation_dir, "toPs")
        self.mask_dir = os.path.join(self.cover_generation_dir, "cover", "mask")
        self.crop_dir = os.path.join(self.cover_generation_dir, "cover", "crop")
        self.generator = CoverGenerator()
        self.cutter = ImageCutter()
    
    def generate_cover_with_mask(self, image_names=None):
        """生成带有蒙版的封面
        
        Args:
            image_names: 可选，要处理的图片名称数组（来自data/toPs目录）。如果为None或空数组，将处理所有图片。
        """
        try:
            # 如果没有指定图片名称，获取所有图片
            if not image_names:
                # 从toPs目录获取图片
                files = os.listdir(self.to_ps_dir)
                image_names = [f for f in files if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))]
            
            # 循环处理每个图片
            results = []
            for image_name in image_names:
                try:
                    # 调用service层的方法生成蒙版封面
                    result = self.generator.generate_cover_with_mask(image_name)
                    
                    if result:
                        results.append({"image": image_name, "success": True, "message": "蒙版封面生成成功"})
                    else:
                        results.append({"image": image_name, "success": False, "error": "蒙版封面生成失败"})
                except Exception as e:
                    results.append({"image": image_name, "success": False, "error": str(e)})
            
            return True, {"results": results}
        except Exception as e:
            return False, {"error": str(e)}
    
    def generate_cropped_image(self, image_names=None, aspect_ratio="4:3"):
        """生成裁剪图片
        
        Args:
            image_names: 可选，要处理的图片名称数组（来自data/cover/mask目录）。如果为None或空数组，将处理所有图片。
            aspect_ratio: 裁剪比例，当前固定使用4:3
        """
        try:
            # 循环处理每个图片
            results = []
            for image_name in image_names:
                try:
                    # 打开图片
                    image_path = os.path.join(self.mask_dir, image_name)
                    
                    # 生成输出文件名，将冒号替换为下划线，避免Windows文件名问题
                    output_filename = image_name
                    
                    # 直接调用service层的cut_to_3_2方法裁剪图片
                    # 注意:cut_to_3_2方法默认使用self.input_image_path,需要修改为我们的图片路径
                    # 先保存当前input_image_path
                    old_input_path = self.cutter.input_image_path
                    
                    # 设置为当前图片路径
                    self.cutter.input_image_path = image_path
                    
                    # 调用cut_to_3_2方法,传递输出文件名
                    result = self.cutter.cut_to_3_2(output_filename)
                    
                    # 恢复原始input_image_path
                    self.cutter.input_image_path = old_input_path
                    
                    if result:
                        results.append({"image": image_name, "success": True, "message": "裁剪图片生成成功"})
                    else:
                        results.append({"image": image_name, "success": False, "error": "裁剪图片生成失败"})
                except Exception as e:
                    results.append({"image": image_name, "success": False, "error": str(e)})
            
            return True, {"results": results}
        except Exception as e: 
            return False, {"error": str(e)}