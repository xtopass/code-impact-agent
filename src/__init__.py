"""
代码影响范围调查Agent - 多Agent协作架构

架构组成：
- Orchestrator: 任务编排调度
- Code Expert: 代码静态分析
- Infrastructure Expert: Puppet配置分析
- API Expert: 接口契约分析
- Security Expert: 安全风险评估
- Consistency Checker: 跨域一致性检查
- Quality Gate: 质量守门员
- Case Learning: 案例学习

使用方式：
    from src.main import Orchestrator
    
    orchestrator = Orchestrator()
    report = orchestrator.analyze("path/to/file.py")
    print(report.to_markdown())
"""

from src.main import main

if __name__ == "__main__":
    main()
