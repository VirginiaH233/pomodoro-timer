<div align="center">
  <h1>🍅 Pomi</h1>
  <p><b>极简玻璃番茄钟</b></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python">
    <img src="https://img.shields.io/badge/platform-windows-lightgrey?logo=windows">
    <img src="https://img.shields.io/github/license/VirginiaH233/pomodoro-timer">
  </p>
  <br>
</div>

**Pomi** 是一个极致的极简番茄钟——没有窗口、没有任务栏按钮、没有多余设置。只有一块半透明的玻璃浮窗，安静地停在你的屏幕角落。

---

## ✨ 特色

| | |
|---|---|
| 🪟 **玻璃浮窗** | 半透明磨砂玻璃质感，启动时默认在屏幕右下角，存在感趋近于零 |
| 🎨 **7 套配色** | Light · Dark · Blue · Mint · Purple · Peach · Slate |
| 🖱 **拖拽缩放** | 任意位置移动，右下角调整大小，可轻松吸附在任务栏或屏幕边缘 |
| ⏱ **标准番茄** | 25+5+15 分钟周期，全参数可自定义 |
| 🔔 **提示音** | 内置 5 种音效 + 自定义 MP3/WAV |
| 🎉 **完成庆祝** | 每完成一个番茄，浮窗闪烁动画 |
| 🖥 **系统托盘** | 右下角常驻图标，右键即出菜单 |
| ⚙️ **图形设置** | 可视化调整所有参数，无需编辑 JSON |
| 🎯 **零干扰** | 没有窗口边框、没有任务栏入口、不抢焦点 |
| 🔤**English-enabled** | bilingual support for Chinese and English |

---

## ⚡ 下载

📦 [GitHub Release](https://github.com/VirginiaH233/pomodoro-timer/releases)  
📦 [GitHub 源码](https://github.com/VirginiaH233/pomodoro-timer)

从源码运行：

```bash
pip install -r requirements.txt
python main.py
```

---

## 🎮 操作

```
 左键单击  →  暂停 / 继续
 按住拖拽  →  移动浮窗
 右下角 ╲  →  调整大小
 右键浮窗  →  菜单
 右键托盘  →  同上
```

---

## 🧩 结构

```
├── main.py         # 入口
├── overlay.py      # 玻璃浮窗 + 拖拽 + 托盘
├── pomtimer.py     # 计时状态机
├── config.py       # 配置 + 7 色预设
├── settings.py     # 设置面板
├── sound.py        # 提示音系统
├── lang.py         # 中英文
├── installer.nsi   # 安装包脚本
├── build.bat       # 打包脚本
└── README.md
```

---

## 📝 许可

MIT — 自由使用、修改、分发。
