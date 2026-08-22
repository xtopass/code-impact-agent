#!/usr/bin/env python3
"""
单元测试
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.main import (
    RiskLevel,
    AnalysisStatus,
    CodeExpertAgent,
    InfrastructureExpertAgent,
    APIExpertAgent,
    SecurityExpertAgent,
    ConsistencyChecker,
    QualityGateAgent,
    CaseLearningAgent,
    Orchestrator,
    ImpactReport
)


class TestImpactReport(unittest.TestCase):
    """测试报告生成"""
    
    def test_to_markdown(self):
        """测试Markdown报告生成"""
        report = ImpactReport(
            target_file="test.py",
            created_at="2026-01-01T00:00:00",
            summary={"summary": "测试摘要"},
            final_risk_level=RiskLevel.MEDIUM,
            recommendations=["建议1", "建议2"]
        )
        md = report.to_markdown()
        self.assertIn("代码影响范围分析报告", md)
        self.assertIn("test.py", md)
        self.assertIn("建议1", md)


class TestRiskLevel(unittest.TestCase):
    """测试风险等级"""
    
    def test_risk_level_enum(self):
        self.assertEqual(RiskLevel.LOW.value, "low")
        self.assertEqual(RiskLevel.CRITICAL.value, "critical")


class TestAgents(unittest.TestCase):
    """测试Agent执行"""
    
    def test_code_expert_basic(self):
        """测试代码专家基础功能"""
        agent = CodeExpertAgent()
        state = {
            "target_file": "test.py",
            "code_diff": "diff --git a/test.py b/test.py\n+def new_func():\n"
        }
        result = agent.execute(state)
        self.assertIn("code_analysis", result)
        self.assertEqual(result["code_analysis"].status, AnalysisStatus.COMPLETED)
    
    def test_security_expert_basic(self):
        """测试安全专家基础功能"""
        agent = SecurityExpertAgent()
        state = {
            "target_file": "test.py",
            "code_diff": "+password = 'secret123'\n"
        }
        result = agent.execute(state)
        self.assertIn("security_analysis", result)
        self.assertTrue(any("凭证" in f for f in result["security_analysis"].findings))


class TestOrchestrator(unittest.TestCase):
    """测试编排器"""
    
    def test_analyze_nonexistent_file(self):
        """测试分析不存在的文件"""
        orchestrator = Orchestrator()
        report = orchestrator.analyze("nonexistent_file.py")
        self.assertIsNotNone(report)
        self.assertIsInstance(report, ImpactReport)


if __name__ == "__main__":
    unittest.main()
