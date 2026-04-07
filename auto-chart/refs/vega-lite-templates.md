# Vega-Lite 模板参考

## 基础结构

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "mark": "bar",
  "data": { "values": [...] },
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "value", "type": "quantitative"}
  }
}
```

## 图表模板

### 1. 柱状图 (Bar Chart)

**比较/排名场景**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "各分类数值对比",
  "mark": "bar",
  "data": {
    "values": [
      {"category": "A", "value": 100},
      {"category": "B", "value": 80},
      {"category": "C", "value": 60}
    ]
  },
  "encoding": {
    "x": {"field": "category", "type": "nominal", "axis": {"title": "分类"}},
    "y": {"field": "value", "type": "quantitative", "axis": {"title": "数值"}}
  }
}
```

**水平柱状图（分类名较长）**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "水平柱状图",
  "mark": "bar",
  "data": {"values": [...]},
  "encoding": {
    "y": {"field": "category", "type": "nominal"},
    "x": {"field": "value", "type": "quantitative"}
  }
}
```

### 2. 折线图 (Line Chart)

**趋势/时序场景**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "时间趋势变化",
  "mark": "line",
  "data": {
    "values": [
      {"date": "2024-01", "value": 120},
      {"date": "2024-02", "value": 150},
      {"date": "2024-03", "value": 180}
    ]
  },
  "encoding": {
    "x": {"field": "date", "type": "temporal", "axis": {"title": "时间"}},
    "y": {"field": "value", "type": "quantitative", "axis": {"title": "数值"}}
  }
}
```

**带数据点标记**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "mark": {"type": "line", "point": true},
  "data": {"values": [...]},
  "encoding": {...}
}
```

### 3. 饼图/环形图 (Pie/Donut)

**占比/构成场景**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "占比分布",
  "mark": {"type": "arc", "innerRadius": 0},  // innerRadius>0 为环形图
  "data": {
    "values": [
      {"category": "类型A", "value": 40},
      {"category": "类型B", "value": 30},
      {"category": "类型C", "value": 20},
      {"category": "其他", "value": 10}
    ]
  },
  "encoding": {
    "theta": {"field": "value", "type": "quantitative"},
    "color": {"field": "category", "type": "nominal", "legend": {"title": "类型"}}
  },
  "view": {"stroke": null}
}
```

**环形图(Donut)**

```json
{
  "mark": {"type": "arc", "innerRadius": 50}
}
```

### 4. 直方图 (Histogram)

**分布场景**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "数值分布",
  "mark": "bar",
  "data": {
    "values": [5, 8, 8, 12, 15, 18, 18, 22, 25, 28]
  },
  "encoding": {
    "x": {
      "field": "data",
      "type": "quantitative",
      "bin": true,
      "axis": {"title": "数值区间"}
    },
    "y": {
      "aggregate": "count",
      "type": "quantitative",
      "axis": {"title": "频数"}
    }
  }
}
```

### 5. 散点图 (Scatter Plot)

**相关性/分布场景**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "变量关系",
  "mark": "point",
  "data": {
    "values": [
      {"x": 10, "y": 20},
      {"x": 15, "y": 25},
      {"x": 20, "y": 35}
    ]
  },
  "encoding": {
    "x": {"field": "x", "type": "quantitative", "axis": {"title": "变量X"}},
    "y": {"field": "y", "type": "quantitative", "axis": {"title": "变量Y"}},
    "size": {"value": 100}
  }
}
```

### 6. 面积图 (Area Chart)

**累积趋势**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "累积面积",
  "mark": "area",
  "data": {"values": [...]},
  "encoding": {
    "x": {"field": "date", "type": "temporal"},
    "y": {"field": "value", "type": "quantitative"}
  }
}
```

### 7. 分组柱状图 (Grouped Bar)

**多维度比较**

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "分组比较",
  "mark": "bar",
  "data": {
    "values": [
      {"category": "A", "group": "G1", "value": 100},
      {"category": "A", "group": "G2", "value": 80},
      {"category": "B", "group": "G1", "value": 60},
      {"category": "B", "group": "G2", "value": 90}
    ]
  },
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "value", "type": "quantitative"},
    "color": {"field": "group", "type": "nominal"},
    "column": {"field": "group", "type": "nominal"}
  }
}
```

### 8. 堆叠柱状图 (Stacked Bar)

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "title": "堆叠占比",
  "mark": "bar",
  "data": {"values": [...]},
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "value", "type": "quantitative", "aggregate": "sum"},
    "color": {"field": "group", "type": "nominal"}
  }
}
```

## 常用配置

### 中文标题支持

```json
{
  "title": {"text": "中文标题", "font": "Arial Unicode MS"}
}
```

### 响应式尺寸

```json
{
  "width": "container",
  "height": 300
}
```

### 颜色方案

```json
"encoding": {
  "color": {
    "field": "category",
    "type": "nominal",
    "scale": {"scheme": "category20"}  // 或 "blues", "greens", "rainbow"
  }
}
```

### 工具提示

```json
"encoding": {
  "tooltip": [
    {"field": "category", "type": "nominal"},
    {"field": "value", "type": "quantitative", "format": ".2f"}
  ]
}
```

### X轴标签旋转（防止重叠）

```json
"encoding": {
  "x": {
    "field": "category",
    "type": "nominal",
    "axis": {"labelAngle": -45, "labelAlign": "right"}
  }
}
```

### 数值格式化

```json
"encoding": {
  "y": {
    "field": "value",
    "type": "quantitative",
    "axis": {"format": ".2f"}  // 或 ".0%", "$,.0f"
  }
}
```

## 决策规则速查表

| 数据特征 | 推荐mark | 典型encoding |
|---------|---------|-------------|
| 时间+数值 | `line` | x:T, y:Q |
| 分类+数值(≤5类) | `arc` | theta:Q, color:N |
| 分类+数值(>5类) | `bar` | x:N, y:Q |
| 单数值分布 | `bar`(bin) | x:Q(bin), y:count |
| 双数值相关 | `point` | x:Q, y:Q |
| 分类+双数值 | `bar`(grouped) | x:N, y:Q, color:N |

## 输出规范

**必须包含：**
- `$schema`: 固定值
- `mark`: 图表类型
- `data.values`: 数据数组
- `encoding`: 字段映射

**禁止包含：**
- markdown代码块包裹
- 多余注释
- 非标准字段