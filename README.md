# Claude Desktop macOS 中文补丁（zh-CN）

一个面向 macOS 版 Claude Desktop 的简体中文资源与补丁项目。

本项目会写入 Claude Desktop 的中文 i18n JSON 资源，修补前端语言白名单，并对少量没有走 i18n 的 JS chunk 硬编码文案做中文替换。同时注入一个中文字体运行时，方便在 Claude Desktop 右下角通过「字体」按钮调整中文显示效果。

> 本项目不是 Anthropic 官方发布内容。请只在你自己的设备上使用，并自行承担修改本地 app bundle 的兼容性风险。

## 已知限制

- Claude 更新后通常需要重新打补丁。
- macOS 可能阻止直接修改 `/Applications/Claude.app`。
- DevTools、Electron 原生菜单、部分系统级弹窗不一定受前端 i18n 控制。
- 当前测试脚本仍需要继续整理，建议发布前补齐 macOS 脚本的回归测试。
- 使用汉化副本时，最好只保留一个最终副本，避免 LaunchServices 或 Dock 中出现多个 Claude。

## 推荐安装方式

macOS 近几个版本会对 `/Applications/*.app` 施加更严格的应用管理保护。有些机器即使用 `sudo` 或 AppleScript 管理员授权，仍可能在写入 `/Applications/Claude.app` 时遇到：

```text
PermissionError: [Errno 1] Operation not permitted
```

因此本项目推荐两种方式：

- **方式 A：直接修改原版 `/Applications/Claude.app`**
  适合你的终端已经有权限写入 app bundle 的情况。优点是只有一个 Claude app；缺点是 Claude 更新后补丁会被覆盖。

- **方式 B：创建一个用户目录里的汉化副本**
  适合遇到 macOS 权限保护、公司 MDM 限制，或想保留原版 app 的情况。推荐最终保留：
  - `/Applications/Claude.app`：原版
  - `~/Applications/Claude-zh-CN.app`：汉化版

### 方式 A：直接修改原版

进入项目目录：

```bash
cd /path/to/claude-desktop_mac-zh_cn
chmod +x claude-zh-cn.sh
./claude-zh-cn.sh
```

菜单中选择「安装中文补丁」。脚本会自动：

1. 查找 Claude Desktop 的 Resources 目录。
2. 关闭正在运行的 Claude。
3. 写入 zh-CN JSON 资源。
4. 修补语言白名单。
5. 替换部分硬编码英文 UI 标签。
6. 注入中文字体设置按钮。
7. 写入 `locale=zh-CN`。
8. 将原始文件备份到 `~/Library/Application Support/Claude-zh-CN-backup/`。

也可以直接运行底层脚本：

```bash
sudo python3 patch_claude_mac_json_only.py --app-dir /Applications/Claude.app/Contents/Resources
sudo python3 patch_chunks_mac.py --app-dir /Applications/Claude.app/Contents/Resources
```

如果这一步出现 `Operation not permitted`，请改用方式 B。

### 方式 B：创建汉化副本

这种方式不修改 `/Applications/Claude.app` 本体，而是在用户目录中创建一个汉化版副本。

```bash
cd /path/to/claude-desktop_mac-zh_cn

# 关闭 Claude，避免正在运行的 app bundle 被系统保护或缓存
pkill -x Claude 2>/dev/null || true

# 创建副本。--noextattr / --noqtn 能减少从 /Applications 复制过来的保护属性
ditto --noextattr --noqtn --noacl --nopersistRootless \
  /Applications/Claude.app \
  "$HOME/Applications/Claude-zh-CN.app"

# 给副本打中文资源补丁
python3 patch_claude_mac_json_only.py \
  --app-dir "$HOME/Applications/Claude-zh-CN.app/Contents/Resources"

# 给副本打 JS chunk 和字体运行时补丁
python3 patch_chunks_mac.py \
  --app-dir "$HOME/Applications/Claude-zh-CN.app/Contents/Resources"

# 启动汉化版
open -n "$HOME/Applications/Claude-zh-CN.app"
```

如果你之前已经启动过某个汉化副本，macOS 可能也会对那个副本加上保护属性，导致后续补丁写入失败。最稳妥的做法是重新从原版复制一个干净副本，并在第一次启动前把所有补丁一次性打完。

## 安装后如何确认

可以用这些方式确认补丁是否生效：

