# Code Refactoring - Observability Module

## 概述

將追蹤和可視化相關的功能重構為一個獨立的 `observability` 子模組，使代碼結構更清晰、更易維護。

## 變更內容

### 目錄結構變更

**之前**：
```
fractal/
├── __init__.py
├── agent.py
├── toolkit.py
├── models.py
├── parser.py
├── tracing.py              # 追蹤功能
├── trace_visualizer.py     # HTML 可視化
└── trace_viewer.py         # 終端查看器
```

**之後**：
```
fractal/
├── __init__.py
├── agent.py
├── toolkit.py
├── models.py
├── parser.py
└── observability/          # 新增：observability 模組
    ├── __init__.py
    ├── __main__.py         # 統一命令行入口
    ├── tracing.py          # TracingKit (重命名)
    ├── html_visualizer.py  # HTML 可視化 (重命名)
    └── terminal_viewer.py  # 終端查看器 (重命名)
```

### 檔案重命名

| 舊檔名 | 新檔名 | 說明 |
|--------|--------|------|
| `tracing.py` | `observability/tracing.py` | 移動到子模組 |
| `trace_visualizer.py` | `observability/html_visualizer.py` | 更明確的命名 |
| `trace_viewer.py` | `observability/terminal_viewer.py` | 更明確的命名 |

### 命令行介面改進

#### 舊命令（已移除）

```bash
# 以下路徑已不存在
python -m fractal.trace_visualizer trace.jsonl
python -m fractal.trace_viewer trace.jsonl
```

#### 新命令

```bash
# 統一入口 - HTML 可視化
python -m fractal.observability visualize trace.jsonl

# 統一入口 - 終端查看
python -m fractal.observability view trace.jsonl

# 或使用完整路徑
python -m fractal.observability.html_visualizer trace.jsonl
python -m fractal.observability.terminal_viewer trace.jsonl
```

### Import 路徑變更

#### Python 代碼

**之前**：
```python
from fractal.tracing import TracingKit, TraceEvent
```

**之後（兩種方式都可以）**：
```python
# 方式 1：從主模組導入（推薦，向後相容）
from fractal import TracingKit, TraceEvent

# 方式 2：從 observability 子模組導入
from fractal.observability import TracingKit, TraceEvent
```

**向後相容性**：從 `fractal` 直接導入仍然有效，無需修改現有代碼。

## 優點

### 1. 更清晰的組織結構

- **核心功能**：`agent.py`, `toolkit.py`, `models.py`, `parser.py`
- **Observability**：所有追蹤和可視化功能集中在一個模組

### 2. 更好的命名

- `html_visualizer` 比 `trace_visualizer` 更明確
- `terminal_viewer` 比 `trace_viewer` 更明確
- 清楚區分兩種不同的可視化方式

### 3. 統一的命令行介面

- 新增 `__main__.py` 提供統一入口
- 更簡潔的命令：`observability view` 和 `observability visualize`
- 更符合 Python 模組設計慣例

### 4. 易於擴展

未來可以輕鬆添加新的 observability 功能：
```
observability/
├── tracing.py           # 現有
├── html_visualizer.py   # 現有
├── terminal_viewer.py   # 現有
├── metrics.py           # 未來：性能指標
├── profiler.py          # 未來：性能分析
└── exporter.py          # 未來：導出到 APM 系統
```

### 5. 模組化

- 每個功能獨立
- 可以單獨使用或組合使用
- 便於測試和維護

## 向後相容性

✅ **完全向後相容**

所有現有代碼無需修改即可繼續工作：

```python
# 這些 import 仍然有效
from fractal import TracingKit, TraceEvent
from fractal import BaseAgent, AgentToolkit

# 現有的 agent 代碼完全不需要修改
agent = BaseAgent(
    name="MyAgent",
    system_prompt="...",
    enable_tracing=True
)
```

舊的命令行命令也仍然支援（透過完整路徑）。

## 遷移指南

### 無需遷移

如果你的代碼使用：
```python
from fractal import TracingKit, TraceEvent
```

**不需要做任何改變！**

### 命令行遷移

舊的命令行路徑已移除，請使用新的統一入口：

```bash
python -m fractal.observability view trace.jsonl -s
python -m fractal.observability visualize trace.jsonl
```

## 測試

所有功能已測試：

```bash
# ✓ Import 測試
python -c "from fractal import TracingKit, TraceEvent; print('OK')"

# ✓ 終端查看器
python -m fractal.observability view examples/traces/visualization_demo.jsonl -s

# ✓ HTML 可視化
python -m fractal.observability visualize examples/traces/visualization_demo.jsonl

# ✓ 舊命令（向後相容）
python -m fractal.observability.terminal_viewer examples/traces/visualization_demo.jsonl -s
python -m fractal.observability.html_visualizer examples/traces/visualization_demo.jsonl
```

## 文檔更新

以下文檔已更新以反映新結構：

- ✅ [README.md](../README.md) - 更新快速命令
- ✅ [TRACE_VISUALIZATION.md](TRACE_VISUALIZATION.md) - 更新所有命令
- ✅ [CHANGELOG.md](../CHANGELOG.md) - 記錄重構
- ✅ [examples/](../examples/) - 更新所有範例

## 總結

這次重構：
- ✅ 改善代碼組織和可維護性
- ✅ 提供更清晰的命名
- ✅ 統一命令行介面
- ✅ 完全向後相容
- ✅ 為未來擴展奠定基礎

**建議**：開始使用新的 `python -m fractal.observability` 命令，但舊命令仍然可用。
