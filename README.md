<div align="center">
  <h1>🍅 Pomodoro Timer</h1>
  <p><b>极简 · 玻璃浮窗番茄钟</b></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python">
    <img src="https://img.shields.io/badge/platform-windows-lightgrey?logo=windows">
    <img src="https://img.shields.io/github/license/VirginiaH233/pomodoro-timer">
  </p>
  <br>
</div>

一个**极致的极简番茄钟**——没有窗口、没有任务栏按钮、没有多余设置。只有一块半透明的玻璃浮窗，安静地停在你的屏幕角落。

---

## ✨ 特色

| | |
|---|---|
| 🪟 **玻璃浮窗** | 半透明磨砂玻璃效果，存在感趋近于零 |
| 🎨 **7 套配色** | Light · Dark · Blue · Mint · Purple · Peach · Slate |
| 🖱 **拖拽缩放** | 任意位置移动，右下角 `╲` 把手调整大小 |
| ⏱ **标准番茄** | 25+5+15 分钟周期，全参数可自定义 |
| 🎉 **完成庆祝** | 每完成一个番茄，浮窗闪烁庆祝动画 |
| 🖥 **系统托盘** | 右下角常驻图标，右键即出菜单 |
| ⚙️ **设置面板** | 图形化配置，无需编辑 JSON 文件 |
| 🎯 **零干扰** | 没有窗口边框、没有任务栏入口、不抢焦点 |

---

## ⚡ 快速开始

### 一键启动（推荐）

下载 [PomodoroTimer.exe](https://github.com/VirginiaH233/pomodoro-timer/releases)（单文件，免 Python 环境）。

或者用 Python：

```bash
pip install -r requirements.txt
python main.py
```

### 从源码构建

```bash
pip install pyinstaller
python build.bat
# 输出: dist/PomodoroTimer.exe
```

---

## 🎮 操作指南

```
 左键单击  →  暂停 / 继续
 按住拖拽  →  移动浮窗
 右下角 `╲`  →  调整大小
 右键浮窗  →  菜单（开始/暂停/跳过/重置/颜色/设置/退出）
 右键托盘  →  同上
```

**它不会：**
- 出现在任务栏
- 出现在 Alt+Tab 切换
- 遮挡点击（透明区域穿透）
- 消耗超过 12MB 内存

---

## 🧩 项目结构

```
pomodoro_timer/
├── main.py          # 入口
├── overlay.py       # 玻璃浮窗 + 拖拽 + 托盘
├── pomtimer.py      # 计时状态机
├── config.py        # 配置 + 7 色预设
├── settings.py      # 设置面板
├── icon_gen.py      # 托盘图标
├── notifier.py      # 通知
├── requirements.txt # 依赖清单
├── build.bat        # 构建脚本
└── README.md
```

---

## 📝 许可

MIT — 自由使用、修改、分发。
