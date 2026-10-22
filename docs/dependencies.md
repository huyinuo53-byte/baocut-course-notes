> 这是 2026-10-11 的历史版本核验记录。2026-10-22 安装入口和新旧接口说明见 [当前安装手册](agent-setup.md)。不要把旧版信息当作最新发行。

# 依赖与版本边界

核验日期：2026-10-11。下列链接指向第三方自己的发行与条款；本包不包含其软件、厂商 Skill、安装器、字体或模型权重。

## 离线脚本

Python 3.9+ 标准库即可运行分块、渲染、验证、演示及安装复制工具。3.9 是所用 `Path.is_relative_to` 等 API 的最低版本要求；实际测试只覆盖 Python 3.9.6。浏览器需支持原生 `dialog`、`details` 和现代 CSS；演示正文与图片无需联网。

Python 官方来源：[python.org](https://www.python.org/downloads/)。媒体处理若需 FFmpeg，另见 [FFmpeg 官网](https://ffmpeg.org/)。不把 Python 和 FFmpeg 安装包放入本包。

## 本机已存在的旧版 BaoCut

本轮对既有应用做了安全只读检查，没有下载安装或替换版本，没有启动/停止 runtime、创建项目、下载课程、转写或调用付费接口。

| 证据 | 观察值 |
| --- | --- |
| launcher `--json version` | appVersion 2.1.0；specVersion 1.249.0；内部 version 0.1.0；release；aarch64-apple-darwin；MLX |
| CLI commit | `da3f29f45364de5fd8fdc2db0663318c1242ae10` |
| 应用 Info.plist | 2.1.0 / build 54 |
| 随包 app-release.json | 2.0.0 / build 52，属于滞后的发行元数据 |
| `--help` | 成功，确认旧接口存在 |

这里的“已知可用”仅指已安装且本轮版本/帮助查询成功；没有据此声称本次完成真实视频流水线测试。该版本能否从官方重新获得或在另一台电脑复现安装，本轮未验证。

确认自己已经安装了此旧版应用后，可把下例路径改为应用的真实位置（不要照抄为下载命令）：

```sh
BAOCUT_APP_PATH='/Applications/BaoCut.app'
BAOCUT_SKILL_NO_LINK=1 "$BAOCUT_APP_PATH/Contents/Resources/skills/baocut/bin/bcut-cli" --json version
BAOCUT_SKILL_NO_LINK=1 "$BAOCUT_APP_PATH/Contents/Resources/skills/baocut/bin/bcut-cli" --help
```

`BAOCUT_SKILL_NO_LINK=1` 是旧版 launcher 提供的无缓存链接选项，避免版本查询创建 CLI 缓存链接；不改变项目绑定或权限。先阅读已安装厂商 Skill 的 `references/hosts.md`；本机厂商文档表明 `version` 和 `--help` 不进入 runtime。其他看似只读的命令可能启动服务，不能把 `spec/project/check` 一概视为无副作用的版本查询。

## 上游已更换接口

- [BaoCut 官方站点](https://baocut.app/)与[官方仓库](https://github.com/JimLiu/baocut)是获取依赖的入口。
- 本次 API 观察到 `main` 为 [`a61ce203047ff32d96243cbc525ea6c6b38efc17`](https://github.com/JimLiu/baocut/tree/a61ce203047ff32d96243cbc525ea6c6b38efc17)。[该版本说明](https://github.com/JimLiu/baocut/blob/a61ce203047ff32d96243cbc525ea6c6b38efc17/README.md)采用 `baocut` CLI、Runtime 和工具目录；它与此 Skill 的旧版 `bcut-cli` 流程不同。未做新接口适配或端到端测试。
- [旧档案分支 archive/legacy-2026-10-07](https://github.com/JimLiu/baocut/tree/archive/legacy-2026-10-07)本次解析为 [`6caf38144d82008d80e53e5d8e2000b7c2d81710`](https://github.com/JimLiu/baocut/tree/6caf38144d82008d80e53e5d8e2000b7c2d81710)。档案 README 也描述了 `bin/baocut` resolver；档案分支不自动等于本机 App 随带的 `bin/bcut-cli`，本包不建议复制档案中的动态安装命令来猜配版本。
- 若使用新一代 BaoCut，先阅读对应发行版的实际文档，验证导出结构，再决定是否单独适配；现阶段可先导出或提供符合[数据合同](../skills/baocut-course-notes/references/contract.md)的 transcript.json，使用本包离线路径。

## 许可分别判断

当前上游 [LICENSE](https://github.com/JimLiu/baocut/blob/a61ce203047ff32d96243cbc525ea6c6b38efc17/LICENSE)标为 BaoCut Community License v1.0，日期为 2026-10-07，并将自身描述为 source-available。不能把它统一称作无条件开源授权；具体使用和分发以该文件为准。

旧档案 README 链接到自身 [LICENSE](https://github.com/JimLiu/baocut/blob/6caf38144d82008d80e53e5d8e2000b7c2d81710/LICENSE)，不代表本机某个二进制或后来版本当然沿用同一授权。当前 LICENSE 对第三方组件和历史版本另有说明。不要用第三方许可证替本包授予权利，也不要把此处简要依赖说明当作具体场景的许可结论。
