# Proposal: Add Transcript Semantic Segmentation

## Why

当前 `TranscriptScraper` 缺乏语义分段能力。用户需要在生成 spec 之前，先对 transcript 进行结构化分析和总结。

## What

新增"分段总结"预处理步骤，工作流如下：

```
【原始 transcript】                    【AI 编程助手执行分段总结】
      │                                         │
      ▼                                         ▼
scraped_data.json  ──────────┬──────── segmented_summary.json
                             │
                             ▼
               【综合生成 spec.yaml】
               （同时参考原文和分段总结）
```

**核心功能：**
1. 根据语义标志词（"好"、"下一个"等）精确分段
2. 在主分段内识别子分段
3. 为每段提供全面总结（让未读原文者能吸收所有信息）
4. 保留时间戳、修正同音字错误
5. 输出独立的 `segmented_summary.json` 文件
6. 生成 spec 时同时参考原始文本（验证准确性）和分段总结

**执行方式：** AI 编程助手手动执行，非运行时 API 调用

## How

详见 [design.md](./design.md)

## Constraints

- 分段总结是手动工作流步骤
- 保持向后兼容（无分段数据时正常工作）
- JSON 格式输出，便于后续处理
