# 更新说明

## 2026-03-25

- Windows 自启动方式从启动目录快捷方式切换为计划任务 + `start_blog.bat`。
- `start_blog.bat` 现在会固定到项目根目录启动，优先使用项目 `.venv`，找不到时回退系统 `python`，并将日志写入 `%LOCALAPPDATA%\PersonalBlog\logs\startup.log`。
- 启动脚本新增端口 `10024` 检测，服务已运行时会直接跳过重复启动并记录日志。
- 新增 `scripts/register_personal_blog_task.ps1`，用于注册或更新隐藏的 `PersonalBlog` 登录任务，并清理旧的 `PersonalBlog.lnk`。
- README 补充了 Windows 手动启动与静默开机自启动的使用说明。
