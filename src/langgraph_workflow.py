"""
LangGraph 工作流实现
多Agent协作架构的完整工作流程定义
"""
from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph import StateGraph, END, start, end
import operator


# ==================== 状态定义 ====================

class AgentState(TypedDict):
    """完整的分析状态"""
    # 输入
    target_file: str
    options: dict
    
    # 中间结果
    code_diff: str
    git_info: dict
    dependency_graph: dict
    puppet_resources: list
    
    # 专家分析结果
    code_analysis: Optional[dict]
    infrastructure_analysis: Optional[dict]
    api_analysis: Optional[dict]
    security_analysis: Optional[dict]
    
    # 跨域检查
    cross_domain_conflicts: list
    cross_domain_check: Optional[dict]
    
    # 质量检查
    quality_issues: list
    quality_passed: bool
    
    # 最终输出
    final_risk_level: str
    recommendations: list
    report_markdown: str
    
    # 调试信息
    execution_log: list


# ==================== 路由函数 ====================

def should_run_infrastructure(state: AgentState) -> str:
    """判断是否运行基础设施分析"""
    if state["target_file"].endswith('.pp') or 'puppet' in state["target_file"].lower():
        return "infrastructure"
    return "api"


def should_check_consistency(state: AgentState) -> str:
    """判断是否需要一致性检查"""
    # 简化：始终检查
    return "consistency"


def should_run_quality_gate(state: AgentState) -> str:
    """判断是否需要质量守门"""
    return "quality"


def should_ask_human(state: AgentState) -> str:
    """判断是否需要人工介入"""
    conflicts = state.get("cross_domain_conflicts", [])
    if len(conflicts) > 0 or state.get("final_risk_level") == "critical":
        return "human_review"
    return "output"


# ==================== 节点函数 ====================

