# Project Overview

## 这个项目现在是干什么的

这是一个很小的 Python 命令行工具，用 `faster-whisper` 把本地音频或视频转成纯文本或带时间轴的 SRT 字幕。

对外入口只有一个命令：

```bash
att stt /path/to/file
```

它会把识别结果输出到标准输出，你可以自己重定向到文件：

```bash
att stt /path/to/file > transcript.txt
```

## 现在已经支持的能力

- 转写本地音频文件
- 转写本地视频文件
- 视频输入时自动用 `ffmpeg` 抽取临时 WAV
- 可指定语言，如 `zh`、`en`
- 可指定 Whisper 模型，如 `small`、`medium`、`large-v3`
- 可尝试使用 CUDA
- 如果请求 CUDA 但系统缺少可用 cuDNN，会自动回退到 CPU
- 可保留中间临时音频用于排查问题
- 输出带时间轴的 SRT 字幕（`--output srt`），支持 `--output-path` 自定义路径
- `--context` 把术语透传给 faster-whisper（initial_prompt）做识别引导
- `att srt` 子命令解析/重建 SRT，支持基于上下文的字幕校对（校对由 Claude 在 Skill 层完成，CLI 保持无 LLM 依赖）
- 烧录字幕到视频由 ffmpeg 完成（指引在 `SKILL.md`）

## 现在不支持的能力

- 没有批量处理目录
- 没有 Web UI
- 没有 API 服务
- 没有任务队列、数据库、历史记录

## 字幕输出（SRT）

CLI 的 `stt` 命令支持 `--output txt|srt`：

- `txt`（默认）：纯文本打到 stdout。
- `srt`：带时间轴的 SRT 字幕，默认写到输入文件旁边 `<name>.<lang>.srt`（重名自动 rename），可用 `--output-path` 自定义路径。

相关代码：

- `audio_to_text/subtitles/srt.py`：把带时间戳的 segment 渲染成 SRT。
- `audio_to_text/io.py`：决定 SRT 输出路径（重名自动 rename）并原子写入。
- `audio_to_text/cli.py`：根据 `--output` 选项接入上面两个模块。

## 核心运行流程

1. 用户执行 `att stt <文件路径>`
2. CLI 检查输入文件
3. 如果输入不是常见音频扩展名，就认为它是视频或其他媒体，先调用 `ffmpeg` 抽取临时 WAV
4. 调用 `faster-whisper` 执行转写
5. 根据 `--output`：`txt` 时拼接成纯文本打到 stdout；`srt` 时渲染成带时间轴的 SRT 写到文件
6. 如果是临时抽取的音频，默认在结束后清理

## 关键文件

- `README.md`
  项目使用说明（面向最终用户）。

- `pyproject.toml`
  Python 包定义和依赖。CLI 命令 `att` 也是在这里注册的。

- `install.sh`
  安装脚本。负责安装 `ffmpeg`、`uv`、依赖，并创建全局 `att` 命令。

- `audio_to_text/cli.py`
  主入口。含 `stt`（转写）和 `srt`（解析/重建字幕）两个子命令。

- `audio_to_text/media.py`
  负责检查 `ffmpeg`，以及从视频抽取临时 WAV。

- `audio_to_text/stt/faster_whisper_engine.py`
  负责调用 `faster-whisper`，并处理 CUDA/cuDNN 回退逻辑。

- `audio_to_text/subtitles/srt.py`
  SRT 渲染（`segments_to_srt`/`format_timestamp`）与解析（`parse_srt`），已接入 `cli.py`。

- `audio_to_text/io.py`
  SRT 输出路径决策（`resolve_output_srt_path`）与原子写入（`write_text_atomic`），已接入 `cli.py`。

## 你可以把它理解成什么

最准确的说法是：

> 一个本地命令行音视频转写 + 字幕工具，底层模型是 faster-whisper；同时是一个 Claude Code skill，校对与烧录在 Skill 层完成。

定位边界：

- 转写 / SRT 生成 / SRT 解析重建：在 CLI（纯本地，无 LLM 依赖）。
- 字幕校对：在 Skill 层，由 Claude 基于用户上下文修正文本，CLI 只负责安全重建（保持时间戳）。
- 烧录：在 Skill 层，由 ffmpeg 命令完成（指引在 `SKILL.md`）。

不要把它理解成：多媒体处理平台、带前端的产品、带 LLM/API 依赖的服务。

## 如果你要继续做这个项目，最自然的下一步

已完成（不再是 todo）：

- `--output txt|srt`、`--output-path`、`subtitles/srt.py` 和 `io.py` 接入 CLI
- `--context` 透传 faster-whisper `initial_prompt`
- `att srt` 子命令（解析/重建 SRT）+ Skill 层校对工作流 + 烧录指引
- 引入 pytest 基本测试（`tests/`）

仍可继续：

- 批量处理目录
- 校对工作流更自动化（例如直接读取上下文文件参与校对）
- 更多语言/样式的烧录预设

## 当前一句话总结

这个项目不是“什么都做一点”的杂项目，它现在其实只有一件核心事情：

把本地音频或视频转成纯文本或带时间轴的 SRT 字幕。
