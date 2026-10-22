# BaoCut 课堂笔记 Skill 与麦田五课私有分享包

**第一次使用请先读 [Agent 安装与运行手册](docs/agent-setup.md)**：包含 BaoCut 官方下载、依赖、版本分流、配置、可运行示例与故障处理。

只看课程：下载/克隆并解压整个仓库，打开 [课程导航](notes/课程导航.html)。五课 HTML 为当前本地稳定成品的原样副本，图片已内嵌，正文可离线阅读。未包含扩展访谈、25 本书、原视频或转写缓存。

本次发布检查见 [2026-10-22 发布验证](docs/release-validation.md)。

把已有课程转写、讲义和阅读材料整理成有时间码、来源标注、配图与自测的离线 HTML。本包是供 Agent 使用的工作流程和本地辅助脚本，**不是一键下载、ASR 或自动写作程序**，也不是 BaoCut 官方发行包。

Python 脚本负责分块、验证和渲染；你或 Agent 负责实际阅读、语义整理和视觉核对。要从视频开始，需另外安装兼容的 BaoCut、Agent 及其所需依赖。只有现成 transcript.json 时，也可以直接离线使用本包。

> 本包没有添加 LICENSE，也没有替权利人授予开源许可。公开可见不等于获得任意使用、修改或再分发授权。第三方软件、模型和课程资料各自遵守原有条款；本包不捆绑第三方软件或二进制；五份课程笔记和内嵌图片保留原有来源归属。

## 先看效果：无需 BaoCut、无需 API 密钥

下载仓库 ZIP 并解压，进入包含此 README 的目录。直接打开 [合成示例预览](examples/synthetic/preview.html)，或在终端重新生成：

```sh
python3 --version
python3 tools/run_demo.py
```

然后用浏览器打开 `build/demo/notes.html`。Windows 可将 `python3` 换为 `py -3`。输出目录已存在时程序会拒绝覆盖，可改用 `python3 tools/run_demo.py --out build/demo-2`。

演示文字、虚拟时间轴与方块图都是合成数据；画面上的“视频原帧”“课堂时间”只演示数据字段，不代表存在实际课程。演示不下载视频、不启动 BaoCut、不发起模型请求。可运行脚本仅需 **Python 3.9+ 标准库**，不需要 `pip install`。已验证版本为 macOS arm64 上 Python 3.9.6；其他系统和 Python 版本见[测试范围](docs/validation.md)。

## 安装到 Agent

安装前自行确认本包的使用授权。安装工具只复制 `skills/baocut-course-notes`，不会安装 BaoCut、模型或更改 Agent 凭据。

从仓库根目录执行：

```sh
python3 tools/install_skill.py
```

默认目标为 `~/.agents/skills/baocut-course-notes`。已有同名目录或链接时会明确退出，不覆盖你的版本。安装后刷新或重启 Agent，确认可发现 `baocut-course-notes`。不同 Agent 的发现目录可能不同；可按实际环境指定完整目标目录，例如已使用 `~/.codex/skills` 的环境：

```sh
python3 tools/install_skill.py --dest ~/.codex/skills/baocut-course-notes
```

也可以手动把整个 `skills/baocut-course-notes` 文件夹放入 Agent 支持的 Skill 目录，保留其中相对结构。不要只复制 SKILL.md。本轮只在隔离临时目录验证安装和拒绝覆盖，未修改本机现有 Agent 安装。

## 如何调用

在能发现此 Skill 的 Agent 中发送，例如：

```text
使用 $baocut-course-notes 整理我提供的 transcript.json。
本次只做离线转写笔记，不下载、不转写新媒体。
完整阅读每个分块，按真实主题写 notes.json 和 reading-layout.json，
生成单课 HTML，并如实列出未检查的视频、论文和设备范围。
```

如需整理真实视频，在确认有权使用资料且 BaoCut 可用后，可发送：

```text
使用 $baocut-course-notes 整理这个视频：[视频链接或本地路径]。
先核对实际 BaoCut 版本、宿主和项目状态，复用已完成的媒体与转写。
生成有证据与来源区分的详细单课 HTML；缺少材料或未完成验收时明确说明。
```

视频链接不会使 Python 渲染脚本自行下载。完整课程任务由 Agent 协调 BaoCut、阅读与审查；需要真实画面、推荐材料和设备检查时，结构校验通过不能代替这些工作。

