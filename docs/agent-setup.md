# 给朋友和 Agent 的安装与运行手册

核验日期：2026-10-22。先完成离线合成示例，再接真实媒体。此仓库不包含 BaoCut 应用、模型、账号或课程原始视频。

## 0. 先确定要做什么

只阅读五课：解压完整仓库，双击 `notes/课程导航.html`，无需安装依赖。GitHub 文件页不等于 HTML 网页预览。需要访问私有仓库的朋友须由仓库所有者另行授权；本发布不自动邀请任何人。

运行笔记工具：需要 Python 3.9+、现代浏览器；脚本只使用标准库。实际测试平台为 macOS arm64，Windows/Linux 的本包脚本未实机验证。Windows 命令行把 `python3` 改为 `py -3`。Python 安装器从 https://www.python.org/downloads/ 获取；不要在不存在的 Python 上直接执行 pip 命令，本包无需 pip。

从视频开始：另需 BaoCut、兼容的 Agent 登录、模型和媒体工具。**本 Skill 的 BaoCut 自动化流程针对旧 `bcut-cli`，不能直接套到新版 `baocut`。** 最新版可以先通过其官方工作流导出转写，再走本包离线步骤；导出数据必须核对合同，尚未完成新接口端到端适配。

## 1. 下载、预检、离线跑通（不需要 BaoCut 账号）

从本私有仓库 Code → Download ZIP 解压。或在已有 GitHub 访问权限时复制仓库页面给出的 clone URL，执行 `git clone <仓库URL>`；不要把 token 写进 URL。

终端进入仓库根目录：

```sh
python3 --version
python3 tools/verify_package.py
python3 -B -m unittest discover -s skills/baocut-course-notes/scripts -p 'test_*.py' -v
python3 tools/run_demo.py --out build/first-run
```

预期：校验 passed、69 项测试通过、出现 `build/first-run/notes.html`。打开该 HTML，应有两节正文、一幅合成图、自测折叠块和可点击目录。这个 smoke test 不下载、不调用模型；仅证明数据处理和渲染能运行。目录已存在时换一个新的 `--out`，不要删除他人的输出或加覆盖参数。

## 2. 安装这份课程笔记 Skill

```sh
python3 tools/install_skill.py --dest ~/.agents/skills/baocut-course-notes
```

工具会拒绝覆盖已存在目录。若 Agent 实际使用 `~/.codex/skills`，改用：

```sh
python3 tools/install_skill.py --dest ~/.codex/skills/baocut-course-notes
```

以上二选一。刷新/重启 Agent，确认能发现 skill；若不能，检查其支持的发现目录。完整目录包含 `SKILL.md`、`scripts/`、`assets/`、`references/`、`agents/`，不能只复制一个 Markdown。与 BaoCut 官方的 `baocut` Skill 是两个不同目录，不能互相覆盖。

## 3. BaoCut 从哪里下载，哪些地方必须自己授权

