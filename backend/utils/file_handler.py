"""文件处理工具"""
import os
import re
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from config import settings


def validate_file_upload(file: UploadFile) -> bool:
    """验证上传文件"""
    # 检查文件扩展名
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_extension}"
        )
    
    # 检查文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置到文件开头
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB"
        )
    
    return True


def secure_filename(filename: str) -> str:
    """安全的文件名处理"""
    # 移除危险字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # 限制文件名长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def save_upload_file(file: UploadFile, save_path: str) -> str:
    """保存上传的文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # 保存文件
        with open(save_path, "wb") as f:
            content = file.file.read()
            f.write(content)
        
        return save_path
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败: {str(e)}"
        )

