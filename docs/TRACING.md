# TracingKit - Agent Execution Monitoring

`TracingKit` 是一個輕量級的追蹤工具包，用於監控和記錄 agent 的執行流程。

## 功能特性

✅ **零依賴** - 純 Python 標準庫實現
✅ **可選啟用** - 不影響現有代碼
✅ **低開銷** - 最小化性能影響
✅ **詳細記錄** - 完整的執行流程追蹤

## 記錄內容

TracingKit 會記錄：

1. **Agent 執行**
   - 開始時間和結束時間
   - 執行耗時
   - 執行結果和狀態
   - 父 Agent（用於追蹤委派鏈）
   - 委派深度（在委派層次中的位置）

2. **Agent 委派**
   - 委派開始：哪個 agent 委派給哪個 agent
   - 委派結束：委派結果和耗時
   - 完整的委派鏈追蹤（A → B → C）

3. **Tool 調用**
   - Tool 名稱
   - 參數
   - 返回結果
   - 執行耗時
   - 所屬的 Agent 和委派深度

4. **錯誤追蹤**
   - 錯誤類型
   - 錯誤訊息
   - 發生位置
   - 錯誤發生在哪個委派層級

## 快速開始

### 基本使用

```python
from fractal import BaseAgent

# 啟用 tracing
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyAgent",
            system_prompt="You are helpful.",
            enable_tracing=True  # 啟用追蹤
        )

# 使用 agent
agent = MyAgent()
result = await agent.run("Task")

# 查看追蹤記錄
if agent.tracing:
    summary = agent.tracing.get_summary()
    print(f"Tool calls: {summary['tool_calls']}")
    print(f"Total time: {summary['total_time']:.2f}s")
```

### 導出追蹤記錄

```python
# 啟用並自動導出到文件
agent = BaseAgent(
    name="MyAgent",
    system_prompt="You are helpful.",
    enable_tracing=True,
    tracing_output_file="trace.jsonl"  # JSON Lines 格式
)

# 或手動導出
result = await agent.run("Task")
agent.tracing.export_json("trace.jsonl")
```

## API 參考

### BaseAgent 參數

```python
BaseAgent(
    name: str,
    system_prompt: str,
    enable_tracing: bool = False,  # 啟用追蹤
    tracing_output_file: Optional[str] = None,  # 輸出文件
    ...
)
```

### TracingKit 方法

#### `get_trace() -> List[TraceEvent]`

獲取所有追蹤事件。

```python
events = agent.tracing.get_trace()
for event in events:
    print(f"{event.event_type}: {event.tool_name}")
```

#### `get_summary() -> Dict[str, Any]`

獲取追蹤摘要統計。

```python
summary = agent.tracing.get_summary()
# {
#     'total_events': 10,
#     'agent_runs': 1,
#     'tool_calls': 5,
#     'errors': 0,
#     'total_time': 2.5,
#     'average_tool_time': 0.4,
#     'success_rate': 1.0
# }
```

#### `export_json(filepath: str)`

導出追蹤記錄到 JSON Lines 文件。

```python
agent.tracing.export_json("trace.jsonl")
```

每行一個 JSON 事件，方便流式處理和分析。

#### `clear()`

清除所有追蹤記錄。

```python
agent.tracing.clear()
```

### TraceEvent 結構

```python
@dataclass
class TraceEvent:
    timestamp: float              # 時間戳
    event_type: str              # 事件類型
    agent_name: str              # Agent 名稱
    parent_agent: Optional[str]  # 父 Agent（委派鏈中的上層）
    delegation_depth: int        # 委派深度（0 = 頂層 agent）
    tool_name: Optional[str]     # Tool 名稱
    arguments: Optional[Dict]    # 參數
    result: Optional[Any]        # 結果
    error: Optional[str]         # 錯誤訊息
    elapsed_time: Optional[float] # 耗時（秒）
    metadata: Dict[str, Any]     # 額外元數據
```

**委派追蹤欄位**：

- `parent_agent`: 委派鏈中的父 agent 名稱（例如：A → B 中，B 的 parent_agent 是 A）
- `delegation_depth`: 在委派層次中的深度
  - 0 = 頂層 agent（沒有被委派）
  - 1 = 第一層委派的 agent
  - 2 = 第二層委派的 agent
  - 以此類推...

### 事件類型

- `agent_start` - Agent 開始執行
- `agent_end` - Agent 結束執行
- `agent_delegate` - Agent 委派給另一個 agent（委派開始）
- `delegation_end` - Agent 委派結束（返回結果）
- `tool_call` - Tool 調用開始
- `tool_result` - Tool 調用結束
- `error` - 錯誤發生

## 使用場景

### 1. 開發調試

查看 agent 執行流程，快速定位問題：

```python
agent = MyAgent(enable_tracing=True)
result = await agent.run("Debug this")

# 查看完整執行流程
for event in agent.tracing.get_trace():
    print(f"[{event.event_type}] {event.tool_name or event.agent_name}")
    if event.error:
        print(f"  Error: {event.error}")
```

### 2. 性能分析

分析哪些操作最耗時：

```python
agent = MyAgent(enable_tracing=True)
await agent.run("Task")

# 分析 tool 耗時
tool_events = [e for e in agent.tracing.get_trace()
               if e.event_type == 'tool_result']

for event in sorted(tool_events, key=lambda e: e.elapsed_time or 0, reverse=True):
    print(f"{event.tool_name}: {event.elapsed_time:.3f}s")
```

### 3. 生產監控

記錄生產環境的執行情況：

