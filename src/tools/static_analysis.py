"""
静态分析工具
基于Semgrep的规则引擎
"""
import subprocess
import json
from typing import List, Dict, Optional
from pathlib import Path


class SemgrepTool:
    """Semgrep静态分析工具"""
    
    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = rules_path
    
    def run_scan(self, target: str, rules: Optional[List[str]] = None) -> Dict:
        """运行Semgrep扫描"""
        cmd = ["semgrep", "--json"]
        
        if self.rules_path:
            cmd.extend(["--config", self.rules_path])
        
        if rules:
            for rule in rules:
                cmd.extend(["--config", rule])
        
        cmd.append(target)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"errors": [result.stderr]}
        except json.JSONDecodeError:
            return {"parse_error": "Failed to parse semgrep output"}
        except FileNotFoundError:
            return {"error": "semgrep not found, please install: pip install semgrep"}
    
    def extract_findings(self, scan_result: Dict) -> List[Dict]:
        """提取扫描发现"""
        findings = []
        
        matches = scan_result.get("results", [])
        for match in matches:
            findings.append({
                "rule_id": match.get("rule_id", ""),
                "severity": match.get("severity", ""),
                "message": match.get("extra", {}).get("message", ""),
                "file": match.get("path", ""),
                "line": match.get("start", {}).get("line", 0),
                "code": match.get("extra", {}).get("lines", "")
            })
        
        return findings


class DependencyAnalyzer:
    """依赖分析器"""
    
    @staticmethod
    def analyze_python(file_path: str) -> List[str]:
        """分析Python依赖"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 匹配 import 语句
            import_pattern = r'^\s*import\s+(\w+)'
            from_import_pattern = r'^\s*from\s+(\w+[\.\w]*)\s+import'
            
            for line in content.split('\n'):
                match = __import__('re').match(import_pattern, line)
                if match:
                    imports.append(match.group(1))
                
                match = __import__('re').match(from_import_pattern, line)
                if match:
                    imports.append(match.group(1).split('.')[0])
        
        except (IOError, UnicodeDecodeError):
            pass
        
        return list(set(imports))
    
    @staticmethod
    def analyze_javascript(file_path: str) -> List[str]:
        """分析JavaScript依赖"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # ES6 import
            es6_pattern = r'import\s+.*\s+from\s+[\'"](.+?)[\'"]'
            # CommonJS require
            require_pattern = r'require\s*\(\s*[\'"](.+?)[\'"]\s*\)'
            
            import re
            for pattern in [es6_pattern, require_pattern]:
                matches = re.findall(pattern, content)
                imports.extend(matches)
        
        except (IOError, UnicodeDecodeError):
            pass
        
        return list(set(imports))
    
    @staticmethod
    def analyze_puppet(file_path: str) -> List[Dict]:
        """分析Puppet依赖"""
        resources = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            import re
            # 匹配资源定义
            resource_pattern = r'(package|service|file|exec|class|define)\s+"([^"]+)"'
            
            for match in re.finditer(resource_pattern, content):
                resources.append({
                    "type": match.group(1),
                    "title": match.group(2)
                })
        
        except (IOError, UnicodeDecodeError):
            pass
        
        return resources
