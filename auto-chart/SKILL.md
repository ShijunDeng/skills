---
name: auto-chart
description: >
  AI稽查Agent自动图表识别与生成。
  Use when: Agent查询结果需要可视化展示、用户询问涉及趋势/占比/分布/比较、数据输出包含表格/数值序列。
  Not for: 简单文本回答、单条记录查询、用户明确指定"不要图表"。
  Output: 标准Vega-Lite规范JSON（可直接渲染）。
triggers:
  - "查询结果"
  - "数据显示"
  - "趋势"
  - "占比"
  - "分布"
  - "比较"
  - "可视化"
  - "图表"
  - "表格数据"
  - "数值序列"
not_for:
  - "纯文本"
  - "单条记录"
  - "不要图表"
output: "Vega-Lite JSON spec"
next: null
---

# Auto Chart — 自动图表识别与生成

> 基于Microsoft LIDA架构：数据摘要 → 目标识别 → 图表推荐 → Vega-Lite生成

## 核心架构（借鉴LIDA）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   数据输入   │ --> │  数据摘要   │ --> │  目标识别   │ --> │  图表生成   │
│  (原始数据)  │     │ (Summarizer)│     │ (GoalExplorer)│   │ (VizGenerator)│
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                    │                    │
                           v                    v                    v
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │ 字段类型识别 │     │ 问题+图表意图│     │ Vega-Lite   │
                    │ 统计属性提取 │     │ rationale   │     │ JSON输出    │
                    │ semantic_type│     │             │     │             │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Step 1: 数据摘要（Summarizer）

**借鉴 LIDA Summarizer 的字段分析逻辑**

### 字段类型识别规则

| 原始类型 | 判断条件 | LIDA dtype | Vega-Lite type |
|---------|---------|------------|----------------|
| int/float | 数值型 | `number` | `:Q` (quantitative) |
| datetime | 可解析为日期 | `date` | `:T` (temporal) |
| string | nunique/len < 0.5 | `category` | `:N` (nominal) |
| string | nunique/len ≥ 0.5 | `string` | `:N` (nominal) |
| bool | 布尔型 | `boolean` | `:N` (nominal) |

### 字段属性提取（每字段必填）

```json
{
  "column": "sales",
  "properties": {
    "dtype": "number",
    "min": 100,
    "max": 500,
    "std": 120.5,
    "samples": [150, 280, 420],
    "num_unique_values": 5,
    "semantic_type": "currency",
    "description": "销售金额（单位：万元）"
  }
}
```

### 语义类型推断（semantic_type）

| 字段名特征 | 样本值特征 | semantic_type |
|-----------|-----------|---------------|
| 含date/time/年/月 | 日期格式 | `temporal` |
| 含price/amount/sales | 数值+货币符号 | `currency` |
| 含city/country/region | 地名 | `geographic` |
| 含name/id/code | 标识符 | `identifier` |
| 含rate/ratio/percent | 0-1之间或百分比 | `ratio` |
| 含count/num/quantity | 整数 | `count` |

---

## Step 2: 目标识别（GoalExplorer）

**借鉴 LIDA GoalExplorer 的 Goal 结构**

### Goal 定义

```json
{
  "index": 0,
  "question": "各产品线的销售额对比情况如何？",
  "visualization": "bar chart of sales by product",
  "rationale": "使用柱状图对比各产品线销售额，字段product为nominal，sales为quantitative"
}
```

### 意图识别关键词（从用户输入提取）

| 意图类别 | 关键词 | 推荐图表 |
|---------|-------|---------|
| `trend` | 趋势/变化/增长/下降/演变/走势 | `line` |
| `proportion` | 占比/比例/份额/构成/组成/分布 | `arc` |
| `comparison` | 对比/比较/差异/差别/versus | `bar` |
| `ranking` | 排名/排序/top/排行/榜单 | `bar`(横向) |
| `distribution` | 分布/频率/密度/分散 | `bar`(bin) |
| `relationship` | 关系/相关/关联/影响 | `point` |
| `composition` | 构成/组成/结构/ breakdown | `bar`(stacked) |

