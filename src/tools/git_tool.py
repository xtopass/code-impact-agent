"""
工具层：Git操作
"""
import subprocess
import re
from typing import List, Dict, Optional
from datetime import datetime


class GitTool:
    """Git操作工具类"""
    
    @staticmethod
    def get_diff(target: str, staged: bool = False) -> str:
        """获取文件diff"""
        cmd = ["git", "diff"]
        if staged:
            cmd.append("--cached")
        cmd.append(target)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def get_staged_diff(target: str) -> str:
        """获取暂存区diff"""
        return GitTool.get_diff(target, staged=True)
    
    @staticmethod
    def get_changed_files(base: str = "HEAD", head: str = "HEAD") -> List[str]:
        """获取变更文件列表"""
        result = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            capture_output=True, text=True
        )
        files = [f for f in result.stdout.strip().split('\n') if f]
        return files
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict:
        """获取文件Git信息"""
        info = {
            "path": file_path,
            "exists": False,
            "size": 0,
            "modified": None,
            "last_commit": None
        }
        
        import os
        if os.path.exists(file_path):
            info["exists"] = True
            info["size"] = os.path.getsize(file_path)
            info["modified"] = datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).isoformat()
            
            # 获取最后提交信息
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci", file_path],
                capture_output=True, text=True
            )
            if result.stdout:
                info["last_commit"] = result.stdout.strip()
        
        return info
    
    @staticmethod
    def get_commit_history(file_path: str, limit: int = 10) -> List[Dict]:
        """获取文件提交历史"""
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--format=%H|%ai|%s", file_path],
            capture_output=True, text=True
        )
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                parts = line.split('|')
                commits.append({
                    "hash": parts[0],
                    "date": parts[1],
                    "message": parts[2] if len(parts) > 2 else ""
                })
        
        return commits


class FileTool:
    """文件操作工具类"""
    
    @staticmethod
    def read_file(file_path: str, max_lines: int = 1000) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                if len(lines) > max_lines:
                    return '\n'.join(lines[:max_lines]) + f"\n... (截断，共{len(lines)}行)"
                return content
        except (IOError, UnicodeDecodeError):
            return None
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名"""
        import os
        _, ext = os.path.splitext(file_path)
        return ext.lower()
    
    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """判断是否为文本文件"""
        text_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', 
                          '.json', '.yaml', '.yml', '.md', '.txt', '.xml',
                          '.html', '.css', '.scss', '.less', '.sh', '.bat',
                          '.pp', '.erb', '.ejs']
        return FileTool.get_file_extension(file_path) in text_extensions
