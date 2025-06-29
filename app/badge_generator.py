import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def generate_metal_badge(image, size, edge_width=2, edge_color="#9E9E9E"):
    """生成马口铁徽章效果"""
    # 创建圆形掩码
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    
    # 调整图片大小并应用掩码
    image = image.resize((size, size), Image.LANCZOS)
    image.putalpha(mask)
    
    # 创建徽章背景
    badge = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    
    # 添加金属边缘
    draw = ImageDraw.Draw(badge)
    draw.ellipse((edge_width, edge_width, size-edge_width, size-edge_width), 
                outline=edge_color, width=edge_width)
    
    # 添加高光效果
    highlight = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(highlight)
    highlight_size = int(size * 0.6)
    draw.ellipse((size-highlight_size, 0, size, highlight_size), 
                fill=(255, 255, 255, 100))
    
    # 合并所有图层
    badge.paste(image, (0, 0), image)
    badge = Image.alpha_composite(badge, highlight)
    
    return badge

def generate_acrylic_badge(image, size, edge_width=3, edge_color="#FFFFFF", expand=3):
    """生成亚克力徽章效果"""
    # 创建扩展的透明边缘
    new_size = size + expand * 2
    mask = Image.new('L', (new_size, new_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, new_size, new_size), fill=255)
    
    # 调整图片大小
    image = image.resize((size, size), Image.LANCZOS)
    
    # 创建带透明边缘的徽章
    badge = Image.new('RGBA', (new_size, new_size), (255, 255, 255, 0))
    badge.paste(image, (expand, expand), image)
    badge.putalpha(mask)
    
    # 添加亚克力边缘
    draw = ImageDraw.Draw(badge)
    draw.ellipse((edge_width, edge_width, new_size-edge_width, new_size-edge_width), 
                outline=edge_color, width=edge_width)
    
    # 添加高光效果
    highlight = Image.new('RGBA', (new_size, new_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(highlight)
    highlight_size = int(new_size * 0.6)
    draw.ellipse((new_size-highlight_size, 0, new_size, highlight_size), 
                fill=(255, 255, 255, 80))
    
    # 合并所有图层
    badge = Image.alpha_composite(badge, highlight)
    
    # 应用轻微模糊以获得更真实的亚克力效果
    badge = badge.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return badge