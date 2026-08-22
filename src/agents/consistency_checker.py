"""
一致性检查器Agent
负责检查各专家分析结果的一致性
"""
from typing import Dict, Any, List
from src.agents.base import BaseAgent


class ConsistencyCheckerAgent(BaseAgent):
    """跨域一致性检查器Agent"""
    
    def __init__(self):
        super().__init__(
            name="Consistency_Checker",
            description="检查各专家分析结果的一致性和冲突"
        )
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行一致性检查"""
        self.logger.info(f"[{self.name}] 开始跨域一致性检查")
        
        conflicts = []
        
        # 1. 检查代码分析与API分析的一致性
        conflicts.extend(self._check_code_api_consistency(state))
        
        # 2. 检查代码分析与安全分析的一致性
        conflicts.extend(self._check_code_security_consistency(state))
        
        # 3. 检查API与安全分析的一致性
        conflicts.extend(self._check_api_security_consistency(state))
        
        # 4. 检查置信度一致性
        conflicts.extend(self._check_confidence_consistency(state))
        
        state["cross_domain_check"] = {
            "status": "consistent" if not conflicts else "conflicts_found",
            "conflicts": conflicts,
            "total_checks": 4,
            "passed": len(conflicts) == 0,
            "summary": self._generate_summary(conflicts)
        }
        
        self.logger.info(f"[{self.name}] 检查完成，发现 {len(conflicts)} 个冲突")
        return state
    
    def _check_code_api_consistency(self, state: Dict[str, Any]) -> List[Dict]:
        """检查代码分析与API分析的一致性"""
        conflicts = []
        
        code = state.get("code_analysis")
        api = state.get("api_analysis")
        
        if code and api:
            # 大变更但未检测API
            if code.get("lines_changed", 0) > 100 and not api.get("findings"):
                conflicts.append({
                    "type": "MISSING_API_ANALYSIS",
                    "severity": "medium",
                    "source_agents": ["Code_Expert", "API_Expert"],
                    "message": "代码变更较大但API分析未发现接口变更，建议人工复核"
                })
            
            # 功能变更但无API变更
            if code.get("findings") and not api.get("api_changes"):
                conflicts.append({
                    "type": "UNDETECTED_API_IMPACT",
                    "severity": "low",
                    "source_agents": ["Code_Expert", "API_Expert"],
                    "message": "代码功能有变更但API分析未检测到接口变化"
                })
        
        return conflicts
    
    def _check_code_security_consistency(self, state: Dict[str, Any]) -> List[Dict]:
        """检查代码分析与安全分析的一致性"""
        conflicts = []
        
        code = state.get("code_analysis")
        security = state.get("security_analysis")
        
        if code and security:
            # 安全高风险但代码低风险
            if security.get("risk_level") in ["high", "critical"] and code.get("risk_level") == "low":
                conflicts.append({
                    "type": "RISK_MISMATCH",
                    "severity": "high",
                    "source_agents": ["Code_Expert", "Security_Expert"],
                    "message": "安全风险评估为高风险，但代码分析风险较低，需进一步调查"
                })
        
        return conflicts
    
    def _check_api_security_consistency(self, state: Dict[str, Any]) -> List[Dict]:
        """检查API与安全分析的一致性"""
        conflicts = []
        
        api = state.get("api_analysis")
        security = state.get("security_analysis")
        
        if api and security:
            # API变更涉及认证但未在安全检查中体现
            if any("认证" in f or "授权" in f for f in api.get("findings", [])):
                if not any("凭证" in f or "权限" in f for f in security.get("findings", [])):
                    conflicts.append({
                        "type": "MISSING_SECURITY_ANALYSIS",
                        "severity": "medium",
                        "source_agents": ["API_Expert", "Security_Expert"],
                        "message": "API涉及认证/授权变更但安全分析未检测相关风险"
                    })
        
        return conflicts
    
    def _check_confidence_consistency(self, state: Dict[str, Any]) -> List[Dict]:
        """检查置信度一致性"""
        conflicts = []
        
        agents = ["code_analysis", "api_analysis", "security_analysis"]
        
        confidences = []
        for agent_key in agents:
            agent_result = state.get(agent_key)
            if agent_result:
                confidences.append({
                    "agent": agent_key,
                    "confidence": agent_result.get("confidence", 0)
                })
        
        # 检查置信度差异
        if len(confidences) >= 2:
            max_conf = max(c["confidence"] for c in confidences)
            min_conf = min(c["confidence"] for c in confidences)
            
            if max_conf - min_conf > 0.3:
                conflicts.append({
                    "type": "CONFIDENCE_DISPARITY",
                    "severity": "low",
                    "source_agents": ["Multiple"],
                    "message": f"各专家置信度差异较大 (最高: {max_conf:.2f}, 最低: {min_conf:.2f})"
                })
        
        return conflicts
    
    def _generate_summary(self, conflicts: List[Dict]) -> str:
        """生成检查摘要"""
        if not conflicts:
            return "所有分析结果一致，未发现冲突"
        
        high_severity = sum(1 for c in conflicts if c.get("severity") == "high")
        medium_severity = sum(1 for c in conflicts if c.get("severity") == "medium")
        low_severity = sum(1 for c in conflicts if c.get("severity") == "low")
        
        summary = f"发现 {len(conflicts)} 个冲突: "
        summary += f"高风险 {high_severity} 个, "
        summary += f"中风险 {medium_severity} 个, "
        summary += f"低风险 {low_severity} 个"
        
        return summary
