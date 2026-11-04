# 源码迁移与 Skills CLI 验证

日期：2026-11-04（Asia/Shanghai）。源码包装版本2.0.1；原ZIP与视觉风格2.0.0保留。

## 已实际通过

| 检查 | 结果和范围 |
|---|---|
| ZIP解包与保留 | 33个原技能文件全部存在；32个逐字节不变，SKILL.md仅新增版本元数据并修正安装后README依赖说明 |
| 原脚本完整性 | 8个Python脚本均与原ZIP逐字节一致，无删减 |
| YAML与结构 | name匹配目录、description有效、metadata为字符串；skill-creator检查通过 |
| 相对链接 | 31处Markdown/HTML/风格索引路径通过；JSON均可解析，8个脚本AST语法检查通过 |
| 本地发现 | Skills CLI 1.7.6发现恰好1个技能chenyi-editing |
| 实际npx安装 | 项目级Codex安装成功，copy模式，33个安装文件与源码逐字节一致 |
| 安装登记 | skills list --agent codex --json返回项目级chenyi-editing，status=tracked |
| 从安装目录执行 | 原smoke_test.py的8项合成音视频行为检查通过，包含全片解码 |

环境：Windows，Node.js 24.22.1，Skills CLI 1.7.6，Python 3.12.14。测试使用现有FFmpeg、ffprobe、Pillow和思源宋体，不修改系统默认Node，不覆盖用户已有全局技能。

## 复现命令

在独立空测试目录，以满足要求的Node运行：

```sh
npx skills@1.7.6 add /absolute/path/to/repository --list
npx skills@1.7.6 add /absolute/path/to/repository --skill chenyi-editing --agent codex --copy --yes --json
npx skills@1.7.6 list --agent codex --json
```

`--list`不可与`--json`组合；本次最初尝试这一组合被CLI拒绝，随后改用上面的独立命令通过。最初用系统npm下载测试CLI时检测到Node20产生engine警告；实际识别/安装运行均使用已有Node24。不将这些失败尝试记为通过。

安装后的脚本测试（替换工具和字体路径）：

```sh
python .agents/skills/chenyi-editing/scripts/smoke_test.py --work /new/test-output --font /fonts/SourceHanSerifSC-Heavy.otf --ffmpeg /tools/ffmpeg --ffprobe /tools/ffprobe
```

合成素材只验证同步与可执行性，不证明真实口播气口自然度。

## 远程检查

源码推送后执行并记录。当前：待验证，不能以本地安装代替GitHub远程安装通过。

## 未测试 / 需人工完成

- macOS、Linux与其他agent客户端的实际运行。
- Codex客户端新会话自动发现和真实剪辑任务：本次只验证CLI登记、文件落盘及安装脚本可执行。
- 全局安装/覆盖升级：本次不覆盖用户现有技能；使用者需先备份同名副本。
- 真实素材的完整听审、字体与B-roll许可、ASR模型下载/硬件兼容性、ChatCut账号及工程编辑验证。
- 仓库所有者决定是否及采用何种开源许可证；本次未添加LICENSE或license字段。

原ZIP SHA256：`09db81ae6c01ebc3d83177300e9953be7a2f418e7bc39e4f454afa662dca7b30`。原SHA256SUMS.json只对应原ZIP内文件，不冒充当前源码的清单。
