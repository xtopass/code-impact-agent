"""
安全专家Agent
负责安全风险评估和敏感信息检测
"""
import re
from typing import Dict, Any, List
from src.agents.base import BaseAgent


class SecurityExpertAgent(BaseAgent):
    """安全专家Agent"""
    
    def __init__(self):
        super().__init__(
            name="Security_Expert",
            description="评估代码变更的安全风险和潜在漏洞"
        )
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行安全分析"""
        self.logger.info(f"[{self.name}] 开始安全风险评估")
        
        diff = state.get("code_diff", "")
        
        findings = []
        vulnerabilities = []
        
        # 1. 检测硬编码凭证
        findings.extend(self._detect_hardcoded_secrets(diff))
        vulnerabilities.extend(self._find_secrets(diff))
        
        # 2. 检测注入风险
        findings.extend(self._detect_injection_risks(diff))
        
        # 3. 检测不安全操作
        findings.extend(self._detect_unsafe_operations(diff))
        
        # 4. 检测权限变更
        findings.extend(self._detect_permission_changes(diff))
        
        state["security_analysis"] = {
            "agent_name": self.name,
            "findings": findings,
            "vulnerabilities": vulnerabilities,
            "confidence": 0.92,
            "risk_level": self._assess_risk(findings, vulnerabilities)
        }
        
        self.logger.info(f"[{self.name}] 分析完成，发现 {len(findings)} 个安全风险")
        return state
    
    def _detect_hardcoded_secrets(self, diff: str) -> List[str]:
        """检测硬编码凭证"""
        findings = []
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "硬编码密码"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "硬编码密钥"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "硬编码API密钥"),
            (r'token\s*=\s*["\'][^"\']+["\']', "硬编码令牌"),
            (r'private_key\s*=\s*["\'][^"\']+["\']', "硬编码私钥"),
        ]
        
        for pattern, desc in secret_patterns:
            if re.search(pattern, diff, re.IGNORECASE):
                findings.append(f"检测到{desc}")
        
        return findings
    
    def _find_secrets(self, diff: str) -> List[Dict]:
        """查找具体的凭证位置"""
        vulnerabilities = []
        
        secret_lines = [
            ("password", r'password\s*=\s*["\']([^"\']+)["\']'),
            ("api_key", r'api[_-]?key\s*=\s*["\']([^"\']+)["\']'),
            ("secret", r'secret\s*=\s*["\']([^"\']+)["\']'),
        ]
        
        for var_name, pattern in secret_lines:
            for match in re.finditer(pattern, diff, re.IGNORECASE):
                vulnerabilities.append({
                    "type": f"hardcoded_{var_name}",
                    "severity": "high",
                    "value_preview": match.group(1)[:8] + "***" if len(match.group(1)) > 8 else match.group(1) + "***"
                })
        
        return vulnerabilities
    
    def _detect_injection_risks(self, diff: str) -> List[str]:
        """检测注入风险"""
        findings = []
        
        injection_patterns = [
            (r'eval\s*\(', "代码注入风险 (eval)"),
            (r'exec\s*\(', "代码执行风险 (exec)"),
            (r'os\.system\s*\(', "系统命令注入风险"),
            (r'executing.*sql.*f["\']', "SQL注入风险 (f-string)"),
            (r'format\s*\(.*\{.*\}', "字符串格式化注入风险"),
            (r'requests\.get.*f["\']', "URL注入风险"),
        ]
        
        for pattern, desc in injection_patterns:
            if re.search(pattern, diff, re.IGNORECASE):
                findings.append(desc)
        
        return findings
    
    def _detect_unsafe_operations(self, diff: str) -> List[str]:
        """检测不安全操作"""
        findings = []
        
        unsafe_patterns = [
            (r'chmod\s*\(.*0o?777', "危险的文件权限设置"),
            (r'sudo\s+', "特权操作变更"),
            (r'mkdir\s+-p', "目录创建变更"),
            (r'rm\s+-rf', "强制删除操作"),
            (r'pickle\.loads?', "反序列化安全风险"),
        ]
        
        for pattern, desc in unsafe_patterns:
            if re.search(pattern, diff, re.IGNORECASE):
                findings.append(desc)
        
        return findings
    
    def _detect_permission_changes(self, diff: str) -> List[str]:
        """检测权限相关变更"""
        findings = []
        
        permission_keywords = [
            "rbac", "role", "permission", "authorization",
            "access_control", "acl", "privilege"
        ]
        
        for keyword in permission_keywords:
            if keyword in diff.lower():
                findings.append(f"检测到权限相关变更: {keyword}")
                break
        
        return findings
    
    def _assess_risk(self, findings: List[str], vulnerabilities: List[Dict]) -> str:
        """评估风险等级"""
        high_severity = sum(1 for v in vulnerabilities if v.get("severity") == "high")
        
        if high_severity > 0 or len(findings) > 5:
            return "critical"
        elif len(findings) > 2:
            return "high"
        elif len(findings) > 0:
            return "medium"
        return "low"