### Goal 生成示例

**输入数据摘要：**
```json
{
  "fields": [
    {"column": "month", "properties": {"dtype": "date", "semantic_type": "temporal"}},
    {"column": "sales", "properties": {"dtype": "number", "semantic_type": "currency"}}
  ]
}
```

**用户输入：** "展示各月销售额变化"

**识别 Goal：**
```json
{
  "question": "各月销售额的变化趋势如何？",
  "visualization": "line chart with month on x-axis, sales on y-axis",
  "rationale": "month为temporal，sales为quantitative，趋势意图→折线图"
}
```

---

## Step 3: 图表推荐决策

**借鉴 LIDA 的可视化最佳实践**

### 决策矩阵（Goal.visualization → Vega-Lite mark）

| 数据特征组合 | 用户意图 | 推荐mark | encoding |
|-------------|---------|---------|----------|
| temporal + quantitative | trend | `line` | x:T, y:Q |
| nominal(≤5) + quantitative | proportion | `arc` | theta:Q, color:N |
| nominal(≤10) + quantitative | comparison | `bar` | x:N, y:Q |
| nominal + quantitative | ranking | `bar` | x:Q, y:N(sort=-x) |
| quantitative + quantitative | relationship | `point` | x:Q, y:Q |
| quantitative | distribution | `bar`(bin) | x:Q(bin), y:count |
| temporal + quantitative | composition | `area` | x:T, y:Q |
| nominal + nominal + quantitative | breakdown | `bar`(stacked) | x:N, y:Q, color:N |

### 特殊规则

```
饼图限制：分类数 ≤ 8，否则改用 bar
柱状图标签：分类名过长或数量>10 → 横向柱状图
折线图：必须有时间维度，否则用 bar
单条记录：不生成图表，直接文本
数值精度：大数值加 format: ",.0f"，百分比加 format: ".1%"
```

---

## Step 4: Vega-Lite生成（VizGenerator）

**借鉴 LIDA VizGenerator 的代码生成逻辑**

### 输出规范（必须）

1. **$schema**: 固定 `https://vega.github.io/schema/vega-lite/v5.json`
2. **mark**: 图表类型
3. **data.values**: 数据数组（内嵌）
4. **encoding**: 字段映射，必须指定 type

### 字段类型映射（semantic_type → Vega-Lite type）

```
temporal → :T
currency/ratio/count → :Q
geographic/nominal → :N
identifier → :N (但通常不用于可视化)
```

### 生成模板（Altair风格）

**折线图模板：**
```json
{
  "$schema": "...",
  "mark": {"type": "line", "point": true},
  "encoding": {
    "x": {"field": "<temporal_field>", "type": "temporal", "axis": {"labelAngle": -45}},
    "y": {"field": "<quantitative_field>", "type": "quantitative"}
  }
}
```

**柱状图模板：**
```json
{
  "$schema": "...",
  "mark": "bar",
  "encoding": {
    "x": {"field": "<nominal_field>", "type": "nominal", "axis": {"labelAngle": -45}},
    "y": {"field": "<quantitative_field>", "type": "quantitative"},
    "tooltip": [{"field": "<nominal>", "type": "nominal"}, {"field": "<quant>", "type": "quantitative"}]
  }
}
```

**饼图/环形图模板：**
```json
{
  "$schema": "...",
  "mark": {"type": "arc", "innerRadius": 50},
  "encoding": {
    "theta": {"field": "<quantitative_field>", "type": "quantitative"},
    "color": {"field": "<nominal_field>", "type": "nominal", "legend": {"title": "..."}}
  },
  "view": {"stroke": null}
}
```

---

## 具体示例（完整流程演示）

### 示例 1：趋势分析 → 折线图

**Step 1 - 数据摘要：**
```json
{
  "fields": [
    {"column": "month", "dtype": "date", "semantic_type": "temporal", "samples": ["2024-01", "2024-02"]},
    {"column": "sales", "dtype": "number", "semantic_type": "currency", "min": 100, "max": 145}
  ]
}
```

