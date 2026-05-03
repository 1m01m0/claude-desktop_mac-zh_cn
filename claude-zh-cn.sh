#!/usr/bin/env zsh
# ──────────────────────────────────────────────────────────
# Claude Desktop 中文补丁 - 安装 / 卸载 / 状态检查 (macOS)
# ──────────────────────────────────────────────────────────
set -euo pipefail

# ── 颜色 ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m'

ok()  { echo -e "  ${GREEN}[OK]${NC} $*"; }
err() { echo -e "  ${RED}[X]${NC}  $*"; }
warn(){ echo -e "  ${YELLOW}[!]${NC}  $*"; }
info(){ echo -e "  ${GRAY}$*${NC}"; }
title(){ echo -e "\n  ${CYAN}$*${NC}"; }

# ── 路径 ────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_RESOURCES="/Applications/Claude.app/Contents/Resources"
CONFIG_PATH="$HOME/Library/Application Support/Claude/config.json"
BACKUP_BASE="$HOME/Library/Application Support/Claude-zh-CN-backup"
BACKUP_JSON_ONLY="$BACKUP_BASE/json-only"
BACKUP_CHUNKS="$BACKUP_BASE/chunks"

# ── Python 检查 ─────────────────────────────────────────
PYTHON=""
for py in python3 python; do
    if command -v "$py" &>/dev/null; then
        PYTHON="$py"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    err "未找到 Python 3。请先安装 Python 3: https://www.python.org/downloads/"
    exit 1
fi

# ── 查找 Claude 资源目录 ───────────────────────────────
find_claude_resources() {
    if [ -f "$DEFAULT_RESOURCES/en-US.json" ]; then
        echo "$DEFAULT_RESOURCES"
        return
    fi
    # 查找其他可能的路径
    for d in /Applications/Claude*.app/Contents/Resources \
             "$HOME/Applications/Claude"*.app/Contents/Resources; do
        if [ -f "$d/en-US.json" ]; then
            echo "$d"
            return
        fi
    done
    echo ""
}

# ── 检查 sudo 权限 ─────────────────────────────────────
ensure_sudo() {
    if [ ! -w "$RES_DIR" ]; then
        echo ""
        warn "需要管理员权限来修改 Claude Desktop 文件。"
        info "请输入密码："
        sudo -v
    fi
}

# ── 获取状态 ───────────────────────────────────────────
get_status() {
    local has_zh_files=false
    local has_whitelist=false
    local has_locale=false
    local has_backup=false

    if [ -f "$RES_DIR/zh-CN.json" ] && [ -f "$RES_DIR/ion-dist/i18n/zh-CN.json" ] && [ -f "$RES_DIR/ion-dist/i18n/statsig/zh-CN.json" ]; then
        has_zh_files=true
    fi

    for f in "$RES_DIR/ion-dist/assets/v1/index-"*.js; do
        if [ -f "$f" ] && grep -q '"zh-CN"' "$f"; then
            has_whitelist=true
            break
        fi
    done

    if [ -f "$CONFIG_PATH" ] && grep -q '"locale".*"zh-CN"' "$CONFIG_PATH" 2>/dev/null; then
        has_locale=true
    fi

    if [ -d "$BACKUP_JSON_ONLY" ] && [ "$(find "$BACKUP_JSON_ONLY" -type f 2>/dev/null | wc -l)" -gt 0 ]; then
        has_backup=true
    fi

    local installed=false
    if $has_zh_files && $has_whitelist; then
        installed=true
    fi

    echo "$has_zh_files|$has_whitelist|$has_locale|$has_backup|$installed"
}

