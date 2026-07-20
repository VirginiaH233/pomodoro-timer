# 🍅 Pomodoro Timer — Windows 桌面番茄钟

半透明玻璃浮窗番茄钟，常驻屏幕右下角，自由拖拽缩放。

## 功能

- **玻璃半透明浮窗** — 不占任务栏空间，存在感极低
- **7 种颜色预设** — ☀️ Light / 🌙 Dark / 💙 Blue / 🌿 Mint / 💜 Purple / 🍑 Peach / 🪨 Slate
- **自由拖拽缩放** — 按住任意位置拖拽移动，拖拽右下角调整大小
- **标准番茄周期** — 25min 工作 → 5min 短休 → 15min 长休（可自定义）
- **系统托盘图标** — 通知区域常驻，右键即可操作
- **图形化设置面板** — 所有参数在设置对话框中可视化调整
- **完成庆祝效果** — 工作阶段完成时浮窗闪烁 🎉 动画
- **Windows 气泡通知** — 阶段切换时系统托盘弹出提示

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt
# 或
uv pip install pystray pillow pywin32

# 启动
python main.py
```

双击 **`start.bat`** 也能一键启动。

## 操作指南

| 操作 | 方式 |
|------|------|
| 暂停 / 继续 | 单击浮窗 |
| 移动浮窗 | 按住浮窗拖拽 |
| 调整大小 | 拖拽右下角 `╲╲╲` 把手 |
| 右键菜单 | 右键浮窗或托盘图标 |
| 设置 | 右键 → ⚙ Settings... |

## 设置面板

```
⏱  TIMER DURATIONS    — 工作时长 / 短休息 / 长休息 / 长休息触发间隔
⚙  BEHAVIOR           — 自动开始休息 / 自动开始工作
🎨  APPEARANCE         — 7色预设 / 透明度 / 窗口置顶
🎉  REWARDS            — 完成庆祝效果
```

## 配置文件

首次启动后自动生成 `pomodoro_config.json`（也可通过图形设置面板修改）：

```json
{
  "work_minutes": 25,
  "short_break_minutes": 5,
  "long_break_minutes": 15,
  "sessions_before_long_break": 4,
  "color_preset": "light",
  "window_opacity": 0.88,
  "always_on_top": true,
  "reward_enabled": true
}
```

## 技术栈

- **Python 3.11** — 纯 Python，无 Electron
- **tkinter** — 玻璃浮窗渲染，圆角裁剪
- **pystray** — 系统托盘图标，菜单交互
- **Pillow** — 托盘图标生成（32×32 RGBA）
- **pywin32** — Windows API（圆角 SetWindowRgn、气泡通知）

## 项目结构

```
pomodoro_timer/
├── main.py         # 入口
├── overlay.py      # 浮窗 UI + 拖拽 + 托盘
├── pomtimer.py     # 计时器状态机
├── config.py       # 配置 + 7 色预设
├── settings.py     # 图形化设置对话框
├── icon_gen.py     # Pillow 图标渲染
├── notifier.py     # 通知模块
├── start.bat       # 一键启动
└── README.md
```

## 许可

MIT