## 手动处理自己的导出

以下命令在仓库根目录执行；先把有权使用的原始导出放到独立 `my-run/` 中，不操作 BaoCut 项目内部文件。

1. 导出至少应有 `sentences` 数组，每句含唯一字符串 `id`、以秒为单位的 `start/end`、纯文本 `text`。可参考[合成转写](examples/synthetic/transcript.json)。新 BaoCut 导出如不满足此结构，需要另外核对和适配，不能直接假定兼容。
2. 分块后按 `chunks/index.json` 完整读取对应文件。分块是阅读单位，不应机械当作章节。

```sh
python3 skills/baocut-course-notes/scripts/course_notes.py chunks --input my-run/transcript.json --out my-run/chunks
```

3. 你或 Agent 根据阅读结果编写 `my-run/notes.json` 和 `my-run/reading-layout.json`。参照[数据合同](skills/baocut-course-notes/references/contract.md)、[阅读布局](skills/baocut-course-notes/references/editorial-layout.md)及合成示例。`read_chunks`、审查状态不能由脚本冒填；布局 SHA 必须绑定实际 notes 字节。
4. 渲染详细 HTML：

```sh
python3 skills/baocut-course-notes/scripts/course_notes.py render --notes my-run/notes.json --index my-run/chunks/index.json --layout my-run/reading-layout.json --require-layout --out my-run/notes.html
```

notes 修改后，先复核布局受影响的内容，再刷新 SHA 和渲染。图片必须在 run 目录内，格式为 PNG/JPEG/WebP；生成的 HTML 内嵌图片、样式和脚本，正文可离线读，外部来源链接仍需联网。

## BaoCut 版本与第三方依赖

本 Skill 中旧版 `bcut-cli` 工作流对应的已安装样本为 App **2.1.0 build 54 / spec 1.249.0**，本轮只运行 `version` 与 `--help`。这不是新机器端到端兼容承诺。当前上游使用新的 `baocut` 接口；不要把上游 `main` 的安装步骤和旧 `bcut-cli` 命令混在一起。

BaoCut 的应用内 `app-release.json` 可能滞后；本次它写 2.0.0 build 52，与实际二进制和 Info.plist 不同。以实际运行结果、应用版本及对应厂商文档一起核对。

[依赖与官方来源](docs/dependencies.md)列出核验日期、上游固定版本、旧档案分支及许可链接。BaoCut、FFmpeg、模型、Agent 的安装和账号配置均由使用者单独完成。没有兼容运行时时，先使用离线示例，不要为了跑本包盲目升级或替换现有运行时。

## 功能与文件

- `skills/baocut-course-notes/`：完整 Skill，包含 27 个当前源文件。脚本和模板保持源文件字节，3 份文字/经验文件经过通用化处理。
- `examples/synthetic/`：原创合成输入、布局、示意图及静态预览。
- `tools/`：离线演示、拒绝覆盖的 Skill 安装工具及包校验工具。
- `docs/source-manifest.json`：当前源快照及分享副本 SHA-256，不含个人路径。
- `docs/validation.md`：实际测试和未测范围；`PACKAGE-MANIFEST.json` 是包内文件校验清单。

原功能包括 `chunks/render/record/remember`、布局校验、材料阅读台账校验、图片审查、视频覆盖和依赖快照追踪。`remember` 只在使用者明确授权时调用；它不会因生成笔记而自动执行。本包测试中的相关写入仅发生在临时测试目录。

运行原有测试：

```sh
python3 -B -m unittest discover -s skills/baocut-course-notes/scripts -p 'test_*.py' -v
```

本次基于当前源的 69 项测试通过。检查的是结构、哈希绑定、输入拒绝和渲染行为，不能证明任意真实课程内容完整或准确。

## 版权与分享边界

没有为本包添加 MIT、Apache 或其他开源许可，也没有把 BaoCut 的许可复制为本包许可。现有可识别的版权/归属内容未删除；通用质量要求保留，个人反馈和个人使用记录未收录；本次另附用户指定的五份课程笔记。后续是否授权他人修改、再分发或商业使用，须由权利人明确决定。

仅处理有权访问和使用的媒体与材料；分享笔记或图片时保留必要来源，并遵守课程、论文、平台和模型的具体条款。此处不会提供绕过付费、登录或其他访问限制的方法。
