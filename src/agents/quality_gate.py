"""
质量守门员Agent
负责最终输出的质量检查
"""
from typing import Dict, Any, List
from src.agents.base import BaseAgent


class QualityGateAgent(BaseAgent):
    """质量守门员Agent"""
    
    def __init__(self):
        super().__init__(
            name="Quality_Gate",
            description="检查分析报告的完整性和准确性"
        )
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量检查"""
        self.logger.info(f"[{self.name}] 执行质量检查")
        
        issues = []
        
        # 1. 检查报告完整性
        issues.extend(self._check_completeness(state))
        
        # 2. 检查证据链
        issues.extend(self._check_evidence_chain(state))
        
        # 3. 检查置信度阈值
        issues.extend(self._check_confidence_threshold(state))
        
        # 4. 检查风险等级校准
        issues.extend(self._check_risk_calibration(state))
        
        state["quality_check"] = {
            "issues": issues,
            "passed": len(issues) == 0,
            "issues_count": len(issues),
            "summary": self._generate_summary(issues)
        }
        
        self.logger.info(f"[{self.name}] 检查完成，发现 {len(issues)} 个问题")
        return state
    
    def _check_completeness(self, state: Dict[str, Any]) -> List[str]:
        """检查报告完整性"""
        issues = []
        
        required_sections = {
            "code_analysis": "代码层分析",
            "api_analysis": "接口层分析", 
            "security_analysis": "安全风险评估"
        }
        
        for key, name in required_sections.items():
            if key not in state or not state[key]:
                issues.append(f"缺少{name}部分")
            elif not state[key].get("findings"):
                issues.append(f"{name}部分为空，可能分析失败")
        
        return issues
    
    def _check_evidence_chain(self, state: Dict[str, Any]) -> List[str]:
        """检查证据链完整性"""
        issues = []
        
        # 检查是否有结论但无证据
        for agent_key in ["code_analysis", "security_analysis"]:
            if agent_key in state and state[agent_key]:
                findings = state[agent_key].get("findings", [])
                if findings and not state.get("code_diff"):
                    issues.append(f"{agent_key} 有发现但无diff证据")
        
        return issues
    
    def _check_confidence_threshold(self, state: Dict[str, Any]) -> List[str]:
        """检查置信度阈值"""
        issues = []
        
        min_confidence = 0.5
        
        for agent_key in ["code_analysis", "api_analysis", "security_analysis"]:
            if agent_key in state and state[agent_key]:
                confidence = state[agent_key].get("confidence", 0)
                if confidence < min_confidence:
                    issues.append(f"{agent_key} 置信度过低 ({confidence:.2f} < {min_confidence})")
        
        return issues
    
    def _check_risk_calibration(self, state: Dict[str, Any]) -> List[str]:
        """检查风险等级校准"""
        issues = []
        
        # 检查是否存在明显的不合理风险等级
        code = state.get("code_analysis", {})
        security = state.get("security_analysis", {})
        
        if code.get("findings") and security.get("risk_level") == "low":
            if len(code.get("findings", [])) > 3:
                issues.append("代码发现较多但安全风险评估过低，可能漏检")
        
        return issues
    
    def _generate_summary(self, issues: List[str]) -> str:
        """生成检查摘要"""
        if not issues:
            return "质量检查通过，报告完整可信"
        
        summary = f"发现 {len(issues)} 个质量问题:\n"
        for i, issue in enumerate(issues, 1):
            summary += f"{i}. {issue}\n"
        
        return summary