# ── 显示状态 ───────────────────────────────────────────
show_status() {
    local status="$1"
    IFS='|' read -r zh_files whitelist locale backup installed <<< "$status"

    title "当前状态"
    info "Claude 资源目录: $RES_DIR"
    echo ""

    if $zh_files;   then ok   "中文资源文件已写入";       else info "中文资源文件未写入"; fi
    if $whitelist;  then ok   "语言白名单已包含 zh-CN";    else info "语言白名单未包含 zh-CN"; fi
    if $locale;     then ok   "locale 已设为 zh-CN";       else info "locale 未设置"; fi
    if $backup;     then ok   "备份存在";                  else info "无备份"; fi

    echo ""
    if $installed; then
        ok "中文补丁状态: 已安装"
    else
        info "中文补丁状态: 未安装"
    fi
}

# ── 安装 ───────────────────────────────────────────────
do_install() {
    title "安装中文补丁"
    echo ""

    ensure_sudo

    info "正在关闭 Claude 进程..."
    pkill -x "Claude" 2>/dev/null || true
    sleep 2
    ok "Claude 已关闭"

    info "正在执行 JSON 资源 patch..."
    echo ""
    sudo "$PYTHON" "$SCRIPT_DIR/patch_claude_mac_json_only.py" --app-dir "$RES_DIR"

    if [ $? -ne 0 ]; then
        echo ""
        err "JSON 资源 patch 失败。请检查上面的错误信息。"
        return 1
    fi

    echo ""
    info "正在执行 chunk 界面标签和字体自定义 patch..."
    echo ""
    sudo "$PYTHON" "$SCRIPT_DIR/patch_chunks_mac.py" --app-dir "$RES_DIR"

    echo ""
    ok "安装完成！"
    echo ""
    info "下一步："
    info "  1. 打开 Claude Desktop"
    info "  2. 界面应该已经是中文"
    info "  3. 右下角「字体」按钮可调整中文字体设置"
    echo ""
    warn "注意: Claude 更新版本后需要重新运行此脚本"
}

