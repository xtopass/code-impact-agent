#!/usr/bin/env python3
"""
代码影响范围调查 — 多Agent协作架构系统

架构设计：
- Orchestrator Agent: 任务分解与路由
- Code Expert Agent: 代码静态分析
- Infrastructure Expert Agent: Puppet配置分析
- API Expert Agent: 接口契约分析
- Security Expert Agent: 安全风险评估
- Cross-Domain Consistency Checker: 跨域一致性检查
- Quality Gate Agent: 质量守门员
- Case Learning Agent: 案例学习
"""

from typing import TypedDict, Annotated, Literal, Optional
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ChangeInfo:
    """变更基本信息"""
    file_path: str
    change_type: str  # added, modified, deleted
    lines_changed: int = 0
    diff_content: str = ""


@dataclass
class DependencyNode:
    """依赖图节点"""
    id: str
    type: str  # file, module, service, resource
    name: str
    dependencies: list = field(default_factory=list)


@dataclass
class AnalysisResult:
    """单个专家的分析结果"""
    agent_name: str
    status: AnalysisStatus
    findings: list = field(default_factory=list)
    confidence: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    details: dict = field(default_factory=dict)


@dataclass 
class ImpactReport:
    """最终影响范围报告"""
    target_file: str
    created_at: str
    summary: dict = field(default_factory=dict)
    code_analysis: Optional[AnalysisResult] = None
    infrastructure_analysis: Optional[AnalysisResult] = None
    api_analysis: Optional[AnalysisResult] = None
    security_analysis: Optional[AnalysisResult] = None
    cross_domain_check: Optional[dict] = None
    final_risk_level: RiskLevel = RiskLevel.LOW
    recommendations: list = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """生成Markdown报告"""
        md = f"""# 代码影响范围分析报告

## 基本信息
- **分析目标**: `{self.target_file}`
- **分析时间**: {self.created_at}
- **整体风险等级**: **{self.final_risk_level.value.upper()}**

## 执行摘要
{self.summary.get('summary', '无')}

---

## 代码层分析
{self._format_code_analysis()}

---

## 基础设施层分析
{self._format_infra_analysis()}

---

## 接口层分析
{self._format_api_analysis()}

---

## 安全风险评估
{self._format_security_analysis()}

---

## 跨域一致性检查
{self._format_cross_domain()}

---

## 建议行动项
"""
        for i, rec in enumerate(self.recommendations, 1):
            md += f"{i}. {rec}\n"
        
        md += """
---

*本报告由 Code Impact Agent 自动生成*
"""
        return md
    
    def _format_code_analysis(self) -> str:
        if not self.code_analysis:
            return "*未执行*"
        return f"""
| 项目 | 详情 |
|------|------|
| 变更行数 | {self.code_analysis.details.get('lines_changed', 'N/A')} |
| 影响模块数 | {len(self.code_analysis.findings)} |
| 置信度 | {self.code_analysis.confidence:.1%} |

**发现的问题：**
""" + "\n".join([f"- {f}" for f in self.code_analysis.findings[:5]])
    
    def _format_infra_analysis(self) -> str:
        if not self.infrastructure_analysis:
            return "*未执行*"
        return f"""
| 项目 | 详情 |
|------|------|
| Puppet资源 | {len(self.infrastructure_analysis.findings)} |
| 置信度 | {self.infrastructure_analysis.confidence:.1%} |

**配置变更：**
""" + "\n".join([f"- {f}" for f in self.infrastructure_analysis.findings[:5]])
    
    def _format_api_analysis(self) -> str:
        if not self.api_analysis:
            return "*未执行*"
        return f"""
| 项目 | 详情 |
|------|------|
| 接口变更 | {len(self.api_analysis.findings)} |
| 置信度 | {self.api_analysis.confidence:.1%} |

**接口影响：**
""" + "\n".join([f"- {f}" for f in self.api_analysis.findings[:5]])
    
    def _format_security_analysis(self) -> str:
        if not self.security_analysis:
            return "*未执行*"
        return f"""
| 项目 | 详情 |
|------|------|
| 风险发现 | {len(self.security_analysis.findings)} |
| 置信度 | {self.security_analysis.confidence:.1%} |

**安全隐患：**
""" + "\n".join([f"- {f}" for f in self.security_analysis.findings[:5]])
    
    def _format_cross_domain(self) -> str:
        if not self.cross_domain_check:
            return "*未执行*"
        return f"""
| 检查项 | 结果 |
|--------|------|
| 一致性状态 | {self.cross_domain_check.get('status', 'N/A')} |
| 冲突数量 | {self.cross_domain_check.get('conflicts', 0)} |
"""


