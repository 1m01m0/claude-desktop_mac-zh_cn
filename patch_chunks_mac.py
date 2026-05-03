#!/usr/bin/env python3
"""Patch JS chunks with Chinese UI labels for Claude Desktop on macOS.

Applies safe string replacements to hardcoded UI labels in Claude Desktop's
JS bundle files. Backs up originals before modifying.
Also injects Chinese font customization runtime (macOS fonts).
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


BACKUP_ROOT = Path.home() / "Library" / "Application Support" / "Claude-zh-CN-backup" / "chunks"
CONFIG_PATH = Path.home() / "Library" / "Application Support" / "Claude" / "config.json"
FONT_KEY = "claudeZhCnFont"

FONT_PRESETS = [
    {
        "id": "pingfang",
        "label": "苹方 (PingFang SC)",
        "family": "PingFang SC, system-ui, -apple-system, sans-serif",
    },
    {
        "id": "heiti",
        "label": "黑体 (Heiti SC)",
        "family": "Heiti SC, PingFang SC, system-ui, -apple-system, sans-serif",
    },
    {
        "id": "songti",
        "label": "宋体 (Songti SC)",
        "family": "Songti SC, PingFang SC, system-ui, -apple-system, sans-serif",
    },
]


def font_inject_script() -> str:
    presets_json = json.dumps(FONT_PRESETS, ensure_ascii=False, separators=(",", ":"))
    body = f'''
;(()=>{{
  if (globalThis.__CLAUDE_ZH_CN_FONT_PATCH__) return;
  globalThis.__CLAUDE_ZH_CN_FONT_PATCH__ = true;
  const KEY = "{FONT_KEY}";
  const PRESETS = {presets_json};
  const DEFAULT = PRESETS[0].family;
  const STYLE_ID = "claude-zh-cn-font-style";
  const PANEL_ID = "claude-zh-cn-font-panel";
  const FLOATING_PANEL_ID = "claude-zh-cn-font-floating-panel";
  const FAB_ID = "claude-zh-cn-font-fab";
  const FALLBACK = "PingFang SC, system-ui, -apple-system, Hiragino Sans GB, Microsoft YaHei, sans-serif";
  const state = {{ fontFaceUrl: "" }};

  const readConfig = () => {{
    try {{
      const raw = localStorage.getItem(KEY);
      if (!raw) return {{ mode: "preset", presetId: "pingfang", family: DEFAULT }};
      const data = JSON.parse(raw);
      return {{
        mode: data.mode || "preset",
        presetId: data.presetId || "pingfang",
        family: data.family || DEFAULT,
        fontName: data.fontName || "",
        importedName: data.importedName || "",
        importedCss: data.importedCss || ""
      }};
    }} catch {{
      return {{ mode: "preset", presetId: "pingfang", family: DEFAULT }};
    }}
  }};

  const saveConfig = (cfg) => {{
    const current = readConfig();
    const next = {{ ...current, ...cfg }};
    localStorage.setItem(KEY, JSON.stringify(next));
    applyFont(next);
    return next;
  }};

  const cssFamily = (cfg) => {{
    if (cfg.mode === "custom" && cfg.fontName) return `"${{cfg.fontName.replaceAll('"', '\\"')}}", ${{FALLBACK}}`;
    if (cfg.mode === "imported" && cfg.importedName) return `"${{cfg.importedName.replaceAll('"', '\\"')}}", ${{FALLBACK}}`;
    const preset = PRESETS.find((item) => item.id === cfg.presetId);
    return (preset && preset.family) || cfg.family || DEFAULT;
  }};

  function applyFont(cfg = readConfig()) {{
    let style = document.getElementById(STYLE_ID);
    if (!style) {{
      style = document.createElement("style");
      style.id = STYLE_ID;
      document.head.appendChild(style);
    }}
    const family = cssFamily(cfg);
    const importedCss = cfg.mode === "imported" && cfg.importedCss ? cfg.importedCss : "";
    style.textContent = `
${{importedCss}}
:root {{ --claude-zh-cn-font-family: ${{family}}; }}
html, body, #root, #__next, #app {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
body :is(div,span,p,h1,h2,h3,h4,h5,h6,a,button,label,legend,li,dt,dd,th,td,caption,small,strong,em,b,i,input,textarea,select,option,[role="dialog"],[role="menu"],[role="tooltip"],[role="listbox"],[role="option"],[contenteditable="true"]):not(svg):not(svg *):not([aria-hidden="true"]):not([data-icon]):not([class*="icon" i]):not([class*="lucide" i]):not([class*="codicon" i]):not([class*="material" i]):not([class*="fa-" i]) {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
pre, code, kbd, samp, .monaco-editor, .monaco-editor *, .xterm, .xterm * {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
svg text, svg tspan {{
  font-family: var(--claude-zh-cn-font-family) !important;
}}
`;
    document.documentElement.style.setProperty("--claude-zh-cn-font-family", family);
    window.dispatchEvent(new CustomEvent("claude-zh-cn-font-changed", {{ detail: cfg }}));
  }}

  const labelStyle = "display:block;margin:8px 0 4px;font-size:12px;color:var(--text-300,#666);";
  const inputStyle = "width:100%;box-sizing:border-box;border:1px solid var(--border-300,#ddd);border-radius:8px;padding:8px;background:var(--bg-000,#fff);color:inherit;";
  const buttonStyle = "border:1px solid var(--border-300,#ddd);border-radius:8px;padding:6px 9px;background:var(--bg-100,#f7f7f7);color:inherit;cursor:pointer;";
  const panelStyle = "margin:0;padding:10px;border:1px solid var(--border-200,#e6e6e6);border-radius:12px;background:var(--bg-000,#fff);box-shadow:0 12px 30px rgba(0,0,0,.13);backdrop-filter:blur(10px);";
  const mutedText = "font-size:11px;line-height:1.4;color:var(--text-300,#666);";
  const sectionStyle = "padding:9px;border:1px solid var(--border-200,#e6e6e6);border-radius:10px;background:var(--bg-050,#fafafa);";
  const sectionAltStyle = "padding:9px;border:1px solid var(--border-300,#ddd);border-radius:10px;background:var(--bg-000,#fff);";
  const previewStyle = "padding:12px;border:1px solid var(--border-300,#ddd);border-radius:12px;background:linear-gradient(180deg,var(--bg-000,#fff),var(--bg-050,#fafafa));min-height:130px;";
  const segmentBase = "flex:1;min-width:0;border:0;border-radius:7px;padding:6px 7px;background:transparent;color:var(--text-300,#666);cursor:pointer;font-size:11px;font-weight:600;text-align:center;transition:background .12s ease,color .12s ease,box-shadow .12s ease;";
  const segmentActive = "background:var(--bg-000,#fff);color:var(--text-500,#111);box-shadow:0 1px 2px rgba(0,0,0,.07),inset 0 0 0 1px var(--border-300,#ddd);";

  const VISIBLE_TEXT_FIXES = new Map([
    ["auto", "自动"],
    ["Auto", "自动"],
    ["light", "浅色"],
    ["Light", "浅色"],
    ["dark", "深色"],
    ["Dark", "深色"],
    ["sans", "无衬线"],
    ["Sans", "无衬线"],
  ]);

  function shouldFixTextNode(node) {{
    const parent = node.parentElement;
    if (!parent || parent.closest("script,style,[contenteditable='true']")) return false;
    const scope = parent.closest("[role='dialog'],[role='menu'],[role='listbox'],main,section");
    if (!scope) return false;
    const context = scope.innerText || "";
    return /(Appearance|外观|颜色模式|Color mode|聊天字体|Chat font|Font|字体)/.test(context);
  }}

  function fixVisibleText(root = document.body) {{
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (nodes.length < 2000) {{
      const node = walker.nextNode();
      if (!node) break;
      nodes.push(node);
    }}
    nodes.forEach((node) => {{
      const text = node.nodeValue;
      if (!text) return;
      const trimmed = text.trim();
      const replacement = VISIBLE_TEXT_FIXES.get(trimmed);
      if (!replacement) return;
      if (!shouldFixTextNode(node)) return;
      node.nodeValue = text.replace(trimmed, replacement);
    }});
  }}

  let textFixScheduled = false;
  function scheduleFixVisibleText() {{
    if (textFixScheduled) return;
    textFixScheduled = true;
    const schedule = window.requestAnimationFrame || ((callback) => window.setTimeout(callback, 16));
    schedule(() => {{
      textFixScheduled = false;
      fixVisibleText();
    }});
  }}

  function buildPanel(expanded = false, mode = "inline") {{
    const panel = document.createElement("section");
    panel.id = mode === "floating" ? FLOATING_PANEL_ID : PANEL_ID;
    panel.dataset.fontPanelMode = mode;
    panel.style.cssText = panelStyle + (mode === "floating" ? "width:min(520px,calc(100vw - 40px));" : "width:100%;box-sizing:border-box;");
    panel.innerHTML = `
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
        <div>
          <h3 style="margin:0;font-size:13px;font-weight:700;letter-spacing:-0.01em;">中文字体</h3>
          <p style="margin:4px 0 0;${{mutedText}}">调整 Claude 界面的中文字体。</p>
        </div>
        <button data-font-toggle style="${{buttonStyle}};white-space:nowrap;font-size:11px;">${{expanded ? "收起" : "字体"}}</button>
      </div>

      <div data-font-body style="display:${{expanded ? "block" : "none"}};margin-top:8px;">
      <div data-font-layout style="display:grid;grid-template-columns:minmax(0,1.25fr) minmax(150px,.75fr);gap:10px;align-items:stretch;">
      <div style="display:flex;flex-direction:column;gap:8px;">
      <div style="${{sectionStyle}}">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:5px;">
          <label style="margin:0;font-size:11px;font-weight:600;color:var(--text-400,#444);">内置推荐</label>
          <span data-font-status style="font-size:11px;color:var(--text-300,#666);"></span>
        </div>
        <div data-font-preset-group style="display:flex;gap:1px;padding:2px;border:1px solid var(--border-300,#ddd);border-radius:10px;background:var(--bg-100,#f5f5f5);box-shadow:inset 0 1px 2px rgba(0,0,0,.04);">
          ${{PRESETS.map((item) => `<button type="button" data-font-preset-btn="${{item.id}}" style="${{segmentBase}}">${{item.label}}</button>`).join("")}}
        </div>
        <p style="margin:5px 0 0;${{mutedText}}">推荐字体，直接切换。</p>
      </div>

      <div style="${{sectionAltStyle}}">
        <label style="margin:0 0 5px;display:block;font-size:11px;font-weight:600;color:var(--text-400,#444);">自定义系统字体名</label>
        <div style="display:flex;gap:5px;align-items:center;">
          <input data-font-name placeholder="已安装字体名称" style="${{inputStyle}};min-width:0;padding:6px 7px;font-size:11px;" />
          <button data-font-apply-custom style="${{buttonStyle}};white-space:nowrap;font-size:11px;">应用</button>
        </div>
        <p style="margin:5px 0 0;${{mutedText}}">输入已安装字体名。</p>
      </div>

      <div style="${{sectionStyle}}">
        <label style="margin:0 0 5px;display:block;font-size:11px;font-weight:600;color:var(--text-400,#444);">导入本地字体文件</label>
        <input data-font-file type="file" accept=".ttf,.otf,font/ttf,font/otf" style="${{inputStyle}};padding:4px 5px;font-size:11px;" />
        <p style="margin:5px 0 0;${{mutedText}}">选择本地 .ttf / .otf。</p>
      </div>
      </div>

      <div style="${{previewStyle}}">
        <div style="margin:0 0 8px;font-size:11px;font-weight:600;color:var(--text-400,#444);">预览</div>
        <div style="font-size:16px;line-height:1.45;font-weight:600;color:var(--text-500,#111);">中文字体预览</div>
        <div style="margin-top:8px;${{mutedText}}">Claude Desktop 中文补丁 (macOS)</div>
        <div style="margin-top:14px;font-size:11px;color:var(--text-300,#666);">Aa 你好 Claude</div>
      </div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px;">
        <button data-font-reset style="${{buttonStyle}};white-space:nowrap;font-size:11px;">恢复默认</button>
      </div>
      </div>
    `;

    const presetButtons = [...panel.querySelectorAll("[data-font-preset-btn]")];
    const fontName = panel.querySelector("[data-font-name]");
    const status = panel.querySelector("[data-font-status]");
    const updateLayout = () => {{
      const layout = panel.querySelector("[data-font-layout]");
      if (!layout) return;
      layout.style.gridTemplateColumns = panel.getBoundingClientRect().width < 430 ? "1fr" : "minmax(0,1.25fr) minmax(150px,.75fr)";
    }};
    panel.querySelector("[data-font-toggle]").addEventListener("click", () => {{
      if (panel.dataset.fontPanelMode === "floating") {{
        panel.remove();
        return;
      }}
      const body = panel.querySelector("[data-font-body]");
      const willExpand = body.style.display === "none";
      body.style.display = willExpand ? "block" : "none";
      panel.querySelector("[data-font-toggle]").textContent = willExpand ? "收起" : "字体";
      if (willExpand) updateLayout();
    }});
    const setActivePreset = (presetId) => {{
      presetButtons.forEach((button) => {{
        const active = button.getAttribute("data-font-preset-btn") === presetId;
        button.style.cssText = `${{segmentBase}}${{active ? segmentActive : ""}}`;
      }});
    }};
    const sync = () => {{
      const cfg = readConfig();
      const currentPreset = cfg.presetId || "pingfang";
      setActivePreset(currentPreset);
      fontName.value = cfg.fontName || "";
      status.textContent = cfg.mode === "custom" ? `当前：${{cfg.fontName}}` : cfg.mode === "imported" ? `当前：${{cfg.importedName}}` : `当前：${{PRESETS.find((item) => item.id === cfg.presetId)?.label || "苹方 (PingFang SC)"}}`;
    }};
    presetButtons.forEach((button) => {{
      button.addEventListener("click", () => {{
        const item = PRESETS.find((entry) => entry.id === button.getAttribute("data-font-preset-btn")) || PRESETS[0];
        saveConfig({{ mode: "preset", presetId: item.id, family: item.family }});
        sync();
      }});
    }});
    panel.querySelector("[data-font-apply-custom]").addEventListener("click", () => {{
      const name = fontName.value.trim();
      if (!name) return;
      saveConfig({{ mode: "custom", fontName: name }});
      sync();
    }});
    panel.querySelector("[data-font-file]").addEventListener("change", async (event) => {{
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      const buffer = await file.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = "";
      for (let i = 0; i < bytes.length; i += 1) binary += String.fromCharCode(bytes[i]);
      const b64 = btoa(binary);
      const name = `ClaudeZhCnImported-${{Date.now()}}`;
      const format = file.name.toLowerCase().endsWith(".otf") ? "opentype" : "truetype";
      const css = `@font-face{{font-family:"${{name}}";src:url(data:font/${{format}};base64,${{b64}}) format("${{format}}");font-display:swap;}}`;
      saveConfig({{ mode: "imported", importedName: name, importedCss: css }});
      sync();
    }});
    panel.querySelector("[data-font-reset]").addEventListener("click", () => {{
      localStorage.removeItem(KEY);
      applyFont();
      sync();
    }});
    sync();
    updateLayout();
    return panel;
  }}

  function openFloatingPanel() {{
    let panel = document.getElementById(FLOATING_PANEL_ID);
    if (!panel) {{
      panel = buildPanel(true, "floating");
      panel.style.position = "fixed";
      panel.style.right = "20px";
      panel.style.bottom = "76px";
      panel.style.zIndex = "2147483647";
      panel.style.width = "min(520px, calc(100vw - 40px))";
      panel.style.boxShadow = "0 18px 60px rgba(0,0,0,.24)";
      document.body.appendChild(panel);
    }} else {{
      panel.remove();
    }}
  }}

  function mountFloatingButton() {{
    if (!document.body || document.getElementById(FAB_ID)) return;
    const button = document.createElement("button");
    button.id = FAB_ID;
    button.type = "button";
    button.textContent = "字体";
    button.title = "中文字体设置";
    button.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:2147483647;border:1px solid var(--border-300,#ddd);border-radius:999px;padding:8px 12px;background:var(--bg-000,#fff);color:inherit;box-shadow:0 8px 28px rgba(0,0,0,.18);cursor:pointer;font-size:13px;";
    button.addEventListener("click", openFloatingPanel);
    document.body.appendChild(button);
  }}

  function mountPanel() {{
    return;
  }}

  const start = () => {{
    applyFont();
    mountFloatingButton();
    scheduleFixVisibleText();
    const observer = new MutationObserver(() => {{
      scheduleFixVisibleText();
    }});
    observer.observe(document.body, {{ childList: true, subtree: true }});
  }};
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, {{ once: true }});
  else start();
}})();
'''.strip()
    return "\n".join([
        "// __CLAUDE_ZH_CN_FONT_PATCH_BEGIN__",
        body,
        "// __CLAUDE_ZH_CN_FONT_PATCH_END__",
    ])


DEFAULT_APP_RESOURCES = Path("/Applications/Claude.app/Contents/Resources")


def find_claude_resources() -> Path | None:
    if DEFAULT_APP_RESOURCES.exists() and (DEFAULT_APP_RESOURCES / "en-US.json").exists():
        return DEFAULT_APP_RESOURCES
    candidates = sorted(Path("/Applications").glob("Claude*.app/Contents/Resources/en-US.json"))
    if candidates:
        return candidates[0].parent
    candidates = sorted(Path.home().glob("Applications/Claude*.app/Contents/Resources/en-US.json"))
    if candidates:
        return candidates[0].parent
    return None


def backup_file(path: Path, assets_dir: Path) -> None:
    if not path.exists():
        return
    rel = path.relative_to(assets_dir)
    dst = BACKUP_ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(path, dst)


def set_font_config_mirror() -> bool:
    if not CONFIG_PATH.exists():
        return False

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    data.setdefault(
        FONT_KEY,
        {
            "mode": "preset",
            "presetId": "pingfang",
            "family": FONT_PRESETS[0]["family"],
        },
    )
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def patch_font_runtime(assets_dir: Path) -> int:
    candidates = sorted(assets_dir.glob("index-*.js"))
    if not candidates:
        print("Warning: no index-*.js found; skipping font runtime patch")
        return 0

    script = font_inject_script()
    marker = "__CLAUDE_ZH_CN_FONT_PATCH__"
    begin_marker = "// __CLAUDE_ZH_CN_FONT_PATCH_BEGIN__"
    end_marker = "// __CLAUDE_ZH_CN_FONT_PATCH_END__"
    changed = 0
    for path in candidates:
        backup_file(path, assets_dir)
        content = path.read_text(encoding="utf-8")
        if begin_marker in content and end_marker in content:
            start = content.index(begin_marker)
            end = content.index(end_marker, start) + len(end_marker)
            new_content = content[:start].rstrip() + "\n" + script + "\n" + content[end:].lstrip()
            action = "updated font runtime"
        elif marker in content:
            marker_pos = content.index(marker)
            start = content.rfind(";(()=>{", 0, marker_pos)
            if start == -1:
                start = marker_pos
            legacy_end = content.find("})();", marker_pos)
            end = legacy_end + len("})();") if legacy_end != -1 else len(content)
            new_content = content[:start].rstrip() + "\n" + script + "\n" + content[end:].lstrip()
            action = "replaced legacy font runtime"
        else:
            new_content = content.rstrip() + "\n" + script + "\n"
            action = "injected font runtime"

        if new_content == content:
            continue
        path.write_text(new_content, encoding="utf-8")
        changed += 1
        print(f"  {path.name}: {action}")
    return changed


# Same chunk patches as Windows version (format is OS-independent)
PATCHES: dict[str, list[tuple[str, str]]] = {}

PATCHES["c71860c77-*.js"] = [
    ('"Egress Requirements"', '"出口要求"'),
    ('"Gateway base URL"', '"自定义 Base URL"'),
    ('"Gateway API key"', '"自定义 API Key"'),
    ('"Gateway auth scheme"', '"自定义认证方式"'),
    ('"Gateway extra headers"', '"自定义额外请求头"'),
    ('"Allow desktop extensions"', '"允许桌面扩展"'),
    ('"Show extension directory"', '"显示扩展目录"'),
    ('"Require signed extensions"', '"要求扩展签名"'),
    ('"Allow user-added MCP servers"', '"允许用户添加 MCP 服务器"'),
    ('"Allow Claude Code tab"', '"允许 Claude Code 标签页"'),
    ('"Secure VM features"', '"安全虚拟机功能"'),
    ('"Require full VM sandbox"', '"要求完整虚拟机沙盒"'),
    ('"Allowed egress hosts"', '"允许的出口主机"'),
    ('"OpenTelemetry collector endpoint"', '"OpenTelemetry 采集器端点"'),
    ('"OpenTelemetry exporter protocol"', '"OpenTelemetry 导出协议"'),
    ('"OpenTelemetry exporter headers"', '"OpenTelemetry 导出请求头"'),
    ('"Auto-update enforcement window"', '"自动更新强制窗口"'),
    ('"Block auto-updates"', '"禁止自动更新"'),
    ('"Skip login-mode chooser"', '"跳过登录模式选择"'),
    ('"Required organization"', '"必需的组织"'),
    ('"Inference provider"', '"推理供应商"'),
    ('"Connection"', '"连接方式"'),
    ('"Sandbox & workspace"', '"沙盒与工作区"'),
    ('"Connectors & extensions"', '"连接器与扩展"'),
    ('"Telemetry & updates"', '"遥测与更新"'),
    ('"Usage limits"', '"使用限制"'),
    ('"Plugins & skills"', '"插件与技能"'),
    ('gateway:"自定义"', 'gateway:"自定义"'),
    ('gateway:"Gateway"', 'gateway:"自定义"'),
]

PATCHES["cbc59a8af-*.js"] = [
    ('label:"聊天"', 'label:"聊天"'),
    ('label:"Chat"', 'label:"聊天"'),
    ('label:"Cowork"', 'label:"协作"'),
    ('label:"Code"', 'label:"代码"'),
    ('label:"Operon"', 'label:"实验室"'),
    ('label:"项目"', 'label:"项目"'),
    ('label:"Projects"', 'label:"项目"'),
    ('label:"已安排"', 'label:"已安排"'),
    ('label:"Scheduled"', 'label:"已安排"'),
    ('label:"Live artifacts"', 'label:"实时 Artifacts"'),
    ('label:"任务"', 'label:"任务"'),
    ('label:"Tasks"', 'label:"任务"'),
    ('label:"Pull Requests"', 'label:"拉取请求"'),
    ('label:"回放"', 'label:"回放"'),
    ('label:"Replay"', 'label:"回放"'),
    ('label:"调度"', 'label:"调度"'),
    ('label:"Dispatch"', 'label:"调度"'),
    ('label:"想法"', 'label:"想法"'),
    ('label:"Ideas"', 'label:"想法"'),
    ('label:"应用"', 'label:"应用"'),
    ('label:"Apps"', 'label:"应用"'),
    ('label:"安全"', 'label:"安全"'),
    ('label:"Security"', 'label:"安全"'),
    ('label:"自定义"', 'label:"自定义"'),
    ('label:"Customize"', 'label:"自定义"'),
    ('label:"状态"', 'label:"状态"'),
    ('label:"Status"', 'label:"状态"'),
    ('label:"环境"', 'label:"环境"'),
    ('label:"Environment"', 'label:"环境"'),
    ('chat:"新建聊天"', 'chat:"新建聊天"'),
    ('chat:"New chat"', 'chat:"新建聊天"'),
    ('cowork:"新建任务"', 'cowork:"新建任务"'),
    ('cowork:"New task"', 'cowork:"新建任务"'),
    ('code:"新建会话"', 'code:"新建会话"'),
    ('code:"New session"', 'code:"新建会话"'),
    ('operon:"新建会话"', 'operon:"新建会话"'),
    ('operon:"New session"', 'operon:"新建会话"'),
    ('oo="本地"', 'oo="本地"'),
    ('oo="Local"', 'oo="本地"'),
    ('io="云端"', 'io="云端"'),
    ('io="Cloud"', 'io="云端"'),
    ('ro="远程控制"', 'ro="远程控制"'),
    ('ro="Remote Control"', 'ro="远程控制"'),
    ('co="全部"', 'co="全部"'),
    ('co="All"', 'co="全部"'),
    ('const Ea="已安排"', 'const Ea="已安排"'),
    ('const Ea="Scheduled"', 'const Ea="已安排"'),
    ('["active","活跃"]', '["active","活跃"]'),
    ('["active","Active"]', '["active","活跃"]'),
    ('["archived","已归档"]', '["archived","已归档"]'),
    ('["archived","Archived"]', '["archived","已归档"]'),
    ('["all","全部"]', '["all","全部"]'),
    ('["all","All"]', '["all","全部"]'),
    ('["0","全部"]', '["0","全部"]'),
    ('["0","All"]', '["0","全部"]'),
    ('["1","1天"]', '["1","1天"]'),
    ('["1","1d"]', '["1","1天"]'),
    ('["3","3天"]', '["3","3天"]'),
    ('["3","3d"]', '["3","3天"]'),
    ('["7","7天"]', '["7","7天"]'),
    ('["7","7d"]', '["7","7天"]'),
    ('["14","14天"]', '["14","14天"]'),
    ('["14","14d"]', '["14","14天"]'),
    ('["30","30天"]', '["30","30天"]'),
    ('["30","30d"]', '["30","30天"]'),
    ('"日期"', '"日期"'),
    ('"Date"', '"日期"'),
    ('"无"', '"无"'),
    ('"None"', '"无"'),
    ('["project","项目"]', '["project","项目"]'),
    ('["project","Project"]', '["project","项目"]'),
    ('["state","状态"]', '["state","状态"]'),
    ('["state","State"]', '["state","状态"]'),
    ('?"全部":', '?"全部":'),
    ('?"All":', '?"全部":'),
    ('children:"已固定"', 'children:"已固定"'),
    ('children:"Pinned"', 'children:"已固定"'),
    ('children:"拖拽固定"', 'children:"拖拽固定"'),
    ('children:"Drag to pin"', 'children:"拖拽固定"'),
    ('"Drop here"', '"放在这里"'),
    ('"Let go"', '"松开"'),
    ('children:["查看全部"', 'children:["查看全部"'),
    ('children:["View all"', 'children:["查看全部"'),
    ('title:"删除较旧的会话？"', 'title:"删除较旧的会话？"'),
    ('title:"Delete older sessions?"', 'title:"删除较旧的会话？"'),
    ('children:"清除筛选"', 'children:"清除筛选"'),
    ('children:"Clear filters"', 'children:"清除筛选"'),
    ('children:"所有项目"', 'children:"所有项目"'),
    ('children:"All projects"', 'children:"所有项目"'),
    ('children:"开发面板"', 'children:"开发面板"'),
    ('children:"Dev panels"', 'children:"开发面板"'),
    ('children:"主题"', 'children:"主题"'),
    ('children:"Theme"', 'children:"主题"'),
    ('children:"字体"', 'children:"字体"'),
    ('children:"Font"', 'children:"字体"'),
    ('children:"项目"', 'children:"项目"'),
    ('children:"Project"', 'children:"项目"'),
    ('const Co="最近"', 'const Co="最近"'),
    ('const Co="Recents"', 'const Co="最近"'),
    ('label:"最近活动"', 'label:"最近活动"'),
    ('label:"Last activity"', 'label:"最近活动"'),
    ('label:"分组方式"', 'label:"分组方式"'),
    ('label:"Group by"', 'label:"分组方式"'),
    ('"Stale after"', '"过期时间"'),
    ('"Older"', '"更早"'),
    ('"Ungrouped"', '"未分组"'),
]

PATCHES["index-*.js"] = [
    ('title:"计划任务"', 'title:"计划任务"'),
    ('title:"Scheduled tasks",subheader', 'title:"计划任务",subheader'),
    ('message:"计划任务仅在计算机保持唤醒时运行。"', 'message:"计划任务仅在计算机保持唤醒时运行。"'),
    ('message:"Scheduled tasks only run while your computer is awake."', 'message:"计划任务仅在计算机保持唤醒时运行。"'),
    ('Ifn={all:"全部",active:"活跃",archived:"已归档"}', 'Ifn={all:"全部",active:"活跃",archived:"已归档"}'),
    ('Ifn={all:"All",active:"Active",archived:"Archived"}', 'Ifn={all:"全部",active:"活跃",archived:"已归档"}'),
    ('"No tasks yet."', '"还没有任务。"'),
    ('"No active tasks."', '"没有活跃任务。"'),
    ('"No archived tasks."', '"没有已归档任务。"'),
    ('children:"活跃"}),renderRow', 'children:"活跃"}),renderRow'),
    ('children:"Active"}),renderRow', 'children:"活跃"}),renderRow'),
    ('children:"新建任务"', 'children:"新建任务"'),
    ('children:"New task"', 'children:"新建任务"'),
    ('?"新建任务":"新建聊天"', '?"新建任务":"新建聊天"'),
    ('?"New task":"New chat"', '?"新建任务":"新建聊天"'),
    ('baseDescription:"新建任务"', 'baseDescription:"新建任务"'),
    ('baseDescription:"New task"', 'baseDescription:"新建任务"'),
    ('title:"任务"', 'title:"任务"'),
    ('nextRun:"下次运行",name:"名称"', 'nextRun:"下次运行",name:"名称"'),
    ('nextRun:"Next run",name:"Name"', 'nextRun:"下次运行",name:"名称"'),
    ('children:"3P"', 'children:"第三方"'),
    ('label:"文档"', 'label:"文档"'),
    ('label:"Documents"', 'label:"文档"'),
    ('label:"文件"', 'label:"文件"'),
    ('label:"Files"', 'label:"文件"'),
    ('label:"同步源"', 'label:"同步源"'),
    ('label:"Sync Sources"', 'label:"同步源"'),
    ('title:"从 GitHub 添加内容"', 'title:"从 GitHub 添加内容"'),
    ('title:"Add content from GitHub"', 'title:"从 GitHub 添加内容"'),
    ('title:"将 Claude 连接到 Google Drive"', 'title:"将 Claude 连接到 Google Drive"'),
    ('title:"Connect Claude to Google Drive"', 'title:"将 Claude 连接到 Google Drive"'),
    ('title:"结束此通话？"', 'title:"结束此通话？"'),
    ('title:"End this call?"', 'title:"结束此通话？"'),
    ('title:"代码执行与文件创建"', 'title:"代码执行与文件创建"'),
    ('title:"Code execution and file creation"', 'title:"代码执行与文件创建"'),
]

PATCHES["*.js"] = [
    ('defaultMessage:"New session"', 'defaultMessage:"新建会话"'),
    ('defaultMessage:"New chat"', 'defaultMessage:"新建聊天"'),
    ('defaultMessage:"New task"', 'defaultMessage:"新建任务"'),
    ('defaultMessage:"Scheduled"', 'defaultMessage:"已安排"'),
    ('defaultMessage:"Customize"', 'defaultMessage:"自定义"'),
    ('defaultMessage:"Pinned"', 'defaultMessage:"已固定"'),
    ('defaultMessage:"Pinned or active"', 'defaultMessage:"已固定或活跃"'),
    ('defaultMessage:"Recents"', 'defaultMessage:"最近"'),
    ('defaultMessage:"Filter"', 'defaultMessage:"筛选"'),
    ('defaultMessage:"Active"', 'defaultMessage:"活跃"'),
    ('defaultMessage:"Archived"', 'defaultMessage:"已归档"'),
    ('defaultMessage:"All"', 'defaultMessage:"全部"'),
    ('defaultMessage:"Local"', 'defaultMessage:"本地"'),
    ('defaultMessage:"Cloud"', 'defaultMessage:"云端"'),
    ('defaultMessage:"Remote Control"', 'defaultMessage:"远程控制"'),
    ('recents:"Recents"', 'recents:"最近"'),
    ('shared:"Shared"', 'shared:"共享"'),
    ('label:"Scheduled"', 'label:"已安排"'),
    ('label:"Customize"', 'label:"自定义"'),
    ('chat:"New chat"', 'chat:"新建聊天"'),
    ('cowork:"New task"', 'cowork:"新建任务"'),
    ('code:"New session"', 'code:"新建会话"'),
    ('operon:"New session"', 'operon:"新建会话"'),
    ('description:"New session"', 'description:"新建会话"'),
    ('label:"New session"', 'label:"新建会话"'),
    ('"Pinned"', '"已固定"'),
    ('"Recents"', '"最近"'),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch Claude Desktop (macOS) JS chunks with zh-CN labels")
    parser.add_argument("--app-dir", type=str, default=None)
    args = parser.parse_args()

    if args.app_dir:
        app_resources = Path(args.app_dir)
    else:
        app_resources = find_claude_resources()

    if not app_resources or not app_resources.exists():
        raise SystemExit("Claude Resources directory not found. Use --app-dir to specify manually.")

    assets_dir = app_resources / "ion-dist" / "assets" / "v1"
    if not assets_dir.exists():
        raise SystemExit(f"Assets dir not found: {assets_dir}")

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    total = 0

    for pattern, replacements in PATCHES.items():
        files = sorted(assets_dir.glob(pattern))
        for fpath in files:
            content = fpath.read_text(encoding="utf-8")
            changed = 0
            for old, new in replacements:
                if old in content and old != new:
                    content = content.replace(old, new)
                    changed += 1
            if changed > 0:
                backup_file(fpath, assets_dir)
                fpath.write_text(content, encoding="utf-8")
                total += changed
                print(f"  {fpath.name}: {changed} replacements")

    font_patches = patch_font_runtime(assets_dir)
    config_mirrored = set_font_config_mirror()

    print(f"Done. Total chunk patches: {total}")
    print(f"Font runtime patches: {font_patches}")
    print(f"Font config mirrored: {config_mirrored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
