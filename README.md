# Claude Desktop macOS 中文补丁

为 macOS 版 Claude Desktop 添加简体中文资源、语言白名单补丁、部分硬编码界面翻译，以及可切换的中文字体设置。

本项目是非官方的本地应用补丁。代码和资源按 [个人非商业许可](LICENSE.md) 提供；修改应用包会受到 Claude 版本和 macOS 权限的影响。

## 功能与适用环境

- 写入桌面壳层、前端和 Statsig 中文 JSON 资源。
- 在前端入口脚本的语言白名单中加入 `zh-CN`。
- 替换已知 JS chunk 中的部分导航文案。
- 注入右下角「字体」按钮，支持系统字体、自定义字体名及本地 `.ttf`／`.otf` 文件。

需要 macOS、Python 3 和已安装的 Claude Desktop，默认应用路径为 `/Applications/Claude.app`。项目此前记录的验证版本为 **1.5354.0**；这不代表适配后续所有版本。变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 快速开始：创建汉化副本

此方式保留原版应用包，方便遇到兼容问题时切回原版。副本与原版仍可能共享用户配置，不等于隔离的用户环境。

```bash
git clone https://github.com/1m01m0/claude-desktop_mac-zh_cn.git
cd claude-desktop_mac-zh_cn
python3 tools/validate_resources.py
```

退出 Claude，确认 `~/Applications/Claude-zh-CN.app` 不是需要保留的已有副本，再复制：

```bash
mkdir -p "$HOME/Applications"
ditto --noextattr --noqtn --noacl --nopersistRootless \
  /Applications/Claude.app \
  "$HOME/Applications/Claude-zh-CN.app"

python3 patch_claude_mac_json_only.py \
  --app-dir "$HOME/Applications/Claude-zh-CN.app/Contents/Resources"
python3 patch_chunks_mac.py \
  --app-dir "$HOME/Applications/Claude-zh-CN.app/Contents/Resources"

open -n "$HOME/Applications/Claude-zh-CN.app"
```

在副本第一次启动前完成两个补丁步骤。检查每条命令的输出；白名单或 chunk 未匹配时，不能仅凭资源文件已复制判断全部成功。

### 直接修改原版

若终端有权写入原版应用包，可运行交互菜单：

```bash
bash claude-zh-cn.sh
```

选择安装、状态检查或卸载。安装流程会关闭 Claude 并请求管理员权限。若出现 `Operation not permitted`，先检查终端的应用管理权限，或采用用户目录副本方式；`sudo` 不保证能绕过系统保护。

脚本使用 `Path.home()` 定位备份与用户配置。管理员身份运行时，实际主目录可能与当前登录用户不同，应核对输出和目标路径，避免把配置写入错误用户目录。

## 安装后检查

1. 确认运行的是预期应用，可用 `pgrep -fl Claude` 查看进程路径。
2. 检查「新建会话」「已安排」「自定义」「已固定」「最近」等导航文案。
3. 检查右下角「字体」按钮是否存在并可操作。
4. 如果仍显示英文，核对实际用户数据目录及 `locale`。

资源文件检查示例（副本方式）：

```bash
test -f "$HOME/Applications/Claude-zh-CN.app/Contents/Resources/zh-CN.json"
test -f "$HOME/Applications/Claude-zh-CN.app/Contents/Resources/ion-dist/i18n/zh-CN.json"
test -f "$HOME/Applications/Claude-zh-CN.app/Contents/Resources/ion-dist/i18n/statsig/zh-CN.json"
```

这些检查确认文件存在，不代表所有界面均已翻译。

## 用户配置与字体

资源脚本默认修改当前执行用户的：

```text
~/Library/Application Support/Claude/config.json
```

该文件存在且能解析时，脚本写入 `locale=zh-CN`；缺失或无法解析时会跳过。字体设置使用浏览器 `localStorage`，并通过 `claudeZhCnFont` 配置字段提供镜像。

第三方推理模式可能使用 `~/Library/Application Support/Claude-3p/`。先检查实际进程的 `--user-data-dir`，再备份并编辑对应 `config.json`，将以下字段合并到现有对象中，保留其他配置：

