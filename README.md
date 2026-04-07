# Skills Repository

存放各类有用的 Claude Code Skills。

## 结构

```
skills/
├── email/        # 邮件发送 Skill
├── auto-chart/   # 自动图表生成 Skill
├── ...           # 更多 skills
└── README.md     # 本文件
```

## 使用方式

将 skill 目录复制或链接到 Claude Code 的 skills 配置目录。

## Skills 列表

| Skill | 描述 | 依赖 |
|-------|------|------|
| [email](./email/) | 邮件发送，支持转发对话内容 | Python 标准库 |
| [auto-chart](./auto-chart/) | AI稽查Agent自动图表识别与生成 | Vega-Lite |