**Step 2 - Goal识别：**
```json
{
  "question": "各月销售额的变化趋势？",
  "visualization": "line chart of sales over month",
  "rationale": "temporal + quantitative + trend意图 → 折线图"
}
```

**Step 4 - Vega-Lite输出：**
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "月度销售额趋势",
  "mark": {"type": "line", "point": true},
  "data": {"values": [
    {"month": "2024-01", "sales": 100},
    {"month": "2024-02", "sales": 120},
    {"month": "2024-03", "sales": 115},
    {"month": "2024-04", "sales": 130},
    {"month": "2024-05", "sales": 145}
  ]},
  "encoding": {
    "x": {"field": "month", "type": "temporal", "axis": {"labelAngle": -45, "title": "月份"}},
    "y": {"field": "sales", "type": "quantitative", "axis": {"title": "销售额"}}
  }
}
```

---

### 示例 2：占比分析 → 环形图

**Step 1 - 数据摘要：**
```json
{
  "fields": [
    {"column": "department", "dtype": "category", "semantic_type": "nominal", "num_unique_values": 4},
    {"column": "ratio", "dtype": "number", "semantic_type": "ratio", "min": 0.1, "max": 0.45}
  ]
}
```

**Step 2 - Goal识别：**
```json
{
  "question": "各部门预算占比情况？",
  "visualization": "pie/donut chart of budget ratio by department",
  "rationale": "nominal(4类≤8) + ratio + proportion意图 → 饼图/环形图"
}
```

**Step 4 - Vega-Lite输出：**
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "部门预算占比",
  "mark": {"type": "arc", "innerRadius": 50},
  "data": {"values": [
    {"department": "市场部", "ratio": 0.30},
    {"department": "技术部", "ratio": 0.45},
    {"department": "人力部", "ratio": 0.15},
    {"department": "行政部", "ratio": 0.10}
  ]},
  "encoding": {
    "theta": {"field": "ratio", "type": "quantitative"},
    "color": {"field": "department", "type": "nominal", "legend": {"title": "部门"}},
    "tooltip": [{"field": "department", "type": "nominal"}, {"field": "ratio", "type": "quantitative", "format": ".1%"}]
  },
  "view": {"stroke": null}
}
```

---

### 示例 3：排名分析 → 横向柱状图

**Step 1 - 数据摘要：**
```json
{
  "fields": [
    {"column": "employee", "dtype": "string", "semantic_type": "identifier", "num_unique_values": 5},
    {"column": "sales", "dtype": "number", "semantic_type": "currency", "max": 500}
  ]
}
```

**Step 2 - Goal识别：**
```json
{
  "question": "销售业绩排名前5的员工？",
  "visualization": "horizontal bar chart sorted by sales",
  "rationale": "ranking意图 → 横向柱状图，便于显示员工姓名"
}
```

**Step 4 - Vega-Lite输出：**
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "销售业绩排行",
  "mark": "bar",
  "data": {"values": [
    {"employee": "张三", "sales": 500},
    {"employee": "李四", "sales": 450},
    {"employee": "王五", "sales": 420},
    {"employee": "赵六", "sales": 380},
    {"employee": "钱七", "sales": 350}
  ]},
  "encoding": {
    "y": {"field": "employee", "type": "nominal", "sort": "-x", "axis": {"title": "员工"}},
    "x": {"field": "sales", "type": "quantitative", "axis": {"title": "销售额"}},
    "tooltip": [{"field": "employee", "type": "nominal"}, {"field": "sales", "type": "quantitative"}]
  }
}
```

---

### 示例 4：相关性分析 → 散点图

**Step 1 - 数据摘要：**
```json
{
  "fields": [
    {"column": "ad_spend", "dtype": "number", "semantic_type": "currency"},
    {"column": "revenue", "dtype": "number", "semantic_type": "currency"}
  ]
}
```

**Step 2 - Goal识别：**
```json
{
  "question": "广告投入与销售额的关系？",
  "visualization": "scatter plot of ad_spend vs revenue",
  "rationale": "quantitative + quantitative + relationship意图 → 散点图"
}
```

**Step 4 - Vega-Lite输出：**
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "广告投入 vs 销售额",
  "mark": {"type": "point", "filled": true, "size": 100},
  "data": {"values": [
    {"ad_spend": 10, "revenue": 100},
    {"ad_spend": 15, "revenue": 140},
    {"ad_spend": 20, "revenue": 180},
    {"ad_spend": 25, "revenue": 220},
    {"ad_spend": 30, "revenue": 280}
  ]},
  "encoding": {
    "x": {"field": "ad_spend", "type": "quantitative", "scale": {"zero": false}, "axis": {"title": "广告投入"}},
    "y": {"field": "revenue", "type": "quantitative", "scale": {"zero": false}, "axis": {"title": "销售额"}},
    "tooltip": [{"field": "ad_spend", "type": "quantitative"}, {"field": "revenue", "type": "quantitative"}]
  }
}
```

