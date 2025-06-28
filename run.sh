#!/bin/bash

# 确保脚本在项目根目录运行
cd "$(dirname "$0")"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 下载SAM模型权重（如果不存在）
if [ ! -f "models/sam_vit_h_4b8939.pth" ]; then
    mkdir -p models
    echo "下载SAM模型权重（约2.5GB）..."
    curl -L -o models/sam_vit_h_4b8939.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
fi

# 运行应用
export FLASK_APP=app
export FLASK_DEBUG=1
flask run