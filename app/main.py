import os
import base64
import torch
import numpy as np
from flask import Blueprint, render_template, request, jsonify
from PIL import Image, ImageFilter
from segment_anything import sam_model_registry, SamPredictor

main_bp = Blueprint('main', __name__)

# 徽章类型配置
badge_types = {
    'metal': {
        'name': '马口铁徽章',
        'sizes': [25, 38, 50, 58, 70, 85],
        'edge_color': '#9E9E9E',
        'edge_width': 2,
        'shine_effect': True
    },
    'acrylic': {
        'name': '亚克力徽章',
        'sizes': [58],  # 默认尺寸
        'edge_color': '#FFFFFF',
        'edge_width': 3,
        'transparent_edge': True,
        'expand_options': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
}

# 初始化SAM模型
def init_sam_model():
    model_type = "vit_h"
    sam_checkpoint = "models/sam_vit_h_4b8939.pth"
    
    if not os.path.exists(sam_checkpoint):
        raise FileNotFoundError(f"SAM模型权重文件不存在: {sam_checkpoint}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam.to(device=device)
    return SamPredictor(sam)

# 延迟初始化模型
predictor = None

@main_bp.before_app_first_request
def load_model():
    global predictor
    try:
        predictor = init_sam_model()
    except Exception as e:
        print(f"Error loading SAM model: {e}")
        # 可以考虑使用备选模型或回退方案

@main_bp.route('/')
def index():
    return render_template('index.html', badge_types=badge_types)

@main_bp.route('/generate', methods=['POST'])
def generate():
    global predictor
    
    # 检查模型是否加载
    if predictor is None:
        try:
            predictor = init_sam_model()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f"无法加载抠图模型: {str(e)}"
            }), 500
    
    # 处理上传的图片
    if 'image' not in request.files:
        return jsonify({
            'success': False,
            'error': '未上传图片'
        }), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': '空文件名'
        }), 400
    
    # 保存上传的图片
    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)
    image_path = os.path.join(upload_dir, file.filename)
    file.save(image_path)
    
    try:
        # 获取参数
        badge_type = request.form.get('badge_type', 'metal')
        size = int(request.form.get('size', 58))
        expand = int(request.form.get('expand', 3))
        
        # 处理图片
        image = Image.open(image_path).convert("RGB")
        
        # 使用SAM模型进行精细抠图
        predictor.set_image(np.array(image))
        
        # 默认使用中心点作为提示
        input_point = np.array([[image.width // 2, image.height // 2]])
        input_label = np.array([1])
        
        masks, scores, logits = predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=True,
        )
        
        # 选择最高分数的掩码
        best_mask = masks[np.argmax(scores)]
        
        # 创建带透明通道的图像
        mask_image = Image.fromarray((best_mask * 255).astype(np.uint8)).convert("L")
        result = Image.new("RGBA", image.size)
        result.paste(image, mask=mask_image)
        
        # 生成徽章效果
        badge = create_badge(result, badge_type, size, expand)
        
        # 保存结果
        output_dir = 'outputs'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"badge_{file.filename}")
        badge.save(output_path, "PNG")
        
        # 转换为Base64以便前端显示
        with open(output_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode("ascii")
        
        return jsonify({
            'success': True,
            'badge_image': f"data:image/png;base64,{img_data}",
            'badge_type': badge_type,
            'size': size,
            'expand': expand
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"生成徽章失败: {str(e)}"
        }), 500

def create_badge(image, badge_type, size, expand=3):
    """创建徽章效果"""
    # 计算缩放比例
    width, height = image.size
    max_dim = max(width, height)
    scale = (size - (badge_types[badge_type]['edge_width'] * 2)) / max_dim
    
    # 调整图像大小
    new_width = int(width * scale)
    new_height = int(height * scale)
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # 创建徽章背景
    badge = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    badge_center = (size // 2, size // 2)
    image_position = (badge_center[0] - new_width // 2, badge_center[1] - new_height // 2)
    
    # 粘贴图像
    badge.paste(resized_image, image_position, resized_image)
    
    if badge_type == 'metal':
        # 马口铁徽章效果
        draw_metal_effect(badge, size)
    elif badge_type == 'acrylic':
        # 亚克力徽章效果
        draw_acrylic_effect(badge, size, expand)
    
    return badge

def draw_metal_effect(badge, size):
    """添加马口铁徽章效果"""
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(badge)
    
    # 绘制金属边框
    edge_width = badge_types['metal']['edge_width']
    draw.ellipse(
        (edge_width, edge_width, size - edge_width, size - edge_width),
        outline=badge_types['metal']['edge_color'],
        width=edge_width
    )
    
    # 添加金属光泽效果
    if badge_types['metal']['shine_effect']:
        shine_radius = size // 3
        shine_center = (size // 3, size // 3)
        
        # 创建光泽渐变
        shine = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        shine_draw = ImageDraw.Draw(shine)
        
        for i in range(shine_radius):
            opacity = int(150 * (1 - i / shine_radius))
            shine_draw.ellipse(
                (shine_center[0] - i, shine_center[1] - i, 
                 shine_center[0] + i, shine_center[1] + i),
                outline=(255, 255, 255, opacity),
                width=1
            )
        
        # 合并光泽效果
        badge.paste(shine, mask=shine.split()[3])

def draw_acrylic_effect(badge, size, expand):
    """添加亚克力徽章效果"""
    from PIL import ImageDraw
    
    draw = ImageDraw.Draw(badge)
    
    # 创建扩展的透明边缘
    if badge_types['acrylic']['transparent_edge']:
        # 扩展边缘的大小
        edge_size = size + (expand * 2)
        
        # 创建更大的透明画布
        expanded_badge = Image.new("RGBA", (edge_size, edge_size), (255, 255, 255, 0))
        
        # 计算位置并粘贴原徽章
        position = (expand, expand)
        expanded_badge.paste(badge, position, badge)
        
        # 创建渐变边缘
        draw = ImageDraw.Draw(expanded_badge)
        for i in range(expand):
            opacity = int(255 * (1 - i / expand))
            draw.ellipse(
                (i, i, edge_size - i, edge_size - i),
                outline=(255, 255, 255, opacity),
                width=1
            )
        
        # 调整回原大小
        badge.paste(expanded_badge.resize((size, size), Image.LANCZOS), mask=expanded_badge.resize((size, size), Image.LANCZOS).split()[3])
    
    # 绘制亚克力边缘
    edge_width = badge_types['acrylic']['edge_width']
    draw.ellipse(
        (edge_width, edge_width, size - edge_width, size - edge_width),
        outline=badge_types['acrylic']['edge_color'],
        width=edge_width
    )