# ==================== 工具层 ====================

class GitTool:
    """Git操作工具"""
    
    @staticmethod
    def get_diff(target: str, staged: bool = False) -> str:
        """获取文件diff"""
        cmd = ["git", "diff", "--cached" if staged else "", target]
        cmd = [c for c in cmd if c]  # 移除空字符串
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    @staticmethod
    def get_changed_files(base: str = "HEAD", head: str = "HEAD") -> list[str]:
        """获取变更文件列表"""
        result = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            capture_output=True, text=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """获取文件基本信息"""
        info = {
            "exists": os.path.exists(file_path),
            "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "modified": datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).isoformat() if os.path.exists(file_path) else None
        }
        return info


class StaticAnalysisTool:
    """静态分析工具"""
    
    @staticmethod
    def run_semgrep(target: str, rules: str = None) -> dict:
        """运行Semgrep静态分析"""
        # 这里简化实现，实际应调用semgrep命令行
        return {
            "findings": [],
            "errors": []
        }
    
    @staticmethod
    def extract_imports(file_path: str) -> list[str]:
        """提取文件导入依赖"""
        # 简化实现：基于文件扩展名判断
        ext_map = {
            '.py': ['python'],
            '.js': ['node_modules'],
            '.java': ['maven_dependencies']
        }
        ext = Path(file_path).suffix
        return ext_map.get(ext, [])


class PuppetTool:
    """Puppet配置分析工具"""
    
    @staticmethod
    def validate_manifest(manifest: str) -> dict:
        """验证Puppet清单语法"""
        result = subprocess.run(
            ["puppet", "parser", "validate", manifest],
            capture_output=True, text=True
        )
        return {
            "valid": result.returncode == 0,
            "stderr": result.stderr,
            "stdout": result.stdout
        }
    
    @staticmethod
    def parse_dependencies(manifest: str) -> list[dict]:
        """解析Puppet资源依赖"""
        # 简化实现
        return []


# ==================== Agent层 ====================

