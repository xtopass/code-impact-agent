"""
案例学习Agent
负责从历史案例中学习优化分析规则
"""
import json
import os
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from src.agents.base import BaseAgent


class CaseLearningAgent(BaseAgent):
    """案例学习Agent"""
    
    def __init__(self, case_file: str = "cases.json"):
        super().__init__(
            name="Case_Learning",
            description="从历史分析案例中学习，持续优化分析规则"
        )
        self.case_file = Path(case_file)
        self.cases = self._load_cases()
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行案例学习和规则更新"""
        self.logger.info(f"[{self.name}] 执行案例学习")
        
        # 1. 保存当前分析案例
        case = self._save_case(state)
        
        # 2. 分析历史模式
        patterns = self._analyze_patterns()
        
        # 3. 更新规则建议
        rule_updates = self._suggest_rule_updates(patterns)
        
        state["case_learning"] = {
            "case_saved": case,
            "patterns_analyzed": patterns,
            "rule_updates": rule_updates,
            "total_cases": len(self.cases)
        }
        
        self.logger.info(f"[{self.name}] 学习完成，累计 {len(self.cases)} 个案例")
        return state
    
    def _load_cases(self) -> List[Dict]:
        """加载历史案例"""
        if self.case_file.exists():
            try:
                with open(self.case_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_case(self, state: Dict[str, Any]) -> Dict:
        """保存当前分析案例"""
        case = {
            "timestamp": datetime.now().isoformat(),
            "target_file": state.get("target_file", ""),
            "risk_level": state.get("final_risk_level", "unknown"),
            "code_findings": len(state.get("code_analysis", {}).get("findings", [])),
            "api_findings": len(state.get("api_analysis", {}).get("findings", [])),
            "security_findings": len(state.get("security_analysis", {}).get("findings", [])),
            "quality_passed": state.get("quality_check", {}).get("passed", False),
            "recommendations_count": len(state.get("recommendations", []))
        }
        
        self.cases.append(case)
        self._persist_cases()
        
        return case
    
    def _persist_cases(self):
        """持久化案例到文件"""
        try:
            with open(self.case_file, 'w', encoding='utf-8') as f:
                json.dump(self.cases, f, indent=2, ensure_ascii=False)
        except IOError as e:
            self.logger.error(f"保存案例失败: {e}")
    
    def _analyze_patterns(self) -> Dict[str, Any]:
        """分析历史案例模式"""
        if not self.cases:
            return {"patterns": [], "trends": {}}
        
        # 统计风险等级分布
        risk_distribution = {}
        for case in self.cases:
            risk = case.get("risk_level", "unknown")
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        # 统计平均发现数
        avg_code_findings = sum(c.get("code_findings", 0) for c in self.cases) / len(self.cases)
        avg_security_findings = sum(c.get("security_findings", 0) for c in self.cases) / len(self.cases)
        
        # 检测趋势
        recent_cases = self.cases[-10:] if len(self.cases) >= 10 else self.cases
        recent_risk_high = sum(1 for c in recent_cases if c.get("risk_level") in ["high", "critical"])
        
        return {
            "total_cases": len(self.cases),
            "risk_distribution": risk_distribution,
            "avg_findings": {
                "code": avg_code_findings,
                "security": avg_security_findings
            },
            "trends": {
                "recent_high_risk_ratio": recent_risk_high / len(recent_cases) if recent_cases else 0,
                "quality_pass_rate": sum(1 for c in self.cases if c.get("quality_passed")) / len(self.cases)
            }
        }
    
    def _suggest_rule_updates(self, patterns: Dict[str, Any]) -> List[Dict]:
        """根据分析结果建议规则更新"""
        suggestions = []
        
        # 基于风险分布建议
        risk_dist = patterns.get("risk_distribution", {})
        if risk_dist.get("critical", 0) > len(self.cases) * 0.3:
            suggestions.append({
                "type": "risk_calibration",
                "priority": "high",
                "message": "高比例critical风险，建议调整风险评分阈值"
            })
        
        # 基于质量通过率建议
        pass_rate = patterns.get("trends", {}).get("quality_pass_rate", 1.0)
        if pass_rate < 0.7:
            suggestions.append({
                "type": "quality_improvement",
                "priority": "medium",
                "message": "质量通过率较低，建议优化分析规则减少误报"
            })
        
        return suggestions
    
    def get_case_statistics(self) -> Dict[str, Any]:
        """获取案例统计信息"""
        if not self.cases:
            return {"message": "暂无历史案例"}
        
        return {
            "total_cases": len(self.cases),
            "risk_distribution": self._analyze_patterns().get("risk_distribution", {}),
            "recent_cases": self.cases[-5:],
            "last_updated": self.cases[-1].get("timestamp") if self.cases else None
        }
