# 风格库管理

`styles/index.json` 是机器索引，`styles/风格索引.md` 和 `styles/index.html` 是可看图的目录。每个目录用“编号-名称”，含 profile.json、编号-效果图.jpg 和说明.md。效果图和配置必须一起维护。

选择：`python scripts/style_registry.py list`；初始化时 `--style-id CY-001`。已存在项目切换：`python scripts/style_registry.py apply 原计划.json --style-id CY-002 --output 新计划.json`，只接受已登记编号，不覆盖旧计划。标题文案、字体路径、当前身份、底部/AI声明保留，位置和排版由所选风格提供；身份行数不一致要先人工映射。切换后必须重做预览。不要把他人的名字复制进项目。

新增：从最接近的profile复制到新编号目录，修改真实参数，做一个人物与一个素材场景的预览、最长字幕和身份检查；保存实际效果图；再添加index.json项目。状态draft可展示但不能作为已验收默认，active才可执行。新风格不覆盖旧编号。用同一展示页可查看所有已登记风格，实际素材示例仅留在用户本地，公开包用合成示意。

一个风格内部的阴影或位置修订更新version；整体视觉方案变化分配新ID。修改后更新效果图和版本号。历史项目保留style快照，不自动追随更新。用户说“以后默认用…”时才改default_style；只说“这条用…”只影响当前片。
