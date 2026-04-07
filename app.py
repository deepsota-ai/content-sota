from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from backend.controller.load.load_controller import LoadController
from backend.controller.content.content_controller import ContentController
from backend.controller.cover.cover_controller import CoverController
from backend.controller.publish.publish_controller import PublishController
from backend.controller.clean.clean_controller import CleanController

app = Flask(__name__)
CORS(app)

frontend_path = os.path.join((os.path.dirname(os.path.abspath(__file__))), 'frontend')

# 主页路由
@app.route('/')
def index():
    return send_from_directory(os.path.join(frontend_path, 'html'), 'index.html')

# 静态文件路由 - 统一处理所有静态资源
@app.route('/<path:filename>')
def serve_static(filename):
    if filename.startswith('css/') or filename.startswith('js/') or filename.startswith('fonts/'):
        return send_from_directory(frontend_path, filename)
    return send_from_directory(os.path.join(frontend_path, 'html'), filename)

# 数据文件路由 - 处理data文件夹下的资源
@app.route('/data/<path:filename>')
def serve_data(filename):
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    return send_from_directory(data_path, filename)

# 加载素材API接口
@app.route('/api/load-material', methods=['GET'])
def load_material():
    controller = LoadController()
    success, data = controller.load_material()
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 可用模型列表API接口（从 Gemini API 动态获取）
@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        import os
        from dotenv import load_dotenv
        from google import genai
        load_dotenv()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # 拉取所有模型，过滤出支持 generateContent 的 gemini 模型
        all_models = client.models.list()
        models = []
        seen = set()
        for m in all_models:
            name = m.name  # 格式如 "models/gemini-2.0-flash"
            model_id = name.replace("models/", "")
            if not model_id.startswith("gemini-"):
                continue
            if "generateContent" not in (m.supported_actions or []):
                continue
            if model_id in seen:
                continue
            seen.add(model_id)
            models.append({"id": model_id, "name": model_id})
        # 按名称排序，稳定显示
        models.sort(key=lambda x: x["id"])
        return jsonify({"success": True, "models": models}), 200
    except Exception as e:
        # 降级为静态列表
        fallback = [
            {"id": "gemini-2.5-flash-preview-05-20", "name": "Gemini 2.5 Flash"},
            {"id": "gemini-2.0-flash",               "name": "Gemini 2.0 Flash"},
            {"id": "gemini-1.5-flash",               "name": "Gemini 1.5 Flash"},
        ]
        return jsonify({"success": True, "models": fallback, "warning": str(e)}), 200

# 生成内容API接口
@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    # 获取请求参数
    material_contents = request.json.get('material_contents', [])
    # 前端不再传递 title_tips 和 hook_tips，由后端自动读取
    generate_type = request.json.get('generate_type', 'both')  # 生成类型，默认生成标题和钩子
    model_name = request.json.get('model_name')  # 可选，前端选择的模型
    
    # 如果是单个素材，兼容旧格式
    if not material_contents and request.json.get('material_content'):
        material_contents = [request.json.get('material_content')]
    
    if not material_contents:
        return jsonify({
            'success': False,
            'error': '未提供素材内容'
        }), 400
    
    controller = ContentController()
    results = []
    
    print(f"收到素材数量: {len(material_contents)}")
    print(f"生成类型: {generate_type}")
    
    # 循环处理每个素材内容
    for i, material_content in enumerate(material_contents):
        print(f"处理素材 {i+1}")
        print(f"素材内容: {material_content[:50]}...")
        
        # 调用 controller
        success, data = controller.generate_content(material_content, generate_type=generate_type, model_name=model_name)
        if success:
            print(f"素材 {i+1} 生成成功")
            
            # 根据生成类型返回不同的结果
            result_item = {
                'material_index': i + 1,
                'titles': data['data']['titles'],
                'hooks': data['data']['hooks'],
                'content': data['data'].get('content', '')
            }
            
            results.append(result_item)
        else:
            print(f"素材 {i+1} 生成失败: {data['error']}")
            results.append({
                'material_index': i + 1,
                'error': data['error']
            })
    
    return jsonify({
        'success': True,
        'data': {
            'results': results
        }
    }), 200


# 读取 hashtag 配置
@app.route('/api/hashtags', methods=['GET'])
def get_hashtags():
    from backend.controller.publish.publish_controller import PublishController
    tags = PublishController()._read_hashtags()
    return jsonify({'success': True, 'hashtags': tags}), 200

# 单篇创作：从提示词生成草稿API接口
@app.route('/api/generate-drafts', methods=['POST'])
def generate_drafts():
    user_prompt = request.json.get('user_prompt', '').strip()
    model_name = request.json.get('model_name')
    if not user_prompt:
        return jsonify({'success': False, 'error': '未提供创作需求'}), 400
    controller = ContentController()
    success, data = controller.generate_drafts(user_prompt, model_name=model_name)
    return jsonify(data), 200 if success else 400