官方入口：[下载站](https://baocut.com/#download)、[GitHub Releases](https://github.com/JimLiu/baocut/releases)。2026-10-22 官网显示 3.9.0；动态下载入口会随发行更新。macOS 官方包面向 macOS 14+ Apple Silicon；Windows 为 x64，CPU/CUDA/Vulkan 版本按硬件选择；Linux 发布安装包未验证。安装条件以所选发行说明为准。[官方说明](https://github.com/JimLiu/baocut#download-and-install)

macOS：下载官方 DMG，核对对应 release 校验和后打开，拖入 Applications。Windows：按发行说明安装 Visual C++ x64 运行库，然后运行安装器；本手册未实测 Windows 安装。

可在 macOS 使用以下下载命令（只下载，不自动执行安装器）：

```sh
curl -fL https://baocut.com/download/mac-dmg -o BaoCut.dmg
shasum -a 256 BaoCut.dmg
open BaoCut.dmg
```

将哈希与此次实际下载的发行资产比对；不匹配就停止。不要把旧版 hash 用于动态最新版。以上下载链接经官方文档确认，本次没有重新下载或安装应用。

Agent 功能需要使用者自己的受支持 Agent 引擎及登录。请由用户在官方客户端完成登录、系统权限、模型下载许可及预算选择。打开 App 不等于模型/Agent 已就绪；远程模型可能收费，不能承诺无账号完整运行。不要复制发布者的凭据、Cookie、钥匙串、配置目录，也不要让 Agent 把秘密写进命令、日志或本仓库。

FFmpeg/ffprobe 是媒体准备依赖。官方入口：https://ffmpeg.org/download.html 。已有 Homebrew 的 macOS 可执行 `brew install ffmpeg`，然后验证：

```sh
ffmpeg -version
ffprobe -version
```

仅离线示例不需要这两个程序。不要为本包安装 Rust/Node 编译链；正常 BaoCut 桌面发行版包含自身运行组件。Windows/Linux 按官方发行说明配置工具 PATH，本次未验证。

## 4. 先辨认新旧接口，再选路径

### 新桌面版：只按匹配的官方 Skill 操作

macOS 已安装在默认位置时：

```sh
export BAOCUT_CLI='/Applications/BaoCut.app/Contents/MacOS/baocut-cli'
test -x "$BAOCUT_CLI"
"$BAOCUT_CLI" version
"$BAOCUT_CLI" --help
```

Windows 使用安装目录内的 `baocut.cmd`，完整路径从 App 的 Skills 页获取。路径不存在就停：旧包可能没有该入口，设置环境变量不会修好缺失文件。新入口经版本检查后，可由用户允许执行 `"$BAOCUT_CLI" skill install` 安装官方 `baocut` Skill；读取它并按它的工具目录导出转写。本包不提供猜测的新 API 媒体命令。[官方 CLI 入口文档](https://github.com/JimLiu/baocut/blob/main/apps/desktop/README.md#外部-agent-与-cli)

### 已有旧版 2.1.0：本机验证过的 launcher

本次只读检查确认：2.1.0 / spec 1.249.0 / Apple Silicon。以下是已安装旧版的路径模板，并非旧版下载保证；官方能否重新提供这一旧版未验证，不要从第三方下载不明二进制。

```sh
export BAOCUT_SKILL_ROOT='/Applications/BaoCut.app/Contents/Resources/skills/baocut'
test -f "$BAOCUT_SKILL_ROOT/references/hosts.md"
BAOCUT_SKILL_NO_LINK=1 "$BAOCUT_SKILL_ROOT/bin/bcut-cli" --json version
BAOCUT_SKILL_NO_LINK=1 "$BAOCUT_SKILL_ROOT/bin/bcut-cli" --help
```

`BAOCUT_SKILL_ROOT` 指向**官方 BaoCut Skill**，不是本仓库的课程笔记 Skill。安装在别处时只调整路径。`BAOCUT_SKILL_NO_LINK=1` 避免版本检查创建缓存链接。`BAOCUT_HOST`、`BAOCUT_PROJECT` 如由 App 设置，必须尊重宿主绑定，不能清空以绕过限制；App 内用它给的 `$BAOCUT_CLI`，不要管理 runtime。

终端 Agent 且 `BAOCUT_HOST` 未设置时，先读官方 `references/hosts.md`、`references/projects.md`。确认用户已允许真实媒体处理后：

```sh
"$BAOCUT_SKILL_ROOT/bin/bcut-cli" serve --ensure
"$BAOCUT_SKILL_ROOT/bin/bcut-cli" --json spec
"$BAOCUT_SKILL_ROOT/bin/bcut-cli" --json doctor
"$BAOCUT_SKILL_ROOT/bin/bcut-cli" --json project list
"$BAOCUT_SKILL_ROOT/bin/bcut-cli" --json project dir
```

这些命令会连接或启动 runtime；在 sandbox 中启动失败应走宿主审批，不能换程序绕过。复用匹配媒体的现有项目。没有项目且确需创建时，`PROJECT_PATH` 使用上一步返回的真实库目录下一个新的 `.bcut` 路径；`MEDIA_PATH` 是用户有权处理的文件：

```sh
MEDIA_PATH='/absolute/path/to/your-video.mp4'
PROJECT_PATH='/actual/project/library/Example.bcut'
RUN_DIR='/absolute/path/to/new-note-run'
mkdir -p "$RUN_DIR"
"$BAOCUT_SKILL_ROOT/bin/bcut-cli" transcribe "$MEDIA_PATH" --project "$PROJECT_PATH" --jsonl
"$BAOCUT_SKILL_ROOT/bin/bcut-cli" export "$PROJECT_PATH" --to json --mode original -o "$RUN_DIR/transcript.json" --json
```

上述参数已对照本机旧版 help；本次没有实际转写或导出课程。转写模型和可用资源由 doctor/官方 Skill 确认，不能看到失败就自动切收费 API。`--llm agent` 只用于实际 help 支持它的命令（例如 polish/translate）；本机 `transcribe --help` 不含此参数，不能添加。需要 Agent 任务提交时遵从对应官方协议，不另调供应商。runtime 仅在本任务确实启动且 App 未使用时按官方 hosts 文档停止。

## 5. 自己的输入到 HTML

把导出复制到仓库外独立 run，保留原件。先将 `RUN_DIR` 设置为该目录的绝对路径（例如 `RUN_DIR='/absolute/path/to/new-note-run'`），下列命令仍在仓库根目录运行。`transcript.json` 必须有 `sentences` 数组，每句有唯一字符串 `id`、秒数 `start/end` 和 `text`。新版导出不能只改文件名假装兼容。

```sh
python3 skills/baocut-course-notes/scripts/course_notes.py chunks --input "$RUN_DIR/transcript.json" --out "$RUN_DIR/chunks"
```

逐块读取 `$RUN_DIR/chunks/index.json` 指向的所有分块。然后按 `references/contract.md` 和 `references/editorial-layout.md` 编写 `notes.json`、`reading-layout.json`，参考 `examples/synthetic/`。这些内容需要真正阅读与写作，脚本不会自动完成。布局里的 SHA-256 绑定 notes 原始字节；正文改动后先复核布局再刷新哈希。

```sh
python3 skills/baocut-course-notes/scripts/validate_reading_layout.py --notes "$RUN_DIR/notes.json" --layout "$RUN_DIR/reading-layout.json"
python3 skills/baocut-course-notes/scripts/course_notes.py render --notes "$RUN_DIR/notes.json" --index "$RUN_DIR/chunks/index.json" --layout "$RUN_DIR/reading-layout.json" --require-layout --out "$RUN_DIR/notes.html"
```

图片放在 run 内，支持 PNG/JPEG/WebP；渲染结果内嵌图片/样式/脚本，来源外链仍需联网。完整性声明必须如实填写：未看视频不能标视觉通过，未读论文不能标材料阅读完成。

## 6. 恢复、资源和验收

合成示例通常只需数秒和少量磁盘；真实媒体处理时间取决于时长、硬件和模型。预留源视频、模型和抽帧空间，可能达到数 GB；本包不承诺固定内存或耗时。内嵌图片的 Base64 会使图片部分体积约增加三分之一。五课成品合计约 25.6 MB，不含原视频。

恢复前先读 run 的 index、events、review 和依赖哈希；确认旧任务没有仍在写入。旧版用 `jobs list --json`（先核对 help），先复用 fresh 转写与已通过阶段，从第一个未完成项继续，不重复整个课程。详见本 Skill 的 `references/batch-recovery.md` 和 `references/traceability.md`。

结构检查：运行 unittest、layout 校验；材料、图片、视频覆盖分别使用 `validate_materials.py`、`validate_image_audit.py`、`validate_visual_coverage.py`，先读对应 `--help` 与合同。真实 BaoCut 项目按该版本官方命令执行 strict 检查。最后实际在宽屏/窄屏检查目录跳转、图片放大、自测折叠、打印、控制台与离线图像。结构通过不等于内容正确。

| 现象 | 下一步 |
| --- | --- |
| Python 语法/API 失败 | 核对 3.9+ 与实际解释器；不要先 pip 安装随机包 |
| install_skill 拒绝目录 | 保留现有安装，比较版本后请用户选择新路径或明确升级 |
| CLI 文件不存在/spec 不匹配 | 分辨新旧接口，读取对应官方文档，停止旧命令链 |
| app_not_installed/需要登录 | 用户从官方安装或自行登录；不借用其他人的配置 |
| runtime sandbox/GPU 错误 | 按宿主批准方式或请用户打开 App，不换引擎绕过 |
| 模型下载、403、限额 | 记录失败；检查官方源/用户权限，不重复付费请求 |
| notes SHA 不一致 | 复核内容和布局，再计算哈希；不能仅填一个假值 |
| 图片路径越界或丢失 | 把有权使用的图片复制进 run 并修正相对路径 |
| HTML 来源外链离线打不开 | 正文和内嵌图片应能离线读，外部来源需联网 |

## 7. 可复制给朋友 Agent 的执行约定

> 先读取 README、此手册与 skills/baocut-course-notes/SKILL.md。只在新 run 目录操作；先跑合成示例与 69 项测试，再安装到用户实际使用的 Skill 目录。只阅读现有笔记时不安装 BaoCut。真实视频任务先核对授权范围、BaoCut 实际版本、宿主、媒体指纹、模型和资源；最新 baocut 与旧 bcut-cli 不混用。缺账号/付费许可/覆盖许可/兼容导出合同就停相关步骤并说明，继续能做的离线工作。未经用户明确授权不写 memory、不建自动任务、不上传/公开、不邀请人、不覆盖项目。不得伪造阅读记录或检查结果。交付 HTML、来源、哈希、已验和未验范围。