# ── 卸载 ───────────────────────────────────────────────
do_uninstall() {
    local status="$1"
    IFS='|' read -r zh_files whitelist locale backup installed <<< "$status"

    title "卸载中文补丁"
    echo ""

    ensure_sudo

    info "正在关闭 Claude 进程..."
    pkill -x "Claude" 2>/dev/null || true
    sleep 2
    ok "Claude 已关闭"

    if ! $backup; then
        warn "未找到备份文件，将进行手动清理。"

        # 手动删除 zh-CN 文件
        local targets=(
            "$RES_DIR/zh-CN.json"
            "$RES_DIR/ion-dist/i18n/zh-CN.json"
            "$RES_DIR/ion-dist/i18n/statsig/zh-CN.json"
        )
        for t in "${targets[@]}"; do
            if [ -f "$t" ]; then
                sudo rm -f "$t"
                info "  已删除: $t"
            fi
        done

        # 从白名单中移除 zh-CN
        for f in "$RES_DIR/ion-dist/assets/v1/index-"*.js; do
            if [ -f "$f" ] && grep -q '"zh-CN"' "$f"; then
                local content
                content="$(cat "$f")"
                content=$(echo "$content" | sed 's/,"zh-CN"//g')
                echo "$content" | sudo tee "$f" > /dev/null
                info "  已从白名单移除 zh-CN: $(basename "$f")"
            fi
        done
    else
        info "正在从备份恢复..."
        echo ""
        sudo "$PYTHON" "$SCRIPT_DIR/restore_claude_mac.py" --app-dir "$RES_DIR"

        if [ $? -ne 0 ]; then
            echo ""
            err "恢复失败。请检查上面的错误信息。"
            return 1
        fi
    fi

    # 移除 locale
    if [ -f "$CONFIG_PATH" ]; then
        "$PYTHON" -c "
import json, sys
try:
    with open('$CONFIG_PATH', 'r') as f:
        data = json.load(f)
    changed = False
    for k in ('locale', 'claudeZhCnFont'):
        if k in data:
            del data[k]
            changed = True
    if changed:
        with open('$CONFIG_PATH', 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
    print('locale/font config removed')
except Exception as e:
    print(f'Warning: {e}')
" 2>/dev/null || true
    fi

    echo ""
    ok "卸载完成！"
    echo ""
    info "下一步："
    info "  1. 打开 Claude Desktop"
    info "  2. 界面应该已经恢复英文"
}

# ── 手动指定目录 ───────────────────────────────────────
set_manual_dir() {
    echo ""
    info "手动指定 Claude 资源目录"
    info "示例: /Applications/Claude.app/Contents/Resources"
    echo ""

    while true; do
        read -r -p "  请输入 Claude 资源目录（留空则取消）: " input
        if [ -z "$input" ]; then
            info "已取消。"
            return 1
        fi

        local resolved
        resolved="$(cd "$(dirname "$input" 2>/dev/null || echo .)" 2>/dev/null && pwd)/$(basename "$input" 2>/dev/null || echo "$input")"
        resolved="${resolved%/}"

        if [ -f "$resolved/en-US.json" ]; then
            RES_DIR="$resolved"
            MANUAL_DIR=true
            ok "已切换到: $RES_DIR"
            return 0
        fi

        warn "该目录下未找到 en-US.json，请确认输入的是 Claude 的 Contents/Resources 目录。"
    done
}

# ── 主菜单 ─────────────────────────────────────────────
main_menu() {
    clear
    echo ""
    echo -e "  ${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "  ${CYAN}║   Claude Desktop 中文补丁 - zh-CN, macOS    ║${NC}"
    echo -e "  ${CYAN}╚══════════════════════════════════════════════╝${NC}"

    local status
    status="$(get_status)"
    show_status "$status"
    IFS='|' read -r zh_files whitelist locale backup installed <<< "$status"

    echo ""
    echo -e "  ${GRAY}─────────────────────────────────────────────${NC}"

    if $installed; then
        echo -e "  ${BOLD}[1]${NC} 重新安装 / 更新中文补丁"
        echo -e "  ${BOLD}[2]${NC} 卸载中文补丁（恢复英文）"
    else
        echo -e "  ${BOLD}[1]${NC} 安装中文补丁"
        echo -e "  ${GRAY}[2]${NC} 卸载中文补丁（恢复英文）${GRAY}(未安装)${NC}"
    fi
    echo -e "  ${BOLD}[3]${NC} 手动指定 Claude 资源目录"
    echo -e "  ${BOLD}[4]${NC} 刷新状态"
    echo -e "  ${BOLD}[0]${NC} 退出"
    echo ""
}

# ── 主入口 ─────────────────────────────────────────────
RES_DIR="$(find_claude_resources)"
MANUAL_DIR=false

if [ -z "$RES_DIR" ]; then
    echo ""
    warn "未检测到 Claude Desktop 安装。"
    info "请手动输入 Claude 的 Resources 目录。"
    set_manual_dir
    if [ -z "$RES_DIR" ]; then
        echo ""
        err "未找到可用的 Claude 安装目录。"
        exit 1
    fi
fi

while true; do
    main_menu
    read -r -p "  请选择 [0-4]: " choice

    case "$choice" in
        1)
            do_install
            echo ""
            read -r -p "按 Enter 返回菜单"
            ;;
        2)
            local status
            status="$(get_status)"
            IFS='|' read -r zh_files whitelist locale backup installed <<< "$status"
            if ! $installed && ! $backup; then
                echo ""
                warn "当前未安装中文补丁，也没有备份，无需卸载。"
                echo ""
                read -r -p "按 Enter 返回菜单"
            else
                do_uninstall "$status"
                echo ""
                read -r -p "按 Enter 返回菜单"
            fi
            ;;
        3)
            echo ""
            if set_manual_dir; then :; fi
            echo ""
            read -r -p "按 Enter 返回菜单"
            ;;
        4)
            ;;
        0)
            echo ""
            info "再见！"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            warn "无效选择，请输入 0-4。"
            sleep 1
            ;;
    esac
done
