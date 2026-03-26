#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_BIN_DIR="${HOME}/.local/bin"
ATT_WRAPPER_PATH="${LOCAL_BIN_DIR}/att"
PATH_EXPORT='export PATH="$HOME/.local/bin:$PATH"'
PATH_RELOAD_HINT='source ~/.profile'

log() {
    printf '%s\n' "$1"
}

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

append_path_export() {
    local target_file="$1"

    touch "$target_file"

    if ! grep -Fq "$PATH_EXPORT" "$target_file"; then
        printf '\n%s\n' "$PATH_EXPORT" >>"$target_file"
        log "Added ~/.local/bin to PATH in ${target_file}"
    fi
}

configure_shell_path() {
    local shell_name

    shell_name="$(basename "${SHELL:-}")"

    case "$shell_name" in
        zsh)
            append_path_export "${HOME}/.zshrc"
            PATH_RELOAD_HINT='source ~/.zshrc'
            ;;
        bash)
            append_path_export "${HOME}/.bashrc"
            append_path_export "${HOME}/.profile"
            PATH_RELOAD_HINT='source ~/.bashrc'
            ;;
        *)
            append_path_export "${HOME}/.profile"
            PATH_RELOAD_HINT='source ~/.profile'
            ;;
    esac

    export PATH="${LOCAL_BIN_DIR}:$PATH"
}

install_ffmpeg() {
    if has_cmd ffmpeg; then
        log "ffmpeg already installed"
        return
    fi

    log "Installing ffmpeg..."

    if has_cmd brew; then
        brew install ffmpeg
        return
    fi

    if has_cmd apt-get; then
        sudo apt-get update
        sudo apt-get install -y ffmpeg
        return
    fi

    if has_cmd dnf; then
        sudo dnf install -y ffmpeg
        return
    fi

    if has_cmd yum; then
        sudo yum install -y epel-release || true
        sudo yum install -y ffmpeg
        return
    fi

    if has_cmd pacman; then
        sudo pacman -Sy --noconfirm ffmpeg
        return
    fi

    if has_cmd zypper; then
        sudo zypper install -y ffmpeg
        return
    fi

    if has_cmd apk; then
        sudo apk add --no-cache ffmpeg
        return
    fi

    log "Could not install ffmpeg automatically on this platform."
    log "Install ffmpeg manually, then re-run this script."
    exit 1
}

install_uv() {
    if has_cmd uv; then
        log "uv already installed"
        return
    fi

    log "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    if [ -x "${HOME}/.local/bin/uv" ]; then
        export PATH="${HOME}/.local/bin:$PATH"
    elif [ -x "${HOME}/.cargo/bin/uv" ]; then
        export PATH="${HOME}/.cargo/bin:$PATH"
    fi

    if ! has_cmd uv; then
        log "uv was installed but is not on PATH yet."
        log "Open a new shell and re-run this script."
        exit 1
    fi
}

install_project_dependencies() {
    log "Installing Python dependencies..."
    uv sync
}

install_att_wrapper() {
    mkdir -p "$LOCAL_BIN_DIR"

    cat >"$ATT_WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec uv run --directory "$PROJECT_DIR" att "\$@"
EOF

    chmod +x "$ATT_WRAPPER_PATH"
    log "Installed att command at ${ATT_WRAPPER_PATH}"
}

main() {
    log "=== Audio-to-Text Installer ==="
    log "[1/4] Checking ffmpeg"
    install_ffmpeg

    log "[2/4] Checking uv"
    install_uv

    log "[3/4] Installing project dependencies"
    install_project_dependencies

    log "[4/4] Installing att command"
    install_att_wrapper
    configure_shell_path

    log ""
    log "=== Installation Complete ==="
    log "Command:"
    log "  att stt /path/to/audio.mp3"
    log ""
    log "If the command is not available in your current shell yet, run:"
    log "  ${PATH_RELOAD_HINT}"
    log "or restart the terminal."
}

main "$@"
