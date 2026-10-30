# S00/M02：静态网页安全与交互修复

此分支基于 M01 分支，不改变原始课程 Markdown/PDF。41 篇课程与 README HTML 的正文（body）逐字保持不变，只调整文档头部的脚本加载和语言标记。

## 改动范围

- 删除全部 polyfill.io 引用，删除页面内过早执行的 highlightAll，固定 MathJax 为 3.2.2；markdown.js 先以 defer 执行来配置 MathJax，MathJax 再以 defer 启动，并由其自行完成初始公式排版。
- 课程批注使用本浏览器 localStorage，按 URL 路径和页面 DOM 顺序生成临时锚点；移除旧的重复导出行为，采用 textContent 处理用户输入，生成静态导出 HTML。
- 首页改为流式卡片布局；文章长表格与代码块可横向滚动，批注编辑器不再绝对定位。
- 增加 stdlib 静态安全测试和 Playwright Chromium 真实浏览器 E2E；远端依赖失效不应影响本地批注功能。

## 操作与测试

    python -m unittest discover -s tests -p 'test_web_static.py' -v
    python -m pip install 'playwright==1.55.0'
    python -m playwright install chromium
    python -m unittest discover -s tests -p 'test_web_e2e.py' -v

GitHub Actions 的 browser job 使用自带本地 HTTP 服务。若执行环境禁止 loopback、file URL 或浏览器启动，不应报告浏览器测试通过，应该在可访问的 CI runner 上验证。

## 已知边界

- 批注使用页面 DOM 顺序的锚点。内容增删可能改变映射位置；M03 应当在课程构建中生成稳定段落 ID，并提供批注迁移机制。
- 浏览器清除站点数据、隐私模式或不同设备不会自动同步批注。导出可作个人备份。
- MathJax 和 highlight.js 仍来自版本固定的 CDN；M03 可引入本地资源与 SRI。保留在线依赖的可用性风险。
- 本模块不变更课程原文、不补齐缺失内容、不审核课程 PDF 再传播权，也不开放真实交易接口。

参考：
- https://blog.cloudflare.com/automatically-replacing-polyfill-io-links-with-cloudflares-mirror-for-a-safer-internet/
- https://docs.mathjax.org/en/v3.1/web/configuration.html
- https://playwright.dev/python/docs/intro
