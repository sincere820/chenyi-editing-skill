# 渲染入口

使用 scripts/render_edit.py；参数和配置见 [schema.md](schema.md)。先预览再全片，输出版本不覆盖。切气口先调用 natural_pause_cut.py，再用 remap_plan.py 对齐。
字幕阴影读取 style.shadow_alpha；默认00。每一风格可单独配置。无样式编号的旧项目仍可按其完整style快照渲染。
素材内部可能换镜头或出现烧录标题，首帧干净不能代替全区间检查。自动输出technical检查不代表听审已通过。
