# Test Cases · 边界画像库

这里的每个 JSON 是一个"压力测试用画像", 用来快速验证系统行为是否符合预期.

## 当前画像列表

| ID | 画像 | 探测目的 |
|---|---|---|
| `00-baseline` | 47岁 测试经理 青岛 | 基线对照, 任何 prompt 改动后先跑这个看回归 |
| `01-young-beijing` | 28岁 后端 北京 25K | Agent 会不会还套'裁员焦虑'到年轻人身上 |
| `02-late-shanghai` | 55岁 技术总监 上海 80K | 真正的'晚期'判断是否准确 |
| `03-mid-burdened` | 35岁 前端 深圳 60K + 高负债 | 现金流压力下还会盲推'转型 AI' 吗 |
| `04-pm-hangzhou` | 42岁 PM 杭州 35K | mock 数据全是测试岗位, PM 完全是边界外 |

## 添加新画像

只要在本目录新建 `.json` 文件即可, 前端会自动列出. JSON 结构:

```json
{
  "id": "unique-short-id",
  "name": "显示给用户的简短名",
  "description": "这个画像描述什么场景",
  "probe": "这个画像想验证什么 / 想找出什么 bug",
  "profile": {
    "age": 0,
    "role": "",
    "industry": "",
    "city": "",
    "family": "",
    "mortgage_wan": 0,
    "current_monthly_salary_k": 0,
    "expectation": ""
  }
}
```

## 使用建议

1. **每次改 prompt 前**, 先跑 `00-baseline` 记录 evidence 内容
2. **改完 prompt 后**, 再跑 `00-baseline` 对比变化
3. **每周扫一遍 01-04**, 看是否在某个画像上出现新 bug

5-6 个样本跑下来, 你会发现 2-3 个 prompt 共性缺陷 — 那才是优化方向.
