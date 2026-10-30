# S00/M01 内容安全模块使用说明

改造后的 main.py 默认只读。init 只新建缺失课件，不会覆盖课程或 README。audit 返回包含目录完整性和占位状态的 JSON 报告；已有 27 篇占位课程不会默认让 CI 失败，strict 模式会失败。

命令：

    python main.py audit
    python main.py audit --strict
    python main.py init --dry-run
    python main.py init
    python main.py backup --archive /tmp/behavior-finance-course-backup.zip
    python main.py verify-backup --archive /tmp/behavior-finance-course-backup.zip
    python -m unittest discover -s tests -v

备份只在用户运行 backup 时创建，不能替代异地灾难恢复。ZIP 可能包含原始课程 PDF，存储与分享前须确认版权授权。网页安全修复留待下一模块 M02；本模块的单元测试不能替代浏览器 E2E。