```bash
# 检查中文资源是否存在
test -f "$HOME/Applications/Claude-zh-CN.app/Contents/Resources/zh-CN.json"
test -f "$HOME/Applications/Claude-zh-CN.app/Contents/Resources/ion-dist/i18n/zh-CN.json"

# 检查语言白名单是否包含 zh-CN
rg '"zh-CN"' "$HOME/Applications/Claude-zh-CN.app/Contents/Resources/ion-dist/assets/v1/index-"*.js

# 检查当前运行的 Claude 路径
pgrep -fl Claude
```

正常情况下，Claude 启动参数中会包含 `--lang=zh-CN`，界面中应能看到「新建会话」「已安排」「自定义」「已固定」「最近」等中文文案，右下角会出现「字体」按钮。

## 卸载 / 恢复

### 如果你直接修改了原版 `/Applications/Claude.app`

运行：

```bash
sudo python3 restore_claude_mac.py --app-dir /Applications/Claude.app/Contents/Resources
```

恢复脚本会：

1. 从 `~/Library/Application Support/Claude-zh-CN-backup/` 恢复原始文件。
2. 删除 zh-CN 资源文件。
3. 从语言白名单移除 `zh-CN`。
4. 移除 `locale` 和 `claudeZhCnFont` 配置。

### 如果你使用的是汉化副本

关闭 Claude 后删除副本即可：

```bash
pkill -x Claude 2>/dev/null || true
rm -rf "$HOME/Applications/Claude-zh-CN.app"
```

原版 `/Applications/Claude.app` 不会受到影响。

## 适用环境

- macOS
- 已安装 Claude Desktop，通常位于 `/Applications/Claude.app`
- 已安装 Python 3
- 当前资源和 chunk 补丁在 Claude Desktop `1.5354.0` 上验证过

## 3P / 第三方推理模式说明

如果你使用 Claude Desktop 的第三方推理模式，Claude 可能使用下面这个用户数据目录：

```text
~/Library/Application Support/Claude-3p/
```

普通官方模式通常使用：

```text
~/Library/Application Support/Claude/
```

补丁脚本会写入 `~/Library/Application Support/Claude/config.json` 的 `locale=zh-CN`。如果你启动后仍然看到英文，检查你实际运行进程的 `--user-data-dir`：

```bash
pgrep -fl Claude
```

如果进程使用的是 `Claude-3p`，请确认这里也有 `locale`：

```bash
python3 -m json.tool "$HOME/Library/Application Support/Claude-3p/config.json"
```

缺少时可以手动加入：

```json
{
  "locale": "zh-CN"
}
```

## 项目结构

```text
.
├── claude-zh-cn.sh                    # 交互式安装 / 卸载 / 状态检查入口
├── resources/
│   ├── desktop-zh-CN.json             # 桌面壳层翻译
│   ├── frontend-zh-CN.json            # 前端界面翻译
│   └── statsig-zh-CN.json             # Statsig 功能描述翻译
├── tools/
│   ├── validate_resources.py          # 校验资源 JSON 合法性
│   ├── check_i18n_coverage.py         # 检查疑似未翻译条目
│   └── test_patch_behaviors.py        # 补丁行为回归测试
├── patch_claude_mac_json_only.py      # JSON 资源和语言白名单补丁
├── patch_chunks_mac.py                # JS chunk 文案和字体运行时补丁
├── restore_claude_mac.py              # 从备份恢复 / 清理中文补丁
├── README.md
├── CHANGELOG.md
└── LICENSE.md
```

## 翻译覆盖率

| 资源文件 | 英文 keys | 中文 keys | 覆盖率 |
| --- | ---: | ---: | ---: |
| desktop-zh-CN.json | 355 | 355 | 100% |
| frontend-zh-CN.json | 12325 | 12326 | 100% |
| statsig-zh-CN.json | 46 | 46 | 100% |

资源文件中的可翻译条目已尽量汉化。Claude、Anthropic、Google、GitHub、MCP、模型名、快捷键、代码符号和格式占位符会按语境保留英文。

## 脚本具体做了什么

`patch_claude_mac_json_only.py` 会：

