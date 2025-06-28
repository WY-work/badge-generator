FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 下载SAM模型权重
RUN mkdir -p models \
    && curl -L -o models/sam_vit_h_4b8939.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth

# 复制应用代码
COPY . .

# 设置环境变量
ENV FLASK_APP=app
ENV FLASK_ENV=development

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["flask", "run", "--host=0.0.0.0"]