def extract_git_info(state: AgentState) -> AgentState:
    """提取Git信息"""
    print("🔍 [Orchestrator] 提取Git变更信息...")
    
    import subprocess
    from datetime import datetime
    
    try:
        # 获取diff
        result = subprocess.run(
            ["git", "diff", "--cached", state["target_file"]],
            capture_output=True, text=True
        )
        state["code_diff"] = result.stdout
        
        # 获取文件信息
        result = subprocess.run(
            ["git", "show", f":{state['target_file']}"],
            capture_output=True, text=True
        )
        state["git_info"] = {
            "exists": result.returncode == 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        state["git_info"] = {"error": str(e)}
    
    state["execution_log"].append({
        "step": "extract_git_info",
        "status": "completed"
    })
    return state


def run_code_expert(state: AgentState) -> AgentState:
    """运行代码专家"""
    print("📝 [Code_Expert] 分析代码变更...")
    
    # 简化的代码分析逻辑
    findings = []
    lines_changed = state["code_diff"].count('\n+') if state["code_diff"] else 0
    
    if "import" in state["code_diff"].lower():
        findings.append("检测到模块导入变更")
    if "def " in state["code_diff"] or "function " in state["code_diff"]:
        findings.append("检测到函数定义变更")
    
    state["code_analysis"] = {
        "agent_name": "Code_Expert",
        "findings": findings,
        "confidence": 0.85,
        "risk_level": "medium" if findings else "low",
        "details": {"lines_changed": lines_changed}
    }
    
    state["execution_log"].append({
        "step": "code_expert",
        "findings_count": len(findings)
    })
    return state


def run_infrastructure_expert(state: AgentState) -> AgentState:
    """运行基础设施专家"""
    print("⚙️  [Infrastructure_Expert] 分析Puppet配置...")
    
    findings = []
    
    if state["target_file"].endswith('.pp'):
        findings.append("检测到Puppet资源文件变更")
    
    state["infrastructure_analysis"] = {
        "agent_name": "Infrastructure_Expert",
        "findings": findings,
        "confidence": 0.9,
        "risk_level": "high" if findings else "low"
    }
    
    state["execution_log"].append({
        "step": "infrastructure_expert",
        "findings_count": len(findings)
    })
    return state


def run_api_expert(state: AgentState) -> AgentState:
    """运行API专家"""
    print("🔌 [API_Expert] 分析接口变更...")
    
    findings = []
    
    diff = state.get("code_diff", "")
    if "@app.route" in diff or "router" in diff.lower():
        findings.append("检测到路由定义变更")
    if "request." in diff or "response." in diff:
        findings.append("检测到请求/响应处理变更")
    
    state["api_analysis"] = {
        "agent_name": "API_Expert",
        "findings": findings,
        "confidence": 0.88,
        "risk_level": "medium" if findings else "low"
    }
    
    state["execution_log"].append({
        "step": "api_expert",
        "findings_count": len(findings)
    })
    return state


def run_security_expert(state: AgentState) -> AgentState:
    """运行安全专家"""
    print("🔒 [Security_Expert] 进行安全风险评估...")
    
    findings = []
    diff = state.get("code_diff", "")
    
    suspicious_patterns = [
        ("eval(", "动态代码执行风险"),
        ("exec(", "代码执行风险"),
        ("password", "凭证相关文件变更"),
        ("secret", "密钥相关文件变更"),
    ]
    
    for pattern, message in suspicious_patterns:
        if pattern in diff.lower():
            findings.append(message)
    
    state["security_analysis"] = {
        "agent_name": "Security_Expert",
        "findings": findings,
        "confidence": 0.92,
        "risk_level": "high" if findings else "low"
    }
    
    state["execution_log"].append({
        "step": "security_expert",
        "findings_count": len(findings)
    })
    return state


def run_consistency_checker(state: AgentState) -> AgentState:
    """运行跨域一致性检查器"""
    print("🔗 [Consistency_Checker] 检查跨域一致性...")
    
    conflicts = []
    
    code = state.get("code_analysis")
    api = state.get("api_analysis")
    security = state.get("security_analysis")
    
    # 检查代码与API分析的一致性
    if code and api:
        if code["details"].get("lines_changed", 0) > 100:
            if not api["findings"]:
                conflicts.append({
                    "type": "MISSING_API_ANALYSIS",
                    "severity": "medium",
                    "message": "代码变更较大但未检测到API变更"
                })
    
    # 检查安全与代码分析的一致性
    if security and code:
        if security["risk_level"] == "high" and code["risk_level"] == "low":
            conflicts.append({
                "type": "RISK_MISMATCH",
                "severity": "high",
                "message": "安全风险评估为高风险，但代码分析风险较低"
            })
    
    state["cross_domain_conflicts"] = conflicts
    state["cross_domain_check"] = {
        "status": "conflicts_found" if conflicts else "consistent",
        "conflicts": conflicts,
        "total_checks": 3,
        "passed": len(conflicts) == 0
    }
    
    state["execution_log"].append({
        "step": "consistency_check",
        "conflicts_found": len(conflicts)
    })
    return state


def run_quality_gate(state: AgentState) -> AgentState:
    """运行质量守门员"""
    print("✅ [Quality_Gate] 执行质量检查...")
    
    issues = []
    
    # 检查完整性
    required = ["code_analysis", "api_analysis", "security_analysis"]
    missing = [a for a in required if a not in state or not state[a]]
    if missing:
        issues.append(f"以下分析未执行: {', '.join(missing)}")
    
    # 检查置信度
    for key in ["code_analysis", "security_analysis"]:
        if key in state and state[key]:
            if state[key].get("confidence", 1.0) < 0.7:
                issues.append(f"{key} 置信度过低")
    
    # 检查冲突
    if state.get("cross_domain_check", {}).get("status") == "conflicts_found":
        issues.append(f"存在 {len(state['cross_domain_conflicts'])} 个跨域冲突")
    
    state["quality_issues"] = issues
    state["quality_passed"] = len(issues) == 0
    
    state["execution_log"].append({
        "step": "quality_gate",
        "issues_found": len(issues),
        "passed": state["quality_passed"]
    })
    return state


def calculate_risk(state: AgentState) -> AgentState:
    """计算最终风险等级"""
    print("📊 [Orchestrator] 计算最终风险等级...")
    
    risk_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    
    max_score = 1
    for key in ["code_analysis", "api_analysis", "security_analysis"]:
        if key in state and state[key]:
            score = risk_scores.get(state[key].get("risk_level", "low"), 1)
            max_score = max(max_score, score)
    
    # 如果有冲突，风险升级
    if state.get("cross_domain_conflicts"):
        max_score = min(max_score + 1, 4)
    
    score_to_level = {1: "low", 2: "medium", 3: "high", 4: "critical"}
    state["final_risk_level"] = score_to_level[max_score]
    
    state["execution_log"].append({
        "step": "calculate_risk",
        "risk_level": state["final_risk_level"]
    })
    return state


def generate_recommendations(state: AgentState) -> AgentState:
    """生成改进建议"""
    print("💡 [Orchestrator] 生成改进建议...")
    
    recommendations = []
    
    if state.get("code_analysis") and state["code_analysis"].get("findings"):
        recommendations.append("重点测试核心业务逻辑变更")
    
    if state.get("security_analysis") and state["security_analysis"].get("findings"):
        recommendations.extend([
            "进行安全代码审查",
            "检查敏感信息是否泄露"
        ])
    
    if state.get("api_analysis") and state["api_analysis"].get("findings"):
        recommendations.extend([
            "通知API调用方变更",
            "更新API文档"
        ])
    
    if state.get("cross_domain_conflicts"):
        recommendations.append("人工审核跨域冲突")
    
    if not recommendations:
        recommendations.append("代码变更较为安全，可按常规流程部署")
    
    state["recommendations"] = recommendations
    
    state["execution_log"].append({
        "step": "generate_recommendations",
        "count": len(recommendations)
    })
    return state


def generate_report(state: AgentState) -> AgentState:
    """生成最终报告"""
    print("📄 [Orchestrator] 生成Markdown报告...")
    
    report = f"""# 代码影响范围分析报告

## 基本信息
- **分析目标**: `{state['target_file']}`
- **分析时间**: {state['execution_log'][0]['timestamp'] if state.get('execution_log') else 'N/A'}
- **整体风险等级**: **{state['final_risk_level'].upper()}**

## 执行摘要
分析了 {state['target_file']} 的代码变更，整体风险等级为 **{state['final_risk_level']}**

---

## 代码层分析
| 项目 | 详情 |
|------|------|
| 变更行数 | {state.get('code_analysis', {}).get('details', {}).get('lines_changed', 'N/A')} |
| 影响模块数 | {len(state.get('code_analysis', {}).get('findings', []))} |
| 置信度 | {state.get('code_analysis', {}).get('confidence', 0):.0%} |

**发现的问题：**
""" + "\n".join([f"- {f}" for f in state.get("code_analysis", {}).get("findings", [])[:5]]) + """

---

## 接口层分析
| 项目 | 详情 |
|------|------|
| 接口变更 | {len(state.get('api_analysis', {}).get('findings', []))} |
| 置信度 | {state.get('api_analysis', {}).get('confidence', 0):.0%} |

**接口影响：**
""" + "\n".join([f"- {f}" for f in state.get("api_analysis", {}).get("findings", [])[:5]]) + """

---

## 安全风险评估
| 项目 | 详情 |
|------|------|
| 风险发现 | {len(state.get('security_analysis', {}).get('findings', []))} |
| 置信度 | {state.get('security_analysis', {}).get('confidence', 0):.0%} |

**安全隐患：**
""" + "\n".join([f"- {f}" for f in state.get("security_analysis", {}).get("findings", [])[:5]]) + """

---

## 跨域一致性检查
| 检查项 | 结果 |
|--------|------|
| 一致性状态 | {state.get('cross_domain_check', {}).get('status', 'N/A')} |
| 冲突数量 | {len(state.get('cross_domain_conflicts', []))} |

---

## 建议行动项
"""
    
    for i, rec in enumerate(state.get("recommendations", []), 1):
        report += f"{i}. {rec}\n"
    
    report += """
---

*本报告由 Code Impact Agent 自动生成*
"""
    
    state["report_markdown"] = report
    state["execution_log"].append({
        "step": "generate_report",
        "status": "completed"
    })
    return state


def human_review(state: AgentState) -> AgentState:
    """人工复核（占位）"""
    print("👤 [Human_Review] 需要人工介入...")
    
    # 在实际应用中，这里会触发通知或暂停等待人工输入
    state["execution_log"].append({
        "step": "human_review",
        "status": "pending_review"
    })
    return state


# ==================== 工作流构建 ====================

def build_workflow() -> StateGraph:
    """构建LangGraph工作流"""
    
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("extract_git_info", extract_git_info)
    workflow.add_node("code_expert", run_code_expert)
    workflow.add_node("infrastructure_expert", run_infrastructure_expert)
    workflow.add_node("api_expert", run_api_expert)
    workflow.add_node("security_expert", run_security_expert)
    workflow.add_node("consistency_checker", run_consistency_checker)
    workflow.add_node("quality_gate", run_quality_gate)
    workflow.add_node("calculate_risk", calculate_risk)
    workflow.add_node("generate_recommendations", generate_recommendations)
    workflow.add_node("generate_report", generate_report)
    workflow.add_node("human_review", human_review)
    
    # 设置入口
    workflow.add_edge(start, "extract_git_info")
    workflow.add_edge("extract_git_info", "code_expert")
    workflow.add_edge("code_expert", "api_expert")
    workflow.add_edge("code_expert", "security_expert")
    
    # 并行执行API和安全分析
    workflow.add_edge("api_expert", "consistency_checker")
    workflow.add_edge("security_expert", "consistency_checker")
    
    # 条件路由：是否运行基础设施分析
    workflow.add_conditional_edges(
        "security_expert",
        should_run_infrastructure,
        {
            "infrastructure": "infrastructure_expert",
            "api": "consistency_checker"
        }
    )
    
    # 后续流程
    workflow.add_edge("consistency_checker", "quality_gate")
    workflow.add_edge("quality_gate", "calculate_risk")
    workflow.add_edge("calculate_risk", "generate_recommendations")
    workflow.add_edge("generate_recommendations", "generate_report")
    
    # 条件路由：是否需要人工介入
    workflow.add_conditional_edges(
        "generate_report",
        should_ask_human,
        {
            "human_review": "human_review",
            "output": END
        }
    )
    workflow.add_edge("human_review", END)
    
    return workflow


# ==================== 执行入口 ====================

def run_analysis(target_file: str, options: dict = None) -> dict:
    """运行完整分析流程"""
    options = options or {}
    
    # 初始化状态
    initial_state: AgentState = {
        "target_file": target_file,
        "options": options,
        "code_diff": "",
        "git_info": {},
        "dependency_graph": {},
        "puppet_resources": [],
        "code_analysis": None,
        "infrastructure_analysis": None,
        "api_analysis": None,
        "security_analysis": None,
        "cross_domain_conflicts": [],
        "cross_domain_check": None,
        "quality_issues": [],
        "quality_passed": False,
        "final_risk_level": "low",
        "recommendations": [],
        "report_markdown": "",
        "execution_log": []
    }
    
    # 构建并编译工作流
    workflow = build_workflow()
    app = workflow.compile()
    
    # 执行分析
    result = app.invoke(initial_state)
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python langgraph_workflow.py <target_file>")
        sys.exit(1)
    
    target = sys.argv[1]
    print(f"开始分析: {target}")
    print("=" * 50)
    
    result = run_analysis(target)
    
    print("\n" + "=" * 50)
    print("分析完成！")
    print(f"风险等级: {result['final_risk_level']}")
    print(f"建议数量: {len(result['recommendations'])}")
    print(f"\n报告:\n{result['report_markdown']}")