1. 检查目标 Resources 目录中是否存在 `en-US.json`。
2. 复制 `resources/desktop-zh-CN.json` 到 `zh-CN.json`。
3. 复制 `resources/frontend-zh-CN.json` 到 `ion-dist/i18n/zh-CN.json`。
4. 复制 `resources/statsig-zh-CN.json` 到 `ion-dist/i18n/statsig/zh-CN.json`。
5. 在 `ion-dist/assets/v1/index-*.js` 中把 `zh-CN` 加入语言白名单。
6. 写入用户配置 `locale=zh-CN`。
7. 首次修改前备份原文件。

`patch_chunks_mac.py` 会：

1. 对已知 chunk 前缀做中文替换，例如 `c71860c77-*.js` 和 `cbc59a8af-*.js`。
2. 对当前版本分散到其他 chunk 的常见导航文案做兜底替换。
3. 在 `index-*.js` 注入中文字体运行时。
4. 只在文件真正发生变化时备份原文件，避免把几百个无关 JS 全塞进备份目录。

## 中文字体自定义

补丁安装后，Claude Desktop 右下角会出现「字体」浮动按钮。点击后可以选择：

- 苹方 (PingFang SC)
- 黑体 (Heiti SC)
- 宋体 (Songti SC)
- 自定义系统字体名
- 导入本地 `.ttf` / `.otf` 字体文件

字体配置会保存在浏览器 `localStorage` 中，并镜像到配置文件的 `claudeZhCnFont` 字段。

## 更新 Claude 后怎么做

Claude Desktop 更新后，`ion-dist/assets/v1/*.js` 的文件名和内容 hash 经常会变化。推荐流程：

1. 确认新版 Claude 可以正常启动。
2. 如果使用原版补丁方式，重新运行安装脚本。
3. 如果使用汉化副本方式，从新版 `/Applications/Claude.app` 重新复制一个副本。
4. 在第一次启动副本前运行两个 patch 脚本。
5. 打开 Claude，检查「新建会话」「已安排」「自定义」「已固定」「最近」等主导航文案。

如果只更新资源 JSON，不更新 chunk 替换规则，可能会出现大部分界面中文但少数导航仍是英文的情况。这通常说明新的 chunk 文件名或文案位置变了，需要更新 `patch_chunks_mac.py`。

## 常见问题

### 为什么 sudo 也写不进 `/Applications/Claude.app`？

这通常是 macOS 的应用管理保护、扩展属性或企业 MDM 策略导致的。报错常见为：

```text
Operation not permitted
```

此时建议使用「创建汉化副本」方式。

### 为什么第一次能补，启动后再次补就失败？

app bundle 启动后，macOS 可能会给副本加上额外保护属性，或者 Electron 正在占用部分资源。建议关闭 Claude，必要时重新复制一个干净副本，并在首次启动前一次性打完补丁。

### 为什么界面还有少量英文？

通常有三类原因：

1. 文案来自用户自己的会话标题、项目名、仓库名，不能也不应该自动翻译。
2. 文案来自 Claude 新版本新增的 i18n key，需要更新资源 JSON。
3. 文案是 JS chunk 里的硬编码字符串，需要更新 `patch_chunks_mac.py`。

### 如何检查资源 JSON 是否有效？

```bash
python3 tools/validate_resources.py
```

## 第三方推理入口参考

如果你要使用 Desktop 的第三方推理或本地代理，可以从 Claude 官方菜单进入：

```text
Help -> Troubleshooting -> Enable Developer mode
Developer -> Configure third-party inference
```

推荐选择 **Gateway**：

- Gateway base URL：本地代理地址，例如 `http://127.0.0.1:15721`
- Gateway API key：例如 `PROXY_MANAGED`
- Gateway auth scheme：`bearer`
- Skip login-mode chooser：建议打开

## 免责声明

本项目仅供个人学习与研究使用，不得用于任何商业目的。使用者应自行承担因修改 Claude Desktop 应用程序包而产生的所有风险，包括但不限于软件崩溃、数据丢失、账户封禁或违反 Anthropic 服务条款。本项目作者不对因使用本项目代码、资源或脚本而导致的任何直接或间接损失承担责任。

## 参考来源

- [javaht/claude-desktop-zh-cn](https://github.com/javaht/claude-desktop-zh-cn) — 中文翻译资源
- [Jyy1529/claude-desktop_win-zh_cn](https://github.com/Jyy1529/claude-desktop_win-zh_cn) — Windows 版实现参考

## 许可

本项目仅限个人非商业使用。未经授权，禁止将本项目任何内容用于商业用途。详见 [LICENSE.md](LICENSE.md)。
