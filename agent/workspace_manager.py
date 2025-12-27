"""工作空间管理模块 - 处理文件系统操作"""
import os
import shutil
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class WorkspaceManager:
    """工作空间管理器"""
    
    def __init__(self, work_dir: Path):
        """
        初始化工作空间管理器
        
        Args:
            work_dir: 工作目录路径
        """
        self.work_dir = work_dir
    
    def _get_absolute_path(self, relative_path: str) -> Path:
        """
        获取绝对路径（相对于工作目录）
        
        Args:
            relative_path: 相对路径
            
        Returns:
            绝对路径
        """
        # 规范化路径，防止路径遍历攻击
        normalized = os.path.normpath(relative_path)
        # 移除开头的斜杠
        if normalized.startswith('/'):
            normalized = normalized[1:]
        # 如果路径包含..，则拒绝
        if '..' in normalized.split(os.sep):
            raise ValueError(f"不允许访问工作目录外的路径: {relative_path}")
        
        absolute_path = self.work_dir / normalized
        # 确保路径在工作目录内
        try:
            absolute_path.resolve().relative_to(self.work_dir.resolve())
        except ValueError:
            raise ValueError(f"不允许访问工作目录外的路径: {relative_path}")
        
        return absolute_path
    
    def list_files(self, path: str = "") -> List[Dict[str, Any]]:
        """
        列出指定路径下的文件和文件夹
        
        Args:
            path: 相对路径，默认为工作目录根
            
        Returns:
            文件列表，每个文件包含：name, type, size, modified, path
        """
        try:
            target_path = self._get_absolute_path(path) if path else self.work_dir
            
            if not target_path.exists():
                raise FileNotFoundError(f"路径不存在: {path}")
            
            if not target_path.is_dir():
                raise ValueError(f"路径不是目录: {path}")
            
            files = []
            for item in target_path.iterdir():
                try:
                    stat = item.stat()
                    file_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": str(item.relative_to(self.work_dir))
                    }
                    files.append(file_info)
                except (OSError, PermissionError) as e:
                    # 跳过无法访问的文件
                    continue
            
            # 按类型和名称排序：目录在前，然后按名称排序
            files.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return files
        
        except Exception as e:
            raise Exception(f"列出文件失败: {str(e)}")
    
    def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        读取文件内容
        
        Args:
            path: 文件相对路径
            encoding: 文件编码，默认为utf-8
            
        Returns:
            包含文件内容的字典：content, encoding, size
        """
        try:
            file_path = self._get_absolute_path(path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
            
            if not file_path.is_file():
                raise ValueError(f"路径不是文件: {path}")
            
            # 检查文件大小（限制为10MB）
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:
                raise ValueError(f"文件过大（{file_size}字节），最大支持10MB")
            
            # 尝试读取文件
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试二进制读取并base64编码
                with open(file_path, 'rb') as f:
                    content_bytes = f.read()
                    content = base64.b64encode(content_bytes).decode('ascii')
                    encoding = "base64"
            
            return {
                "content": content,
                "encoding": encoding,
                "size": file_size
            }
        
        except Exception as e:
            raise Exception(f"读取文件失败: {str(e)}")
    
    def write_file(self, path: str, content: str, encoding: str = "utf-8", is_base64: bool = False) -> Dict[str, Any]:
        """
        写入文件
        
        Args:
            path: 文件相对路径
            content: 文件内容
            encoding: 文件编码，默认为utf-8
            is_base64: 内容是否为base64编码
            
        Returns:
            操作结果：success, message
        """
        try:
            file_path = self._get_absolute_path(path)
            
            # 确保父目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if is_base64:
                # 解码base64内容
                content_bytes = base64.b64decode(content)
                with open(file_path, 'wb') as f:
                    f.write(content_bytes)
            else:
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(content)
            
            return {
                "success": True,
                "message": f"文件写入成功: {path}"
            }
        
        except Exception as e:
            raise Exception(f"写入文件失败: {str(e)}")
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        删除文件或文件夹
        
        Args:
            path: 文件或文件夹相对路径
            
        Returns:
            操作结果：success, message
        """
        try:
            target_path = self._get_absolute_path(path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"路径不存在: {path}")
            
            if target_path.is_dir():
                shutil.rmtree(target_path)
                message = f"文件夹删除成功: {path}"
            else:
                target_path.unlink()
                message = f"文件删除成功: {path}"
            
            return {
                "success": True,
                "message": message
            }
        
        except Exception as e:
            raise Exception(f"删除失败: {str(e)}")
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        创建文件夹
        
        Args:
            path: 文件夹相对路径
            
        Returns:
            操作结果：success, message
        """
        try:
            dir_path = self._get_absolute_path(path)
            
            if dir_path.exists():
                raise ValueError(f"路径已存在: {path}")
            
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "message": f"文件夹创建成功: {path}"
            }
        
        except Exception as e:
            raise Exception(f"创建文件夹失败: {str(e)}")
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            path: 文件相对路径
            
        Returns:
            文件信息：name, type, size, modified, path
        """
        try:
            file_path = self._get_absolute_path(path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"路径不存在: {path}")
            
            stat = file_path.stat()
            
            return {
                "name": file_path.name,
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size if file_path.is_file() else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(file_path.relative_to(self.work_dir))
            }
        
        except Exception as e:
            raise Exception(f"获取文件信息失败: {str(e)}")

