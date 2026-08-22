# Code Impact Agent - 代码影响范围调查系统

基于多Agent协作架构的代码变更影响范围分析工具，支持代码、Puppet配置、API接口的全方位影响评估。

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      用户请求                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                       │
│              任务分解 · 路由决策 · 结果汇聚                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Code Expert  │   │ Infrastructure│   │   API Expert │
│   Agent      │   │    Expert     │   │   Agent      │
│ 代码静态分析  │   │   Agent      │   │  接口契约分析 │
└──────────────┘   └──────────────┘   └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
              ┌─────────────────────────────┐
              │  Consistency Checker Agent  │
              │      跨域一致性检查          │
              └─────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────┐
              │      Quality Gate Agent     │
              │       质量守门员             │
              └─────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────┐
              │     Case Learning Agent     │
              │      自监督学习              │
              └─────────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────────┐
              │       Final Report Output   │
              │    影响范围分析报告           │
              └─────────────────────────────┘
```

## Agent角色说明

| Agent | 职责 | 关键能力 |
|-------|------|---------|
| **Orchestrator** | 任务编排调度 | 并行执行、异常处理、结果汇聚 |
| **Code Expert** | 代码静态分析 | Diff分析、依赖提取、模式检测 |
| **Infrastructure Expert** | 基础设施分析 | Puppet配置解析、资源依赖分析 |
| **API Expert** | 接口契约分析 | 路由变更检测、向后兼容性分析 |
| **Security Expert** | 安全风险评估 | 敏感信息检测、攻击面分析 |
| **Consistency Checker** | 跨域一致性检查 | 冲突检测、置信度聚合 |
| **Quality Gate** | 质量守门 | 完整性检查、误报过滤 |
| **Case Learning** | 案例学习 | 历史积累、规则优化 |

## 安装

```bash
pip install -r requirements.txt
```

## 使用

### 基本用法

```bash
# 分析指定文件
python src/main.py analyze app.py

# 分析暂存区变更
python src/main.py analyze --staged

# 输出到文件
python src/main.py analyze app.py -o report.md
```

### 输出格式

报告包含：
- 基本信息（目标文件、分析时间、风险等级）
- 代码层分析（变更行数、影响模块、导入依赖）
- 基础设施层分析（Puppet资源、服务依赖）
- 接口层分析（API变更、兼容性）
- 安全风险评估（潜在漏洞、敏感信息）
- 跨域一致性检查结果
- 改进建议和行动项

## 项目结构

```
code-impact-agent/
├── src/
│   ├── main.py              # 主程序入口
│   ├── agents/              # Agent实现
│   │   ├── base.py
│   │   ├── code_expert.py
│   │   ├── infrastructure.py
│   │   ├── api_expert.py
│   │   ├── security.py
│   │   ├── consistency.py
│   │   ├── quality_gate.py
│   │   └── case_learning.py
│   └── tools/               # 工具链
│       ├── git_tool.py
│       ├── static_analysis.py
│       └── puppet_tool.py
├── config/
│   ├── semgrep-rules.json   # Semgrep规则
│   └── agent-config.yaml    # Agent配置
├── tests/
│   └── test_main.py
├── cases.json               # 历史案例存储
└── README.md
```

## 扩展开发

### 添加新的Agent

1. 继承 `BaseAgent` 类
2. 实现 `execute(self, state: dict) -> dict` 方法
3. 在 `Orchestrator.__init__` 中注册

```python
class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("My_Custom_Agent")
    
    def execute(self, state: dict) -> dict:
        # 实现分析逻辑
        state["my_result"] = {...}
        return state
```

### 添加新的工具

在 `src/tools/` 目录下创建工具类，实现静态分析方法。

## License

MIT License
