# 脚本接口与可重现配置

所有路径都来自当前项目。`edit-plan.json` 的source、asset.path、font_file、fonts_dir可用相对路径（相对JSON目录）或当前机器绝对路径；工具可用PATH命令名。跨机器交付时优先相对路径并把合法可分发素材一起放进项目，否则提供重新链接清单。技能ZIP不含用户视频和字体。

配置示例见 `examples/edit-plan.example.json`。它是结构说明，示例media/font并不存在，不能当成已可渲染工程。用init_project建立真实配置。

- `source/duration/fps/speed`：实际源片（或已粗剪片）、秒数、30、1。
- `tools`：当前FFmpeg/ffprobe路径。
- `style`：模板中的字体、标题、身份、位置；字体路径必须实际存在。
- `captions`：start/end/text/timing_basis。成片秒数，严格有序、不重叠，每条≤13字符且宽≤970；按词时间切，不按字符平均分配冒充精确对齐。
- `assets`：ID映射到path/type及出处；type=image时按指定时长显示，视频不得超出素材源时长。
- `broll`：start/end/asset_id/source_in/focus_x/label/reason。不重叠；focus_x在0–1；固定当前竖屏scale-fill裁切。
- `source_time_map`：气口粗剪后附映射，当前source必须改为rough片；不能把原片时钟直接塞入成片配置。

```text
python scripts/transcribe.py "/media/原片.mp4" "/work/项目/analysis/transcript.raw.json" --model small
python scripts/render_edit.py "/work/项目/edit-plan.json" --output "/work/项目/preview/检查版.mp4" --end 20 --check-only
python scripts/render_edit.py "/work/项目/edit-plan.json" --output "/work/项目/preview/检查版.mp4" --end 20
python scripts/render_edit.py "/work/项目/edit-plan.json" --output "/work/项目/preview/完整v1.mp4"
```

20秒只是命令示例，应替换为本片完整句末；不能照抄切断讲话。check-only只检结构和生成字幕，不证明渲染成功。渲染器拒绝覆盖已有输出，修改后使用v2等新名字。Pillow必需，转写依赖可选。

renderer输出：MP4、旁边的review.json、editing/内ASS/SRT、picture-cache中间画面。不要把同名SRT放视频旁让播放器自动叠双字幕。缓存可重建，原素材不可删。ASS/SRT/JSON均可修改再渲染，但不是可拖动的原生NLE时间轴。

当前渲染器：1080×1920/30fps、硬切、源讲话整轨、B-roll覆盖、标题字幕；任意重排/变速不支持。气口删减需先经natural_pause_cut及remap_plan，或由原生编辑器以保留区间完成。没有听审则不执行删减。输出路径建议避免单引号等FFmpeg滤镜特殊字符；不要为绕开路径问题修改源文件名，改用正常的项目输出路径。

仅Python语法通过不足以验证，见测试记录中的真实解码与时间映射检查。参考渲染器已在Windows执行；macOS/Linux仅做便携路径设计，需目标环境预览验证，不宣称所有平台已实测。
