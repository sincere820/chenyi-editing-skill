# 陈一剪辑 · Agent Skill

把口播原片剪成竖屏成片：语义分句、自然气口、白黄标题、胸口字幕、匹配且尽量不重复的 B-roll、身份与 AI 标识。默认本地 MP4 + 字幕 + 渲染源，需要可视化剪辑台时再使用 ChatCut。

完整源码位于 [`skills/chenyi-editing/`](skills/chenyi-editing/)，遵循 [Agent Skills 格式](https://agentskills.io/specification)。所有 v2.0.0 技能包文件均保留；8 个原有 Python 脚本保持逐字节一致。本次源码包装版本为 2.0.1，视觉风格 CY-001 仍为 2.0.0。

## 一键安装到 Codex

先准备 **Node.js ≥22.20.0、npm/npx、Git**，并确保能访问 npm registry 和 GitHub。以下命令从你的项目目录运行：

```sh
npx skills add sincere820/chenyi-editing-skill --skill chenyi-editing --agent codex
```

先查看可发现的技能，不安装：

```sh
npx skills add sincere820/chenyi-editing-skill --list
```

要在所有项目使用，加 `--global`：

```sh
npx skills add sincere820/chenyi-editing-skill --skill chenyi-editing --agent codex --global
```

自动化、无符号链接安装（执行前确保同名技能已备份）：

```sh
npx skills add sincere820/chenyi-editing-skill --skill chenyi-editing --agent codex --copy --yes
```

安装命令来自 [Skills CLI 官方文档](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)。本次验证使用 `skills@1.7.6`；可将上面命令里的 `skills` 替换为 `skills@1.7.6` 来固定版本。未指定版本的 npx 会使用届时版本，其参数和要求可能变化。

Skills CLI 1.7.6 对 Codex 的项目目录是 `.agents/skills/chenyi-editing`，全局目录是 `~/.agents/skills/chenyi-editing`。本机早期手动安装在 `~/.codex/skills` 的副本不会被此次隔离测试覆盖；升级已有安装时先检查同名重复副本，不自动删除。详见 [CLI 的 agent 路径表](https://github.com/vercel-labs/skills/blob/main/docs/agents.md)。

**安装 skill 只复制指导文件与脚本，不会自动装好 Python、FFmpeg、字体、ASR 模型，也不会直接开始剪片。**

## Codex 使用教程

1. 在安装技能的项目中打开 Codex。安装后新开一个会话，使客户端重新发现技能；用 `npx skills list --agent codex` 检查安装结果，全局安装加 `--global`。
2. 输入 `$chenyi-editing` 明确调用。让 agent 先读取 SKILL.md，再检查视频、素材、字体及执行工具是否可用。
3. 提供原片路径、素材目录、输出目录、标题；逐字稿可作为校对依据，不能代替实际音频时间码。桌面本地路径需要在该 agent 的环境里真实可读，云端会话不会自动看见你的 E 盘。
4. 先检查代表段预览，再渲染全片。真实切点、素材来源和验收状态都保存进项目；没有听音能力时，切点保留待审，不宣称已经听过。

可直接使用：

> $chenyi-editing 使用 CY-001。原片：[路径]；B-roll：[目录]；输出：[目录]；标题：[标题]。保留原口播，听审后收紧无意义长空白并保留自然呼吸；素材尽量丰富且不重复。沿用我已确认的身份与AI标识，先出预览，再交付MP4、字幕和渲染源。需要ChatCut剪辑台时我会另说。

Codex 的技能加载方式与可用执行权限以当前客户端为准，参考 [OpenAI 官方技能说明](https://developers.openai.com/codex/skills)。本仓库验证 CLI 安装落盘和可读取性，不把它说成已经在所有 Codex 客户端中自动运行成功。

## 实际剪辑的依赖与前提

| 用途 | 需要 | 是否自动安装 |
|---|---|---|
| Skills CLI 安装 | Node.js ≥22.20、npm/npx、Git、npm/GitHub 网络 | npx 获取 CLI；不升级系统 Node |
| 视频渲染 | Python 3.10+、Pillow `>=10,<13`、FFmpeg、ffprobe | 手动或由 agent 在授权范围内准备 |
| 字幕与图像 | FFmpeg 含 libass、libx264、AAC；思源宋体 SC Heavy 独立 OTF | 字体不随包提供 |
| 真实时间码 | 自有带词时间转写，或可选 Faster-Whisper `>=1.1,<2` | 模型首次下载另需网络与空间 |
| 气口复核 | 能理解音频的 agent 或用户听审 | 脚本检测不能替代听审 |
| 在线 B-roll | 允许下载的来源、许可和素材出处 | 不自动购买或绕过限制 |
| ChatCut | 接收方自己的账号、官方插件及实际可用工具 | 可选，默认不需要 |

在**安装后的技能目录**运行（将当前目录切换到包含 SKILL.md 的位置）：

```sh
python -m venv .venv
# Windows: .venv/Scripts/python.exe；macOS/Linux: .venv/bin/python
python -m pip install -r requirements.txt
# 仅选择本地转写时：
python -m pip install -r requirements-transcription.txt
ffmpeg -version
ffprobe -version
python scripts/style_registry.py list
```

上面的 pip 应使用虚拟环境内的 Python：先激活环境，或将 `python` 换成该环境解释器的完整路径；不会默认修改全局环境。完整前期准备、官方字体与工具下载入口见 [setup.md](skills/chenyi-editing/references/setup.md)。

初始化真实项目（替换所有示例路径）：

```sh
python scripts/init_project.py --source "/media/原片.mp4" --project "/work/新片" --font "/fonts/SourceHanSerifSC-Heavy.otf" --style-id CY-001 --title-top "标题第一行" --title-bottom "标题第二行"
```

工具不在 PATH 时追加 `--ffmpeg` 与 `--ffprobe` 的完整路径。初始化只做探测与配置，字幕、听审、素材选择仍由后续流程完成。[脚本接口](skills/chenyi-editing/references/schema.md)列出完整参数。

## 平台与已知限制

| 环境 | 状态 |
|---|---|
| Windows | 本次 CLI 测试和脚本验证记录见下方报告；中文路径已使用 |
| macOS / Linux | 使用可移植 Python/FFmpeg 路径设计，尚未本次实机验证 |
| 仅聊天、无本地执行权限的 agent | 可以分析文稿，不能实际生成成片 |
| 第三方可视化编辑器 | 需要真实工具连接和图层检查，本次不作连接成功承诺 |

渲染器当前针对 1080×1920 / 30fps 验证；其他帧率先明确生成派生文件。路径中的单引号等 FFmpeg 滤镜特殊字符尚有局限，使用普通输出目录；不重命名或覆盖用户源素材。Faster-Whisper 模型占用内存与下载空间，模型/硬件兼容性需接收方核对。ASS/SRT/JSON 是可重新渲染的源文件，不是剪映或 ChatCut 原生工程。

## 风格索引

默认 **CY-001｜陈一经典口播**：白黄常驻标题、粗宋单行胸口字幕、100%黑影、自然气口。新风格编号 CY-002、CY-003，须先完成参数和效果图再登记。

[查看带图风格索引](skills/chenyi-editing/styles/风格索引.md) · [风格参数](skills/chenyi-editing/styles/CY-001-陈一经典口播/profile.json)

<img src="CY-001-preview.jpg" width="300" alt="CY-001 合成背景排版示意">

本地可双击 `styles/index.html` 浏览画册。风格切换保留片名、身份、媒体路径及旧项目快照；具体见 [风格库管理](skills/chenyi-editing/references/style-library.md)。

## ZIP 下载仍可用

[下载原版 v2.0.0 ZIP](chenyi-editing-v2.0.0.zip) · [原版文件校验清单](SHA256SUMS.json)

原 ZIP 不修改；它是 2.0.0 历史快照。当前源码版的安装文档修正不追写进原 ZIP。仓库 Code → Download ZIP 可下载当前源码；解压后将 `skills/chenyi-editing` 复制到目标 agent 的技能目录。

## 验证结果

[本次安装与迁移验证报告](VALIDATION.md)区分本地发现、远程发现、安装、脚本测试和未测项目。原有脚本行为验证记录见 [validation.md](skills/chenyi-editing/references/validation.md)。

维护者可运行：

```sh
python -m pip install -r requirements-dev.txt
python tools/validate_skill.py
```

结构检查覆盖 YAML、相对文档链接、HTML资源、JSON、Python语法、原ZIP文件完整性以及8个脚本逐字节不变。示例 JSON 的 media/fonts 路径有意留作占位；不是缺失的发布资源。

## 版权与授权状态

**尚未添加开源许可证。** 公开仓库和可一键安装不等于获得开源许可。是否采用开源许可证由所有者另行决定；第三方工具、模型、字体与媒体遵循各自条件。详见 [版权与依赖说明](RIGHTS.md)。

仓库不含原片、真人截图、素材库、字体、模型、账号或用户机器配置。
