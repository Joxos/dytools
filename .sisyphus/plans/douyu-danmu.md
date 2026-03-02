# Douyu Danmu Crawler - Work Plan

## TL;DR

> **Quick Summary**: 抓取斗鱼直播间6657的弹幕消息，通过WebSocket连接实时获取并保存到CSV文件
> 
> **Deliverables**:
> - Python脚本: `douyu_danmu.py` - 弹幕抓取主程序
> - CSV文件: `danmu_6657.csv` - 弹幕数据记录
> - requirements.txt - 依赖清单
> 
> **Estimated Effort**: Quick (简单任务)
> **Parallel Execution**: NO - 顺序执行
> **Critical Path**: 1 → 2 → 3 → 4

---

## Context

### Original Request
用户想要抓取斗鱼直播间 https://www.douyu.com/6657 的弹幕进行记录，保存到CSV文件。

### Interview Summary
**Key Discussions**:
- 技术栈: Python (推荐)
- 输出格式: CSV文件
- 功能: 基础弹幕记录（时间、用户、内容）

**Research Findings**:
- 斗鱼弹幕使用WebSocket协议 (wss://danmuproxy.douyu.com:850X/)
- 消息格式: 自定义二进制协议，key-value序列化
- 心跳: 每45秒发送 type@=mrkl/
- 消息类型: chatmsg(弹幕), uenter(入场), dgb(礼物)等

### Metis Review
**Identified Gaps** (addressed):
- 添加重连机制处理网络断开
- 直播间ID提取使用正则确保稳健
- CSV字段明确定义: 时间、用户、弹幕内容、用户等级、用户ID

---

## Work Objectives

### Core Objective
实现一个Python脚本，通过WebSocket连接斗鱼弹幕服务器，实时抓取直播间6657的所有弹幕消息，并保存到CSV文件。

### Concrete Deliverables
- `douyu_danmu.py` - 弹幕抓取主程序
- `danmu_6657.csv` - CSV文件（自动创建）
- `requirements.txt` - Python依赖 (websocket-client)
- `README.md` - 使用说明

### Definition of Done
- [x] 脚本能成功连接到斗鱼弹幕服务器
- [x] 能实时接收并解析弹幕消息
- [x] 弹幕数据正确保存到CSV文件
- [x] 程序能优雅退出 (Ctrl+C)

### Must Have
- WebSocket连接和心跳保持
- 弹幕消息解析 (type=chatmsg)
- CSV文件写入（含表头）
- 基础错误处理和重连

### Must NOT Have
- 不需要统计分析功能（用户说回头再做）
- 不需要GUI界面
- 不需要礼物/入场等非弹幕消息

---

## Verification Strategy

> **Agent-Executed QA** - 任务执行者需要验证脚本能正常运行

### Test Decision
- **Infrastructure exists**: NO (新项目)
- **Automated tests**: NO (手动验证即可)
- **Framework**: N/A
- **QA Method**: 实际运行脚本，观察输出和CSV文件生成

### QA Policy
每个任务包含Agent-Executed QA场景：
- 运行脚本，检查WebSocket连接是否成功
- 检查CSV文件是否创建并包含正确字段
- 观察是否实时接收到弹幕

---

## Execution Strategy

### Sequential Execution (简单任务，顺序执行)

```
Task 1: 创建项目结构和依赖文件
Task 2: 实现WebSocket连接和消息解析
Task 3: 实现CSV记录功能
Task 4: 测试运行并验证
```

### Dependency Matrix
- Task 1: — — 2, 3
- Task 2: 1 — 4, 3
- Task 3: 1 — 4
- Task 4: 2, 3 —

---

## TODOs

- [x] 1. 创建项目结构和依赖文件

  **What to do**:
  - 创建 `requirements.txt` 包含 `websocket-client>=1.0.0`
  - 创建 `douyu_danmu.py` 框架代码
  - 添加main函数和命令行参数解析

  **Must NOT do**:
  - 不要添加复杂的配置系统

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: 简单文件创建任务

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: 2, 3
  - **Blocked By**: None

  **References**:
  - Python项目结构参考: 简单单文件脚本
  - websocket-client文档: https://websocket-client.readthedocs.io/

  **Acceptance Criteria**:
  - [x] requirements.txt 包含 websocket-client
  - [x] douyu_danmu.py 存在且可导入

  **QA Scenarios**:

  Scenario: 验证项目结构创建成功
    Tool: Bash
    Preconditions: 无
    Steps:
      1. ls -la 检查文件存在
      2. cat requirements.txt 检查内容
    Expected Result: 文件存在，内容正确
    Evidence: terminal output

- [x] 2. 实现WebSocket连接和消息解析

  **What to do**:
  - 实现WebSocket连接函数 (wss://danmuproxy.douyu.com:8503/)
  - 实现登录请求: type@=loginreq/roomid@=6657/
  - 实现加入弹幕组: type@=joingroup/rid@=6657/gid@=-9999/
  - 实现心跳: type@=mrkl/ 每45秒
  - 实现消息解析函数 (二进制解包 + key-value反序列化)
  - 实现chatmsg消息解析

  **Must NOT do**:
  - 不实现复杂的重连逻辑（简单重试即可）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - Reason: 核心逻辑实现，需要正确处理二进制协议

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: 4
  - **Blocked By**: 1

  **References**:
  - 二进制协议格式: 4字节长度(两次) + 2字节消息类型 + 1字节加密 + 1字节保留 + 数据 + \0
  - 序列化格式: key1@=value1/key2@=value2/ (转义: @→@A, /→@S)
  - 参考实现: https://github.com/Kexiii/pydouyu

  **Acceptance Criteria**:
  - [x] WebSocket能成功连接到服务器
  - [x] 能接收到loginres响应
  - [x] 能接收到chatmsg消息

  **QA Scenarios**:

  Scenario: 测试WebSocket连接和消息接收
    Tool: Bash
    Preconditions: 安装依赖 pip install -r requirements.txt
    Steps:
      1. cd到项目目录
      2. 运行 python douyu_danmu.py
      3. 等待10秒观察输出
    Expected Result: 能看到连接成功和弹幕消息输出
    Evidence: terminal output截图

- [x] 3. 实现CSV记录功能

  **What to do**:
  - 使用csv模块写入CSV文件
  - CSV字段: timestamp, username, content, user_level, user_id, room_id
  - 创建CSV文件时写入表头
  - 每收到一条chatmsg就写入一行
  - 使用流式写入确保数据不丢失

  **Must NOT do**:
  - 不需要复杂的缓冲机制

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: 简单文件IO任务

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: 4
  - **Blocked By**: 1

  **References**:
  - Python csv模块文档
  - 字段顺序: 时间,用户名,弹幕内容,用户等级,用户ID,房间ID

  **Acceptance Criteria**:
  - [x] danmu_6657.csv 文件被创建
  - [x] CSV包含正确的表头
  - [x] 弹幕数据正确写入CSV

  **QA Scenarios**:

  Scenario: 验证CSV文件创建和写入
    Tool: Bash
    Preconditions: 脚本正在运行
    Steps:
      1. 检查CSV文件: ls -la danmu_6657.csv
      2. 查看内容: head -5 danmu_6657.csv
    Expected Result: 文件存在，有表头，有数据行
    Evidence: terminal output

- [x] 4. 测试运行并验证

  **What to do**:
  - 完整运行脚本5-10分钟
  - 验证能持续接收弹幕
  - 验证CSV文件持续写入
  - 验证Ctrl+C能优雅退出
  - 创建README.md说明使用方法

  **Must NOT do**:
  - 不需要长时间运行测试

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: 测试验证任务

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: 2, 3

  **References**:
  - N/A

  **Acceptance Criteria**:
  - [x] 脚本能稳定运行
  - [x] CSV文件持续更新
  - [x] Ctrl+C能停止程序
  - [x] README.md创建完成

  **QA Scenarios**:

  Scenario: 完整功能测试
    Tool: Bash
    Preconditions: 所有代码完成
    Steps:
      1. 启动脚本: python douyu_danmu.py
      2. 等待30秒收集数据
      3. Ctrl+C停止
      4. 检查CSV: wc -l danmu_6657.csv
    Expected Result: 有多条弹幕记录，程序正常退出
    Evidence: terminal output + CSV行数

---

## Final Verification Wave

> 简单任务，跳过并行审查

- [x] F1. **功能完整性检查**
  - 脚本能运行
  - CSV正确生成
  - 弹幕被记录

---

## Commit Strategy

- 完成后一次性提交所有文件
- Message: `feat: 添加斗鱼弹幕抓取工具`

---

## Success Criteria

### Verification Commands
```bash
pip install -r requirements.txt
python douyu_danmu.py
# 观察输出和CSV文件
```

### Final Checklist
- [x] requirements.txt 包含必要依赖
- [x] douyu_danmu.py 可运行
- [x] 能连接到斗鱼弹幕服务器
- [x] CSV文件被创建并包含弹幕数据
- [x] README.md 说明使用方法