```python
# 啟用並持續記錄到文件
agent = MyAgent(
    enable_tracing=True,
    tracing_output_file="logs/agent_trace.jsonl"
)

# 每次執行都會追加到文件
result = await agent.run("Production task")

# 定期分析日誌
# tail -f logs/agent_trace.jsonl | jq '.event_type'
```

### 4. Multi-Agent 追蹤（Delegation-Aware）

TracingKit 自動追蹤完整的 agent 委派鏈：

```python
# 只需在頂層 agent 啟用 tracing
coordinator = CoordinatorAgent(enable_tracing=True)
specialist = SpecialistAgent(enable_tracing=False)  # 會被 "感染"

coordinator.register_delegate(specialist)

# 執行
await coordinator.run("Complex task")

# coordinator 的 tracing 會記錄所有內容，包括 specialist 的執行
summary = coordinator.tracing.get_summary()
print(f"Total agent runs: {summary['agent_runs']}")  # 包含 coordinator 和 specialist

# 查看完整委派鏈
events = coordinator.tracing.get_trace()
for event in events:
    if event.event_type == 'agent_start':
        indent = "  " * event.delegation_depth
        parent = f" <- {event.parent_agent}" if event.parent_agent else ""
        print(f"{indent}{event.agent_name} (depth={event.delegation_depth}){parent}")
```

**多層委派（A → B → C）**：

```python
# 設置多層委派
specialist_c = SpecialistAgent(name="C")
specialist_b = SpecialistAgent(name="B")
coordinator_a = CoordinatorAgent(name="A", enable_tracing=True)

# B 委派給 C
specialist_b.register_delegate(specialist_c)

# A 委派給 B
coordinator_a.register_delegate(specialist_b)

# 執行 - 完整的 A → B → C 鏈會被追蹤
await coordinator_a.run("Task requiring deep delegation")

# 查看完整委派層次
for event in coordinator_a.tracing.get_trace():
    if event.event_type == 'agent_start':
        print(f"{'  ' * event.delegation_depth}{event.agent_name}")
# 輸出:
# A
#   B
#     C
```

**委派事件**：

```python
# 查看委派事件
delegation_events = [
    e for e in coordinator.tracing.get_trace()
    if e.event_type in ('agent_delegate', 'delegation_end')
]

for event in delegation_events:
    if event.event_type == 'agent_delegate':
        to_agent = event.arguments.get('to_agent')
        print(f"Delegate: {event.agent_name} → {to_agent}")
    else:
        from_agent = event.metadata.get('to_agent')
        print(f"Return: {from_agent} → {event.agent_name}")
```

## 性能影響

TracingKit 設計為低開銷：

- **最小 overhead**: < 5% 額外時間
- **內存效率**: 只在內存中保存事件
- **可選啟用**: 不啟用時零影響

```python
# 測試性能影響
import time

# Without tracing
agent = MyAgent(enable_tracing=False)
start = time.time()
await agent.run("Task")
time_no_trace = time.time() - start

# With tracing
agent = MyAgent(enable_tracing=True)
start = time.time()
await agent.run("Task")
time_with_trace = time.time() - start

overhead = (time_with_trace / time_no_trace - 1) * 100
print(f"Tracing overhead: {overhead:.1f}%")
```

## 輸出格式

### JSON Lines (.jsonl)

每行一個 JSON 事件，方便流式處理：

```json
{"timestamp": 1234567890.123, "event_type": "agent_start", "agent_name": "MyAgent", ...}
{"timestamp": 1234567890.234, "event_type": "tool_call", "tool_name": "process", ...}
{"timestamp": 1234567890.345, "event_type": "tool_result", "tool_name": "process", ...}
{"timestamp": 1234567890.456, "event_type": "agent_end", "agent_name": "MyAgent", ...}
```

### 使用 jq 分析

```bash
# 查看所有事件類型
cat trace.jsonl | jq '.event_type'

# 查看所有 tool 調用
cat trace.jsonl | jq 'select(.event_type == "tool_call") | .tool_name'

# 查看錯誤
cat trace.jsonl | jq 'select(.error != null)'

# 計算平均耗時
cat trace.jsonl | jq 'select(.elapsed_time != null) | .elapsed_time' | awk '{sum+=$1} END {print sum/NR}'
```

## 最佳實踐

### 1. 開發時啟用，生產時選擇性啟用

```python
import os

enable_tracing = os.getenv("ENABLE_TRACING", "false").lower() == "true"

agent = MyAgent(enable_tracing=enable_tracing)
```

### 2. 定期清理追蹤記錄

```python
# 處理完一個任務後清理
await agent.run("Task 1")
agent.tracing.clear()

await agent.run("Task 2")
agent.tracing.clear()
```

### 3. 結合日誌系統

```python
import logging

agent = MyAgent(enable_tracing=True)
result = await agent.run("Task")

# 記錄摘要到日誌
if agent.tracing:
    summary = agent.tracing.get_summary()
    logging.info(f"Agent completed: {summary}")
```

### 4. 異常情況詳細分析

```python
agent = MyAgent(enable_tracing=True)

try:
    result = await agent.run("Task")
except Exception as e:
    # 出錯時導出完整追蹤
    if agent.tracing:
        agent.tracing.export_json(f"error_trace_{time.time()}.jsonl")
    raise
```

## 完整示例

查看 [examples/tracing_example.py](examples/tracing_example.py) 獲取完整的使用示例。

運行示例：
```bash
python examples/tracing_example.py
```

## 總結

TracingKit 提供：
- ✅ 簡單易用的 API
- ✅ 詳細的執行記錄
- ✅ 低性能開銷
- ✅ 靈活的導出選項
- ✅ 無外部依賴

非常適合用於開發調試、性能分析和生產監控！
