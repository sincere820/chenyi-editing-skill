# 前期准备与启动

## 先确定工具能力

| 能力 | 最低准备 | 不具备时 |
|---|---|---|
| 文稿气口分析 | 可读文本的agent | 可执行文字模式 |
| 本地剪辑 | Python 3.10+、FFmpeg、ffprobe、Pillow | 给出缺失项，不声称已剪片 |
| 精确字幕 | 有时间码的转写工具，或faster-whisper与模型 | 先转写，不估造时间 |
| 听音判断 | 可播放并理解音频的能力，或用户听审 | 候选不自动批准 |
| 在线素材 | 网页/下载工具、用户授权、可用空间 | 自有素材或缺口清单 |
| 可编辑剪辑台 | 已登录且可调用的ChatCut/其他NLE工具 | 说明阻点，不能用MP4冒充 |

仅把技能贴进没有文件/执行工具的聊天框，不能让它自动剪视频。接收方应能访问原片和素材目录；上传纯文字并不等于上传视频。

## 依赖

Python环境内安装 `python -m pip install -r requirements.txt`。使用本地转写时另装 `python -m pip install -r requirements-transcription.txt`；Faster-Whisper首次使用会下载模型，已缓存可加 `--offline`。安装授权依用户已有请求执行，不修改无关系统设置。

建议在独立虚拟环境安装：`python -m venv .venv`，再使用该环境的Python执行后续命令。Faster-Whisper官方安装与模型说明：https://github.com/SYSTRAN/faster-whisper 。依赖范围不是逐字节锁定环境；严格复现应保留本机实际依赖版本及字体哈希。

系统需有 FFmpeg 和 ffprobe，FFmpeg包含 `libx264`、AAC、`ass`（libass）、`silencedetect`、`trim`、`atrim`、`concat`。用 `ffmpeg -version`、`ffprobe -version`、`ffmpeg -filters` 核对。二者可在PATH或通过参数指定绝对路径。FFmpeg官方获取入口：https://ffmpeg.org/download.html 。其他发行包需核对来源，不运行未知一键脚本。

字体采用 **Source Han Serif SC Heavy / 思源宋体简体中文 Heavy** 的独立OTF，官方：https://github.com/adobe-fonts/source-han-serif 。接收方获取字体时保留官方许可。不要把“字由永胜粗宋”当成已附带字体；本包使用已认可的思源宋体回退。具体字体文件哈希应写入项目记录；换字体须重新目检。不要仅凭字体名称假定已加载。

## 创建项目

以下命令在技能根目录执行；示例路径由接收方替换，不能照抄你电脑的盘符。

```text
python scripts/init_project.py --source "/media/口播.mp4" --project "/work/新片" --font "/fonts/SourceHanSerifSC-Heavy.otf" --title-top "全球AI巨头密集发声" --title-bottom "未来将发生3件大事"
```

Windows同样使用双引号路径。工具不在PATH则追加 `--ffmpeg "C:/工具/ffmpeg.exe" --ffprobe "C:/工具/ffprobe.exe"`。示例只表示参数写法，不假定文件存在。

初始化脚本会检查字体、音轨、帧率，创建空项目配置；**不会假装自动完成字幕、选素材或剪辑**。当前本地渲染器仅验证30fps。其他帧率可先明确生成30fps派生文件，保留源文件，并注明转换；不能声称升帧增加细节。

可加 `--style-id CY-001` 选择风格，省略则读取风格索引的默认编号。已有身份配置可加 `--identity-profile "/work/我的身份.json"`，只读取其中 identity、vertical、footer 字段。禹橙本地工作流保留已确认身份与AI标识，其他使用者填自己的信息；身份配置可留在媒体库，不提交公开仓库。

每个项目建议：`input/`（或原片只读引用）、`analysis/`、`downloads/`、`subtitles/`、`preview/`、`edit-plan.json`、`assets.json`。记录剩余空间；不要为短片盲目下载大量4K。可写目录必须由当前环境实际允许。

## 首次必须知道的素材信息

原片路径或真实附件、素材目录、输出位置、标题/主题。身份条内容未知时先留空；已有素材和标题可推导时先行动。文稿是可选校对依据，原片可先转写。其他可选：平台、自然/稳重等节奏、目标时长、音乐、是否需要原生剪辑台。默认不加音乐。

完成环境检测后，向用户简报“已可执行/缺哪些”，不要重复索取已有资料。把机器相关路径放项目配置里，不写回通用技能。