# 获取toPs图片列表API接口
@app.route('/api/get_to_ps_images', methods=['GET'])
def get_to_ps_images():
    controller = LoadController()
    success, data = controller.get_to_ps_images()
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 获取蒙版图片列表API接口
@app.route('/api/get_mask_images', methods=['GET'])
def get_mask_images():
    controller = LoadController()
    success, data = controller.get_mask_images()
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 获取裁剪图片列表API接口
@app.route('/api/get_cropped_images', methods=['GET'])
def get_cropped_images():
    controller = LoadController()
    success, data = controller.get_cropped_images()
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 生成蒙版封面API接口
@app.route('/api/generate-mask-cover', methods=['POST'])
def generate_mask_cover():
    controller = CoverController()
    
    # 支持循环调用，根据前端需求可以传递图片列表
    images = request.json.get('images', [])
    
    # 调用controller的方法生成蒙版封面（controller内部会处理循环）
    success, data = controller.generate_cover_with_mask(images)
    
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 生成裁剪图片API接口
@app.route('/api/generate-cropped-image', methods=['POST'])
def generate_cropped_image():
    controller = CoverController()
    
    # 支持循环调用，根据前端需求可以传递图片列表
    images = request.json.get('images', [])
    aspect_ratio = request.json.get('aspect_ratio', 'free')
    
    # 调用controller的方法生成裁剪图片（controller内部会处理循环）
    success, data = controller.generate_cropped_image(images, aspect_ratio)
    
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 获取发布文件夹列表API接口
@app.route('/api/publish/folders', methods=['GET'])
def get_publish_folders():
    controller = PublishController()
    date_folder = request.args.get('date') # 获取日期参数
    success, data = controller.get_publish_folders(date_folder)
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 整理内容API接口
@app.route('/api/organize-content', methods=['POST'])
def organize_content():
    controller = PublishController()
    materials = request.json.get('materials', [])
    
    success, data = controller.organize_content(materials)
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 发布内容API接口
@app.route('/api/publish/<path:folder_name>', methods=['POST'])
def publish_content(folder_name):
    controller = PublishController()
    success, data = controller.publish_content(folder_name)
    if success:
        return jsonify(data), 200
    else:
        return jsonify(data), 400

# 保存编辑后图片API接口
@app.route('/api/save-edited-image', methods=['POST'])
def save_edited_image():
    try:
        # 获取请求数据
        image_data = request.json.get('imageData')
        filename = request.json.get('filename')
        date_param = request.json.get('date')           # 可选，日期字符串
        folder_name = request.json.get('folder_name')   # 可选，直接指定素材文件夹名（如"素材_1"）

        if not image_data or not filename:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        # 处理图片数据，移除base64前缀
        if image_data.startswith('data:image/png;base64,'):
            image_data = image_data.replace('data:image/png;base64,', '')
        elif image_data.startswith('data:image/jpeg;base64,'):
            image_data = image_data.replace('data:image/jpeg;base64,', '')
        elif ',' in image_data:
            image_data = image_data.split(',', 1)[1]

        # 解码base64数据
        import base64
        image_bytes = base64.b64decode(image_data)

        # 确定日期
        if date_param:
            date_str = date_param
        else:
            from datetime import datetime
            now = datetime.now()
            date_str = f"{now.year}.{now.month}.{now.day}"

        # 确定素材文件夹：优先使用 folder_name 参数，否则按 filename 映射
        if folder_name:
            material_folder_name = folder_name
        else:
            file_basename = os.path.splitext(filename)[0]
            material_folder_name = f"素材_{file_basename}"

        publish_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'publish', date_str, material_folder_name)
        
        # 确保目标文件夹存在
        if not os.path.exists(publish_dir):
            os.makedirs(publish_dir)
            
        # 确定目标文件名：filename 参数若是纯数字（如 "1","2","3"），保存为 {n}.jpg；
        # 否则使用原文件名（保持旧行为，封面页传入的 filename 通常为原图文件名）
        file_basename = os.path.splitext(filename)[0]
        if file_basename.isdigit():
            target_filename = f"{file_basename}.jpg"
        else:
            target_filename = "1.jpg"
        image_path = os.path.join(publish_dir, target_filename)

        with open(image_path, 'wb') as f:
            f.write(image_bytes)

        return jsonify({'success': True, 'message': '图片保存成功', 'file_path': image_path}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 读取/更新素材内容 API
@app.route('/api/publish/content', methods=['GET', 'POST'])
def publish_content_edit():
    from backend.controller.publish.publish_controller import PublishController
    controller = PublishController()
    if request.method == 'GET':
        path = request.args.get('path', '')
        success, data = controller.get_content(path)
        return jsonify(data), 200 if success else 400
    else:
        body = request.json or {}
        path = body.get('path', '')
        title = body.get('title', '')
        desc = body.get('desc', '')
        success, data = controller.update_content(path, title, desc)
        return jsonify(data), 200 if success else 400

# 小红书封面自动完善API
@app.route('/api/publish/xhs_perfect/<path:folder_name>', methods=['POST'])
def xhs_perfect(folder_name):
    try:
        from backend.service.publish.ibeike_extension import xhs_perfect_cover
        success = xhs_perfect_cover(folder_name)
        
        if success:
            return jsonify({'success': True, 'message': '小红书封面上传指令已发送'}), 200
        else:
            return jsonify({'success': False, 'message': '操作失败，请检查浏览器是否已打开且处于发布编辑状态'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 清理数据API接口
@app.route('/api/clean-data', methods=['POST'])
def clean_data():
    controller = CleanController()
    targets = request.json.get('targets', [])
    success, data = controller.clean_all(targets)
    if success:
        return jsonify({'success': True, 'data': data}), 200
    else:
        return jsonify({'success': False, 'error': str(data)}), 500

if __name__ == '__main__':
    print("Starting Instagram Robot Service...")
    print("\n服务启动在 http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True)