---

### 示例 5：分类过多 → 柱状图替代饼图

**数据特征：** 12个城市，分类数 > 8

**判断规则：** 饼图切片过多 → 改用横向柱状图

**Step 4 - Vega-Lite输出：**
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "各城市用户分布",
  "mark": "bar",
  "data": {"values": [
    {"city": "北京", "users": 5000},
    {"city": "上海", "users": 4500},
    {"city": "广州", "users": 3800},
    {"city": "深圳", "users": 3500},
    {"city": "杭州", "users": 2800},
    {"city": "成都", "users": 2500},
    {"city": "武汉", "users": 2200},
    {"city": "西安", "users": 1800},
    {"city": "南京", "users": 1500},
    {"city": "重庆", "users": 1200},
    {"city": "苏州", "users": 1000},
    {"city": "天津", "users": 800}
  ]},
  "encoding": {
    "y": {"field": "city", "type": "nominal", "sort": "-x"},
    "x": {"field": "users", "type": "quantitative"}
  }
}
```

---

### 示例 6：不需要图表 → 文本输出

**判断条件：**
- 无意图关键词
- 无结构化数据
- 单条记录（<3行）
- 用户明确要求文本

**处理：** 不生成 Vega-Lite，直接文本回复

---

## 常见错误修正（LIDA VizRepairer风格）

| 问题 | 检测方法 | 修复方案 |
|------|---------|---------|
| X轴标签重叠 | 分类数>10或标签过长 | `labelAngle: -45` 或横向柱状图 |
| 数值精度过高 | 大数值无format | `"format": ",.0f"` |
| 百分比显示错误 | ratio字段未format | `"format": ".1%"` |
| 饼图切片过多 | 分类>8 | 改用柱状图 |
| 时间轴未排序 | temporal字段乱序 | 数据预排序 |
| 缺少图例标题 | color encoding无legend | `"legend": {"title": "..."}` |

---

## 与其他Skill的关系

- `rich-messaging`：发送富媒体消息 — auto-chart专注**生成**图表规范，rich-messaging负责**发送**
- `pencil-design`：创建UI设计稿 — auto-chart是**数据可视化**，pencil是**界面设计**
- `browser-preview`：预览前端 — auto-chart产出的Vega-Lite可被browser-preview渲染

---

## 执行流程总结

```
用户输入 + 数据
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. 数据摘要 (Summarizer)                 │
│    - 字段类型: number/date/category/string│
│    - 统计属性: min/max/std/samples        │
│    - 语义类型: temporal/currency/geographic│
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 2. 目标识别 (GoalExplorer)               │
│    - question: 用户想了解什么？           │
│    - visualization: 用什么图表？          │
│    - rationale: 为什么选这个图？          │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 3. 图表推荐决策                          │
│    - 数据特征 + 用户意图 → mark类型       │
│    - 应用特殊规则（饼图限制等）           │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 4. Vega-Lite生成 (VizGenerator)          │
│    - 输出完整JSON规范                     │
│    - 确保encoding.type正确               │
│    - 添加tooltip、format等细节           │
└─────────────────────────────────────────┘
    │
    ▼
Vega-Lite JSON (可直接渲染)
```

---

## 模板参考

详细模板见 `refs/vega-lite-templates.md`