# GhostFabric

<p align="center">
  <strong>唤醒沉睡的数据中心算力。</strong><br />
  面向领域专家系统的置信度感知解码、RAG 检索增强与受限 Agent 执行框架。
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">中文</a>
</p>

## 项目定位

GhostFabric 是一套公开参考实现，目标不是做通用聊天壳，而是帮助团队把“还在机房里、但越来越难用”的存量算力重新变成可用生产力。

它面向的不是消费级 PC，而是老旧数据中心集群、历史推理卡部署、兼容层复杂且运维成本越来越高的基础设施环境。

GhostFabric 的核心技术组合是：

- `DeepConf` 风格的置信度感知解码
- 面向代码、文档、配置、日志的 `RAG` 检索增强
- OpenAI 兼容的 `tool-calling` 接口
- 带白名单和安全边界的受限执行能力

## 为什么 DeepConf 对 Qwen2.5 有价值

`Qwen2.5` 往往不是“不会”，而是“单次回答不够稳”。

DeepConf 的意义在于：不把一次生成结果直接当成最终答案，而是通过多条候选推理轨迹和 token 级置信度打分，尽量选择更强的一条。

这在以下任务里尤其有价值：

- 技术问答
- 代码解释
- 多步推理
- 那些“模型有能力答对，但偶尔会跑偏”的场景

## 为什么 DeepConf 对专家模式有利

专家模式本质上不是 prompt，而是系统工程：

`检索质量 + 回答策略 + 置信度感知解码 + 严格评测`

DeepConf 最擅长解决的是最后一层：当检索已经把相关证据拿回来时，它能减少弱推理路径主导最终回答的概率。

## 推荐阅读

- [架构说明](docs/architecture.md)
- [安全边界](docs/safety.md)
- [专家模式训练方法](docs/expert-mode-training.md)
- [项目愿景](docs/vision.md)
- [Benchmark 说明](docs/benchmark.md)
- [Ascend 910 案例研究](docs/case-study-ascend910.zh-CN.md)

## 中文版本策略

建议优先维护“核心页面双语”，而不是一开始就把整个仓库全部翻译。

当前最值得双语化的内容是：

- 首页 README
- 安全说明
- 专家模式训练方法
- 典型案例研究

这样既能服务中文读者，也不会把文档维护成本立刻拉爆。