```json
{
  "locale": "zh-CN"
}
```

本补丁不配置推理服务或 API 凭证。

## 备份、恢复与更新

补丁备份位于执行用户的：

```text
~/Library/Application Support/Claude-zh-CN-backup/
├── json-only/
└── chunks/
```

备份按文件相对路径保存，不按应用版本或副本路径隔离。更新版本前保留独立的原版应用备份；不要假定一个备份目录可正确恢复任意版本或多个副本。

### 恢复补丁

退出 Claude，针对实际打补丁的 Resources 目录运行：

```bash
python3 restore_claude_mac.py \
  --app-dir "$HOME/Applications/Claude-zh-CN.app/Contents/Resources"
```

修改原版时将路径换为 `/Applications/Claude.app/Contents/Resources`，并确保写入权限及备份所在用户一致。

恢复脚本在有备份时还原备份文件；没有备份时尝试删除中文资源并清理白名单，同时移除默认用户配置中的 `locale` 和 `claudeZhCnFont`。它不会保证删除所有新建资源或还原没有备份的硬编码替换。恢复后应检查实际界面；有疑问时使用干净原版应用。

使用副本时，也可以退出应用后通过 Finder 移除副本，再打开原版。移除副本不会自动清除共享用户配置。

### Claude 更新后

1. 先确认未修改的新版应用能正常启动。
2. 保存需要保留的备份，重新创建干净副本。
3. 运行两个补丁脚本，检查未匹配或跳过提示。
4. 验证中文导航和字体功能。

新版 JS 文件名、结构和翻译 key 可能变化；重新运行旧补丁不一定能解决新增英文文案，需要更新资源或 chunk 匹配规则。

## 项目结构与维护

| 路径 | 用途 |
| --- | --- |
| [claude-zh-cn.sh](claude-zh-cn.sh) | 交互式安装、卸载、状态检查 |
| [resources/](resources/) | 桌面、前端、Statsig 翻译资源 |
| [patch_claude_mac_json_only.py](patch_claude_mac_json_only.py) | JSON 资源、白名单与 locale |
| [patch_chunks_mac.py](patch_chunks_mac.py) | 硬编码文案与字体运行时 |
| [restore_claude_mac.py](restore_claude_mac.py) | 从备份恢复及配置清理 |
| [tools/](tools/) | 资源验证、覆盖检查和历史行为测试 |

提交翻译或补丁变更前运行：

```bash
python3 tools/validate_resources.py
```

它验证三个资源文件是合法 JSON 对象，不能证明翻译完整性或新版本兼容性。`tools/test_patch_behaviors.py` 仍引用仓库中不存在的 Windows 脚本，不应将其视为可用的 macOS 回归测试套件。报告兼容问题时附上应用版本、macOS 版本、安装方式和脱敏错误输出。

## 常见问题

| 现象 | 检查方向 |
| --- | --- |
| 写入被拒绝 | 退出 Claude，检查应用管理权限；必要时使用干净的用户目录副本 |
| 资源存在但仍为英文 | 确认运行路径、实际用户数据目录和 locale；检查白名单补丁输出 |
| 少数导航仍为英文 | 新版 chunk 或 i18n key 变化；用户自己的会话名不会自动翻译 |
| 字体未变化 | 检查字体按钮是否注入、字体是否可用，以及 localStorage／配置状态 |
| 更新后失效 | 从新版原版重新创建副本，并检查补丁是否匹配 |

DevTools、Electron 原生菜单和系统级弹窗不一定受前端 i18n 控制。

## 许可与致谢

仅限个人学习、研究和非商业使用，商业用途须经作者书面授权。软件按原样提供，完整条款见 [LICENSE.md](LICENSE.md)。

保留以下来源致谢：

- [javaht/claude-desktop-zh-cn](https://github.com/javaht/claude-desktop-zh-cn)：中文翻译资源。
- [Jyy1529/claude-desktop_win-zh_cn](https://github.com/Jyy1529/claude-desktop_win-zh_cn)：Windows 实现参考。
