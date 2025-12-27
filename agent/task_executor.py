"""任务执行器模块"""
import asyncio
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Awaitable

# 支持直接运行和作为模块运行
try:
    from .utils import ensure_dir
except ImportError:
    from utils import ensure_dir


class TaskExecutor:
    """任务执行器类"""
    
    def __init__(
        self,
        work_dir: Path,
        on_log: Optional[Callable[[str, str, str], Awaitable[None]]] = None,
        logger=None
    ):
        """
        初始化任务执行器
        
        Args:
            work_dir: 工作目录
            on_log: 日志回调函数 (task_id, level, message)
            logger: 日志器
        """
        self.work_dir = work_dir
        self.on_log = on_log
        self.logger = logger
        self.tasks: Dict[str, subprocess.Popen] = {}  # task_id -> process
        self.task_logs: Dict[str, Path] = {}  # task_id -> log_file_path
    
    def _get_task_dir(self, task_id: str) -> Path:
        """
        获取任务目录
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务目录路径
        """
        return self.work_dir / "tasks" / task_id
    
    def _get_task_log_file(self, task_id: str) -> Path:
        """
        获取任务日志文件路径
        
        Args:
            task_id: 任务ID
        
        Returns:
            日志文件路径
        """
        log_dir = self.work_dir / "logs" / "tasks"
        ensure_dir(log_dir)
        return log_dir / f"{task_id}.log"
    
    async def _log(self, task_id: str, level: str, message: str) -> None:
        """
        记录日志
        
        Args:
            task_id: 任务ID
            level: 日志级别
            message: 日志内容
        """
        # 写入日志文件
        log_file = self._get_task_log_file(task_id)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] [{level.upper()}] {message}\n")
        except Exception as e:
            if self.logger:
                self.logger.error(f"写入任务日志失败: {e}")
        
        # 调用回调函数
        if self.on_log:
            try:
                await self.on_log(task_id, level, message)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"日志回调函数执行失败: {e}")
    
    async def execute_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task_config: 任务配置字典，包含:
                - task_id: 任务ID
                - command: 要执行的命令
                - work_dir: 任务工作目录（可选）
                - env_vars: 环境变量字典（可选）
                - timeout: 超时时间（秒，可选）
        
        Returns:
            任务执行结果字典
        """
        task_id = task_config.get("task_id")
        command = task_config.get("command")
        task_work_dir = task_config.get("work_dir")
        env_vars = task_config.get("env_vars", {})
        timeout = task_config.get("timeout", 3600)
        
        if not task_id or not command:
            raise ValueError("task_id和command是必需的")
        
        start_time = datetime.now()
        
        # 创建任务目录
        if task_work_dir:
            task_dir = Path(task_work_dir).expanduser().resolve()
        else:
            task_dir = self._get_task_dir(task_id)
        
        ensure_dir(task_dir)
        
        # 准备环境变量
        env = os.environ.copy()
        env.update(env_vars)
        
        # 准备命令
        if isinstance(command, str):
            # 如果是字符串，按shell方式执行
            shell = True
            cmd = command
        else:
            # 如果是列表，直接执行
            shell = False
            cmd = command
        
        await self._log(task_id, "info", f"开始执行任务: {command}")
        await self._log(task_id, "info", f"工作目录: {task_dir}")
        
        try:
            # 启动进程
            process = subprocess.Popen(
                cmd,
                shell=shell,
                cwd=str(task_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并stderr到stdout
                universal_newlines=True,
                bufsize=1
            )
            
            self.tasks[task_id] = process
            
            # 实时读取输出
            output_lines = []
            try:
                # 使用asyncio.wait_for实现超时
                async def read_output():
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            if process.poll() is not None:
                                break
                            await asyncio.sleep(0.1)
                            continue
                        
                        line = line.rstrip()
                        output_lines.append(line)
                        await self._log(task_id, "info", line)
                
                await asyncio.wait_for(read_output(), timeout=timeout)
            
            except asyncio.TimeoutError:
                # 超时，终止进程
                await self._log(task_id, "error", f"任务执行超时（{timeout}秒），正在终止...")
                process.terminate()
                
                # 等待进程结束，如果5秒后还没结束，强制杀死
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                output = "\n".join(output_lines)
                
                return {
                    "task_id": task_id,
                    "status": "timeout",
                    "exit_code": -1,
                    "output": output,
                    "error": f"任务执行超时（{timeout}秒）",
                    "duration": duration
                }
            
            # 等待进程结束
            exit_code = process.wait()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 读取剩余输出
            remaining_output = process.stdout.read()
            if remaining_output:
                lines = remaining_output.rstrip().split("\n")
                for line in lines:
                    if line:
                        output_lines.append(line)
                        await self._log(task_id, "info", line)
            
            output = "\n".join(output_lines)
            
            # 确定状态
            if exit_code == 0:
                status = "success"
                error = None
            else:
                status = "failed"
                error = f"进程退出码: {exit_code}"
            
            await self._log(
                task_id,
                "info",
                f"任务执行完成，状态: {status}，退出码: {exit_code}，耗时: {duration:.2f}秒"
            )
            
            return {
                "task_id": task_id,
                "status": status,
                "exit_code": exit_code,
                "output": output,
                "error": error,
                "duration": duration
            }
        
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            error_msg = f"任务执行出错: {str(e)}"
            await self._log(task_id, "error", error_msg)
            
            return {
                "task_id": task_id,
                "status": "error",
                "exit_code": -1,
                "output": "\n".join(output_lines) if output_lines else "",
                "error": error_msg,
                "duration": duration
            }
        
        finally:
            # 清理
            if task_id in self.tasks:
                del self.tasks[task_id]
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否成功取消
        """
        if task_id not in self.tasks:
            if self.logger:
                self.logger.warning(f"任务 {task_id} 不存在或已完成")
            return False
        
        process = self.tasks[task_id]
        
        try:
            await self._log(task_id, "warning", "收到取消任务指令，正在终止...")
            
            # 终止进程
            process.terminate()
            
            # 等待进程结束，如果5秒后还没结束，强制杀死
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            await self._log(task_id, "info", "任务已取消")
            
            # 清理
            del self.tasks[task_id]
            
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"取消任务失败: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态 (running/completed/not_found)
        """
        if task_id not in self.tasks:
            return "not_found"
        
        process = self.tasks[task_id]
        if process.poll() is None:
            return "running"
        else:
            return "completed"