class BaseAgent:
    """Agent基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    def execute(self, state: dict) -> dict:
        raise NotImplementedError


class CodeExpertAgent(BaseAgent):
    """代码专家Agent"""
    
    def __init__(self):
        super().__init__("Code_Expert")
        self.git_tool = GitTool()
        self.static_tool = StaticAnalysisTool()
    
    def execute(self, state: dict) -> dict:
        self.logger.info(f"[{self.name}] 开始分析代码变更: {state.get('target_file')}")
        
        target = state.get("target_file", "")
        findings = []
        
        # 获取diff信息
        diff = self.git_tool.get_diff(target)
        state["code_diff"] = diff
        
        # 分析变更
        if diff:
            lines_changed = len([l for l in diff.split('\n') if l.startswith('+') and not l.startswith('+++')])
            state["code_lines_changed"] = lines_changed
            
            # 检测关键变更模式
            if "import" in diff.lower() or "require" in diff.lower():
                findings.append("检测到模块导入变更，可能影响依赖关系")
            if "def " in diff or "function " in diff:
                findings.append("检测到函数定义变更")
            if "@api" in diff or "route" in diff.lower():
                findings.append("检测到API相关变更")
        
        # 提取导入依赖
        imports = self.static_tool.extract_imports(target)
        state["code_imports"] = imports
        
        result = AnalysisResult(
            agent_name=self.name,
            status=AnalysisStatus.COMPLETED,
            findings=findings,
            confidence=0.85 if findings else 0.95,
            risk_level=RiskLevel.MEDIUM if findings else RiskLevel.LOW,
            details={"lines_changed": state.get("code_lines_changed", 0), "imports": imports}
        )
        
        state["code_analysis"] = result
        self.logger.info(f"[{self.name}] 分析完成，发现 {len(findings)} 个问题")
        return state


class InfrastructureExpertAgent(BaseAgent):
    """基础设施专家Agent"""
    
    def __init__(self):
        super().__init__("Infrastructure_Expert")
        self.puppet_tool = PuppetTool()
    
    def execute(self, state: dict) -> dict:
        self.logger.info(f"[{self.name}] 开始分析基础设施配置")
        
        target = state.get("target_file", "")
        findings = []
        
        # 检查是否为Puppet文件
        if target.endswith('.pp') or 'puppet' in target.lower():
            validation = self.puppet_tool.validate_manifest(target)
            if not validation["valid"]:
                findings.append(f"Puppet语法错误: {validation['stderr']}")
            
            deps = self.puppet_tool.parse_dependencies(target)
            state["puppet_resources"] = deps
        
        result = AnalysisResult(
            agent_name=self.name,
            status=AnalysisStatus.COMPLETED,
            findings=findings,
            confidence=0.9 if findings else 0.95,
            risk_level=RiskLevel.HIGH if findings else RiskLevel.LOW,
            details={}
        )
        
        state["infrastructure_analysis"] = result
        self.logger.info(f"[{self.name}] 分析完成")
        return state


class APIExpertAgent(BaseAgent):
    """API专家Agent"""
    
    def __init__(self):
        super().__init__("API_Expert")
    
    def execute(self, state: dict) -> dict:
        self.logger.info(f"[{self.name}] 开始分析API变更")
        
        target = state.get("target_file", "")
        findings = []
        
        # 分析可能的API变更
        diff = state.get("code_diff", "")
        if diff:
            if "@app.route" in diff or "@router" in diff or "express." in diff:
                findings.append("检测到路由定义变更")
            if "request." in diff or "response." in diff:
                findings.append("检测到请求/响应处理变更")
            if "params" in diff and ("delete" in diff or "remove" in diff):
                findings.append("检测到参数移除，可能破坏向后兼容")
        
        result = AnalysisResult(
            agent_name=self.name,
            status=AnalysisStatus.COMPLETED,
            findings=findings,
            confidence=0.88,
            risk_level=RiskLevel.MEDIUM if findings else RiskLevel.LOW,
            details={}
        )
        
        state["api_analysis"] = result
        self.logger.info(f"[{self.name}] 分析完成，发现 {len(findings)} 个API变更")
        return state


class SecurityExpertAgent(BaseAgent):
    """安全专家Agent"""
    
    def __init__(self):
        super().__init__("Security_Expert")
    
    def execute(self, state: dict) -> dict:
        self.logger.info(f"[{self.name}] 开始安全风险评估")
        
        target = state.get("target_file", "")
        findings = []
        
        # 安全检查
        diff = state.get("code_diff", "")
        if diff:
            suspicious_patterns = [
                ("eval(", "动态代码执行风险"),
                ("exec(", "代码执行风险"),
                ("os.system(", "系统命令注入风险"),
                ("password", "凭证相关文件变更"),
                ("secret", "密钥相关文件变更"),
                ("chmod", "权限变更"),
                ("sudo", "特权操作")
            ]
            
            for pattern, message in suspicious_patterns:
                if pattern in diff.lower():
                    findings.append(message)
        
        result = AnalysisResult(
            agent_name=self.name,
            status=AnalysisStatus.COMPLETED,
            findings=findings,
            confidence=0.92,
            risk_level=RiskLevel.HIGH if findings else RiskLevel.LOW,
            details={}
        )
        
        state["security_analysis"] = result
        self.logger.info(f"[{self.name}] 分析完成，发现 {len(findings)} 个安全风险")
        return state


class ConsistencyChecker(BaseAgent):
    """跨域一致性检查器"""
    
    def __init__(self):
        super().__init__("Consistency_Checker")
    
    def execute(self, state: dict) -> dict:
        self.logger.info(f"[{self.name}] 执行跨域一致性检查")
        
        conflicts = []
        
        # 检查代码分析与API分析的一致性
        code_analysis = state.get("code_analysis")
        api_analysis = state.get("api_analysis")
        
        if code_analysis and api_analysis:
            # 如果代码变更包含函数签名但API分析未检测到
            if code_analysis.details.get("lines_changed", 0) > 50:
                if not api_analysis.findings:
                    conflicts.append({
                        "type": "MISSING_API_ANALYSIS",
                        "severity": "medium",
                        "message": "代码变更较大但未检测到API变更，建议人工复核"
                    })
        
        # 检查安全分析与代码分析的一致性
        security_analysis = state.get("security_analysis")
        if security_analysis and security_analysis.risk_level == RiskLevel.HIGH:
            if not code_analysis or code_analysis.risk_level == RiskLevel.LOW:
                conflicts.append({
                    "type": "RISK_MISMATCH",
                    "severity": "high",
                    "message": "安全风险评估为高风险，但代码分析风险较低"
                })
        
        state["cross_domain_conflicts"] = conflicts
        
        result = {
            "status": "consistent" if not conflicts else "conflicts_found",
            "conflicts": conflicts,
            "total_checks": 3,
            "passed": len(conflicts) == 0
        }
        
        state["cross_domain_check"] = result
        self.logger.info(f"[{self.name}] 检查完成，发现 {len(conflicts)} 个冲突")
        return state


class QualityGateAgent(BaseAgent):
    """质量守门员Agent"""
    
    def __init__(self):
        super().__init__("Quality_Gate")
    
    def execute(self, state: dict) -> dict:
        self.logger.info(f"[{self.name}] 执行质量检查")
        
        issues = []
        
        # 检查报告完整性
        required_agents = ["code_analysis", "infrastructure_analysis", "api_analysis", "security_analysis"]
        missing = [a for a in required_agents if a not in state or not state[a]]
        if missing:
            issues.append(f"以下专家未执行分析: {', '.join(missing)}")
        
        # 检查置信度
        for agent_name in ["code_analysis", "security_analysis"]:
            if agent_name in state:
                agent_result = state[agent_name]
                if hasattr(agent_result, 'confidence') and agent_result.confidence < 0.7:
                    issues.append(f"{agent_name} 置信度过低 ({agent_result.confidence:.2f})")
        
        # 检查冲突
        if state.get("cross_domain_check", {}).get("status") == "conflicts_found":
            issues.append(f"存在 {len(state['cross_domain_conflicts'])} 个跨域冲突需人工处理")
        
        state["quality_issues"] = issues
        state["quality_passed"] = len(issues) == 0
        
        self.logger.info(f"[{self.name}] 检查完成，发现 {len(issues)} 个问题")
        return state


class CaseLearningAgent(BaseAgent):
    """案例学习Agent"""
    
    def __init__(self):
        super().__init__("Case_Learning")
        self.case_store = []  # 简化实现，实际应使用数据库
    
    def execute(self, state: dict) -> dict:
        self.logger.info(f"[{self.name}] 记录案例分析案例")
        
        # 保存案例
        case = {
            "timestamp": datetime.now().isoformat(),
            "target": state.get("target_file"),
            "risk_level": state.get("final_risk_level", "unknown"),
            "findings_count": sum([
                len(state.get(a, AnalysisResult("", AnalysisStatus.FAILED)).findings)
                for a in ["code_analysis", "api_analysis", "security_analysis"]
                if a in state
            ]),
            "quality_passed": state.get("quality_passed", False)
        }
        
        self.case_store.append(case)
        
        # 保存到文件
        case_file = Path("cases.json")
        if case_file.exists():
            with open(case_file, 'r') as f:
                stored_cases = json.load(f)
        else:
            stored_cases = []
        
        stored_cases.append(case)
        with open(case_file, 'w') as f:
            json.dump(stored_cases, f, indent=2)
        
        self.logger.info(f"[{self.name}] 案例已保存，累计 {len(stored_cases)} 个案例")
        return state


# ==================== 编排调度层 ====================

class Orchestrator:
    """任务编排调度器"""
    
    def __init__(self):
        self.agents = {
            "code": CodeExpertAgent(),
            "infrastructure": InfrastructureExpertAgent(),
            "api": APIExpertAgent(),
            "security": SecurityExpertAgent(),
            "consistency": ConsistencyChecker(),
            "quality": QualityGateAgent(),
            "learning": CaseLearningAgent()
        }
        self.logger = logging.getLogger("Orchestrator")
    
    def analyze(self, target_file: str, options: dict = None) -> ImpactReport:
        """执行完整的影响范围分析"""
        options = options or {}
        
        self.logger.info(f"开始分析目标: {target_file}")
        
        # 初始化状态
        state = {
            "target_file": target_file,
            "options": options,
            "created_at": datetime.now().isoformat(),
            "code_analysis": None,
            "infrastructure_analysis": None,
            "api_analysis": None,
            "security_analysis": None,
            "cross_domain_check": None,
            "final_risk_level": RiskLevel.LOW,
            "recommendations": []
        }
        
        # 1. 并行执行专家分析
        self.logger.info("启动并行专家分析...")
        state = self._run_parallel_experts(state, ["code", "infrastructure", "api", "security"])
        
        # 2. 跨域一致性检查
        self.logger.info("执行跨域一致性检查...")
        state = self.agents["consistency"].execute(state)
        
        # 3. 质量守门
        self.logger.info("执行质量检查...")
        state = self.agents["quality"].execute(state)
        
        # 4. 风险汇总
        state = self._calculate_final_risk(state)
        
        # 5. 生成建议
        state = self._generate_recommendations(state)
        
        # 6. 记录案例
        self.agents["learning"].execute(state)
        
        # 7. 生成报告
        report = self._generate_report(state)
        
        self.logger.info(f"分析完成，风险等级: {report.final_risk_level.value}")
        return report
    
    def _run_parallel_experts(self, state: dict, agent_keys: list) -> dict:
        """并行执行多个专家Agent"""
        for key in agent_keys:
            if key in self.agents:
                try:
                    state = self.agents[key].execute(state)
                except Exception as e:
                    self.logger.error(f"专家 {key} 执行失败: {e}")
                    state[key + "_analysis"] = AnalysisResult(
                        agent_name=key,
                        status=AnalysisStatus.FAILED,
                        findings=[f"执行失败: {str(e)}"],
                        confidence=0.0
                    )
        return state
    
    def _calculate_final_risk(self, state: dict) -> dict:
        """计算最终风险等级"""
        risk_scores = {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        
        max_score = 1
        for key in ["code_analysis", "api_analysis", "security_analysis"]:
            if key in state and state[key]:
                score = risk_scores.get(state[key].risk_level, 1)
                max_score = max(max_score, score)
        
        # 如果存在跨域冲突，风险升级
        if state.get("cross_domain_check", {}).get("status") == "conflicts_found":
            max_score = min(max_score + 1, 4)
        
        state["final_risk_level"] = RiskLevel(max_score)
        return state
    
    def _generate_recommendations(self, state: dict) -> dict:
        """生成改进建议"""
        recommendations = []
        
        # 基于分析结果生成建议
        if state.get("code_analysis") and state["code_analysis"].findings:
            recommendations.append("重点测试核心业务逻辑变更")
        
        if state.get("security_analysis") and state["security_analysis"].findings:
            recommendations.append("进行安全代码审查")
            recommendations.append("检查敏感信息是否泄露")
        
        if state.get("api_analysis") and state["api_analysis"].findings:
            recommendations.append("通知API调用方变更")
            recommendations.append("更新API文档")
        
        if state.get("cross_domain_check", {}).get("status") == "conflicts_found":
            recommendations.append("人工审核跨域冲突")
        
        if not recommendations:
            recommendations.append("代码变更较为安全，可按常规流程部署")
        
        state["recommendations"] = recommendations
        return state
    
    def _generate_report(self, state: dict) -> ImpactReport:
        """生成最终报告"""
        report = ImpactReport(
            target_file=state["target_file"],
            created_at=state["created_at"],
            summary={
                "summary": f"分析了 {state['target_file']} 的代码变更，整体风险等级为 {state['final_risk_level'].value}"
            },
            code_analysis=state.get("code_analysis"),
            infrastructure_analysis=state.get("infrastructure_analysis"),
            api_analysis=state.get("api_analysis"),
            security_analysis=state.get("security_analysis"),
            cross_domain_check=state.get("cross_domain_check"),
            final_risk_level=state["final_risk_level"],
            recommendations=state.get("recommendations", [])
        )
        return report


# ==================== CLI入口 ====================

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="代码影响范围调查Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py analyze app.py
  python main.py analyze --staged
  python main.py analyze --output report.md
        """
    )
    
    parser.add_argument("command", choices=["analyze", "list", "cases"],
                       help="命令: analyze-分析, list-列出历史案例, cases-查看案例统计")
    parser.add_argument("target", nargs="?", help="目标文件路径")
    parser.add_argument("--staged", action="store_true", help="分析暂存区变更")
    parser.add_argument("--output", "-o", help="输出报告文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    if args.command == "analyze":
        if not args.target:
            print("错误: analyze命令需要提供目标文件")
            sys.exit(1)
        
        orchestrator = Orchestrator()
        report = orchestrator.analyze(args.target)
        
        # 输出报告
        markdown = report.to_markdown()
        print(markdown)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(markdown)
            print(f"\n报告已保存到: {args.output}")
    
    elif args.command == "cases":
        case_file = Path("cases.json")
        if case_file.exists():
            with open(case_file, 'r') as f:
                cases = json.load(f)
            print(f"历史案例: {len(cases)} 个")
            for case in cases[-5:]:  # 显示最近5个
                print(f"  - {case['target']}: {case['risk_level']}")
        else:
            print("暂无历史案例")
    
    elif args.command == "list":
        print("可用命令: analyze, cases")


if __name__ == "__main__":
    main()
