# S00/M03 — 单一课程内容源与可重复站点构建

## 已确定的内容架构

- 40 篇课程/补充笔记的正文唯一发布源为原始 Markdown，课程身份、排序、状态源为 catalog/lessons.yaml。
- 旧 HTML 和旧 index.html 保留在 Git 历史中供迁移审查，但新站点只从 Markdown 生成，发布时只上传 site-dist 文件夹。
- 原 PDF 不打包。PDF 公开发布授权需另行确认；draft 仅表示有正文，不代表已审稿。
- markdown-it-py 4.2.0 安全关闭原始 HTML，支持表格和围栏代码。旧 Lecture/Content 三引号模板仅在生成时隐藏，原始文件保持不变。
- 内部课程 Markdown 链接构建为 HTML 链接；找不到的本地 Markdown 目标导致失败。
- manifest 中记录每个输出文件 SHA-256；重复构建必须逐字节一致。已有生成目录如果发生人工变更则拒绝覆盖。
- 这是一套轻量级构建器，未来可在不变更课程元数据的前提下，与 MkDocs/Zensical 对照评测。

## 本地命令

    python -m pip install -r requirements-site.txt
    python tools/build_site.py inventory
    python tools/build_site.py build
    python tools/build_site.py check
    python -m unittest discover -s tests -p 'test_site_builder.py' -v
    python -m http.server 8000 --directory site-dist

浏览器打开 http://127.0.0.1:8000 。构建输出为 site-dist，已从 Git 追踪中忽略。更新源文件后，build 会检查旧输出并拒绝覆盖；确认输出不需要后，可人工删除 site-dist 再重新构建。

## 数据与安全边界

- 生成器不执行 Markdown 内嵌原始 HTML，因此部分历史 HTML 自定义排版可能不再保留；保留 Markdown 语义正文及表格。
- 本批不为 27 篇空壳补写正文。未审核的草稿显式显示，不以篇数代表完成度。
- M02 的批注按 DOM 顺序定位；未来文章增删可能产生错位。后续知识工程模块处理稳定锚点及迁移。
- 页面依赖线上 MathJax 3.2.2 公式排版；生成文件本身可确定性校验，但完整公式离线显示需要后续本地资产打包。
- 如果源文含本地图片/附件，应另建许可核查和资源复制流程；不要直接把整个 Git 仓库公开部署。
- 生成器拒绝覆盖不属于构建过程的目录文件。不得运行清空课程源文件的脚本。

## 验收标准

- 8 个模块、40 篇材料、38 个正式课程、2 个补充笔记被唯一 catalog 收录。
- 构建 40 个课程 HTML + 首页，全部位于新发布目录；没有发布课程 PDF。
- 校验坏链、越界路径、原始 HTML 转义、同目录重建、不同运行结果一致和产物 SHA。
- 加入真实浏览器构建站点的导航和移动端回归；保持 M01/M02 测试通过。

参考：
https://markdown-it-py.readthedocs.io/en/latest/security.html
https://markdown-it-py.readthedocs.io/en/latest/using.html
