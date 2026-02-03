# Trace Visualization

可視化工具用於查看和分析 agent 執行追蹤。**Zero dependency** - 只需要 Python 標準庫和瀏覽器。

## 可視化工具

### 1. HTML 可視化（互動式）

生成一個 self-contained HTML 文件，可以在瀏覽器中互動式查看。

**使用方法**：

```bash
# 基本用法
python -m fractal.observability visualize trace.jsonl

# 指定輸出文件
python -m fractal.observability visualize trace.jsonl -o my_trace.html
```

**功能特性**：

- **Timeline 視圖**：顯示完整的執行時間軸
  - 事件按時間順序排列
  - 顏色標記不同的事件類型
  - 縮排顯示委派層級

- **Hierarchy 視圖**：顯示 agent 委派層次結構
  - 樹狀結構顯示 agent 關係
  - 顯示 parent agent 和 depth

- **Event List 視圖**：列表形式查看所有事件
  - 快速瀏覽所有事件
  - 顯示關鍵信息摘要

- **互動功能**：
  - 點擊事件查看完整詳情
  - Modal 顯示所有欄位
  - 統計資訊面板

**範例**：

```bash
# 可視化委派追蹤
python -m fractal.observability visualize examples/traces/delegation_tracing.jsonl

# 在瀏覽器打開生成的 HTML 文件
```

### 2. 終端 ASCII 可視化

直接在終端查看追蹤，適合快速檢查或無 GUI 環境。

**使用方法**：

```bash
# 完整視圖（摘要 + 層次 + 流程圖 + 時間軸）
python -m fractal.observability view trace.jsonl

# 精簡時間軸
python -m fractal.observability view trace.jsonl --compact

# 只顯示摘要
python -m fractal.observability view trace.jsonl --summary

# 只顯示層次結構
python -m fractal.observability view trace.jsonl --hierarchy

# 只顯示流程圖
python -m fractal.observability view trace.jsonl --flow
```

**視圖類型**：

#### Summary（摘要）

```
================================================================================
TRACE SUMMARY
================================================================================
Total Events:    14
Agents:          3
Tool Calls:      2
Delegations:     2
Errors:          0
Duration:        5.875s

Agents: Coordinator, SpecialistB, SpecialistC
================================================================================
```

#### Hierarchy（層次結構）

```
================================================================================
DELEGATION HIERARCHY
================================================================================
|- Coordinator (depth: 0)
  |- SpecialistB (parent: Coordinator, depth: 1)
    |- SpecialistC (parent: SpecialistB, depth: 2)
================================================================================
```

#### Flow Chart（流程圖）

```
================================================================================
EXECUTION FLOW
================================================================================
+-- START: Coordinator
+--> DELEGATE TO: SpecialistB
  +-- START: SpecialistB
  +--> DELEGATE TO: SpecialistC
    +-- START: SpecialistC
    +-- END: SpecialistC (1.501s)
  +<-- RETURN
  +-- END: SpecialistB (3.897s)
+<-- RETURN
+-- END: Coordinator (5.875s)
================================================================================
```

#### Timeline（時間軸）

```
================================================================================
TRACE TIMELINE
================================================================================
      +0.0us [>] Coordinator STARTED
     +1.132s [T] Coordinator calls ask_specialist
     +1.132s [>>] Coordinator -> DataSpecialist
     +1.132s   [>] DataSpecialist STARTED
     +1.740s   [<] DataSpecialist ENDED (took 608.5ms)
     +1.740s [<<] DataSpecialist -> Coordinator
     +1.740s [R] ask_specialist returned (608.5ms)
     +2.767s [<] Coordinator ENDED (took 2.767s)
================================================================================
```

**事件圖示**：

- `[>]` - Agent 開始
- `[<]` - Agent 結束
- `[>>]` - 委派開始
- `[<<]` - 委派結束
- `[T]` - Tool 調用
- `[R]` - Tool 返回
- `[X]` - 錯誤

## 完整範例

### 1. 生成追蹤並可視化

