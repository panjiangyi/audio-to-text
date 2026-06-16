# Project Overview

## 这个项目现在是干什么的

这是一个很小的 Python 命令行工具，用 `faster-whisper` 把本地音频或视频转成纯文本。

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

## 现在不支持的能力

- 还没有把结果直接写成 `.srt` 文件
- 没有批量处理目录
- 没有 Web UI
- 没有 API 服务
- 没有任务队列、数据库、历史记录

## 一个容易让人误解的点

仓库里有字幕相关代码：

- `audio_to_text/subtitles/srt.py`
- `audio_to_text/io.py`

这些文件说明项目曾经考虑过或准备支持 SRT 输出。

但当前 CLI `audio_to_text/cli.py` 实际没有调用这些模块，现在真正交付的是“纯文本转写”，不是“字幕文件生成器”。

## 核心运行流程

1. 用户执行 `att stt <文件路径>`
2. CLI 检查输入文件
3. 如果输入不是常见音频扩展名，就认为它是视频或其他媒体，先调用 `ffmpeg` 抽取临时 WAV
4. 调用 `faster-whisper` 执行转写
5. 把每个 segment 的文本拼接成纯文本输出
6. 如果是临时抽取的音频，默认在结束后清理

## 关键文件

- `README.md`
  项目使用说明。整体方向是对的，但对 SRT 的表述比当前实现更超前。

- `pyproject.toml`
  Python 包定义和依赖。CLI 命令 `att` 也是在这里注册的。

- `install.sh`
  安装脚本。负责安装 `ffmpeg`、`uv`、依赖，并创建全局 `att` 命令。

- `audio_to_text/cli.py`
  主入口。当前唯一用户命令 `stt` 在这里。

- `audio_to_text/media.py`
  负责检查 `ffmpeg`，以及从视频抽取临时 WAV。

- `audio_to_text/stt/faster_whisper_engine.py`
  负责调用 `faster-whisper`，并处理 CUDA/cuDNN 回退逻辑。

- `audio_to_text/subtitles/srt.py`
  SRT 格式化逻辑，当前未接入主流程。

- `audio_to_text/io.py`
  SRT 输出路径和原子写入逻辑，当前未接入主流程。

## 你可以把它理解成什么

最准确的说法是：

> 一个本地命令行音视频转写工具，当前输出纯文本，底层模型是 faster-whisper。

不要把它理解成：

- 完整字幕生产工具
- 多媒体处理平台
- 带前端的产品
- 已完成的 SRT 工作流

## 如果你要继续做这个项目，最自然的下一步

1. 统一项目定位
   要么明确它就是“纯文本转写工具”，要么继续把 SRT 能力补完。

2. 消除文档和实现不一致
   当前 README、包描述、代码注释里有不少 “SRT subtitles” 表述，但实现并没有真正输出 SRT。

3. 如果要补成更完整的工具，优先级建议是
   - 增加 `--output txt|srt`
   - 增加 `--output-path`
   - 把 `subtitles/srt.py` 和 `io.py` 接进 CLI
   - 补基本测试

## 当前一句话总结

这个项目不是“什么都做一点”的杂项目，它现在其实只有一件核心事情：

把本地音频或视频转成纯文本。