```python
from fractal import BaseAgent

# 啟用追蹤
coordinator = CoordinatorAgent(enable_tracing=True)
specialist = SpecialistAgent()

coordinator.register_delegate(specialist)

# 執行
await coordinator.run("Task")

# 導出追蹤
coordinator.tracing.export_json("my_trace.jsonl")
```

### 2. HTML 可視化

```bash
# 生成互動式 HTML
python -m fractal.observability visualize my_trace.jsonl -o my_trace.html

# 在瀏覽器打開
# Windows: start my_trace.html
# Mac: open my_trace.html
# Linux: xdg-open my_trace.html
```

### 3. 終端查看

```bash
# 快速查看摘要
python -m fractal.observability view my_trace.jsonl -s

# 查看流程圖
python -m fractal.observability view my_trace.jsonl -f

# 完整視圖
python -m fractal.observability view my_trace.jsonl
```

## 使用場景

### 開發調試

```bash
# 快速查看執行流程
python -m fractal.observability view trace.jsonl -f

# 檢查是否有錯誤
python -m fractal.observability view trace.jsonl -s
```

### 性能分析

```bash
# 查看詳細時間資訊
python -m fractal.observability view trace.jsonl --compact

# 或用 HTML 互動式查看
python -m fractal.observability visualize trace.jsonl
```

### 文檔和演示

```bash
# 生成漂亮的 HTML 報告
python -m fractal.observability visualize trace.jsonl -o report.html

# 分享給團隊
```

### CI/CD Pipeline

```bash
# 在 CI 中查看測試執行流程
python -m fractal.observability view test_trace.jsonl -f

# 檢查是否有錯誤
python -m fractal.observability view test_trace.jsonl -s | grep "Errors:"
```

## 工具比較

| 功能 | HTML Visualizer | Terminal Viewer |
|------|----------------|-----------------|
| 互動式 | ✓ | ✗ |
| 點擊查看詳情 | ✓ | ✗ |
| 需要瀏覽器 | ✓ | ✗ |
| 終端直接查看 | ✗ | ✓ |
| 適合 CI/CD | ✗ | ✓ |
| 適合分享 | ✓ | ✗ |
| Zero Dependency | ✓ | ✓ |

**建議**：

- **開發時**：用 terminal viewer 快速查看
- **詳細分析**：用 HTML visualizer 互動式探索
- **分享/演示**：用 HTML visualizer 生成報告
- **CI/CD**：用 terminal viewer 自動化檢查

## 自定義分析

可以用 Python 直接讀取和分析 .jsonl 文件：

```python
import json

# 讀取追蹤
events = []
with open('trace.jsonl', 'r') as f:
    for line in f:
        events.append(json.loads(line))

# 分析最慢的工具調用
tool_events = [e for e in events if e['event_type'] == 'tool_result']
slowest = max(tool_events, key=lambda e: e.get('elapsed_time', 0))

print(f"Slowest tool: {slowest['tool_name']}")
print(f"Time: {slowest['elapsed_time']:.3f}s")

# 分析委派深度
max_depth = max(e['delegation_depth'] for e in events)
print(f"Max delegation depth: {max_depth}")

# 統計每個 agent 的調用次數
from collections import Counter
agent_counts = Counter(e['agent_name'] for e in events if e['event_type'] == 'agent_start')
print("Agent call counts:", dict(agent_counts))
```

## 技術細節

### HTML Visualizer

- **技術棧**：Pure HTML + CSS + JavaScript（無外部依賴）
- **資料嵌入**：將 .jsonl 資料嵌入 HTML 文件
- **渲染方式**：客戶端 JavaScript 渲染
- **文件大小**：小型追蹤 < 100KB，大型追蹤 < 1MB

### Terminal Viewer

- **輸出格式**：Pure ASCII（Windows 相容）
- **顏色支持**：無（使用圖示區分）
- **性能**：處理數千個事件 < 1秒

## 總結

兩個可視化工具都是 **zero dependency**，只需要：

- Python 標準庫
- 瀏覽器（僅 HTML visualizer）

適合在任何環境使用，從本地開發到 CI/CD pipeline！
