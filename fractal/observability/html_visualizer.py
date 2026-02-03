"""
Trace Visualizer - Zero Dependency

Generates an interactive HTML visualization from agent trace files (.jsonl).

Features:
- Timeline view showing agent execution flow
- Delegation hierarchy visualization
- Event details on hover/click
- Color-coded event types
- Zero external dependencies (only Python stdlib + browser)

Usage:
    python -m fractal.observability visualize trace.jsonl
    python -m fractal.observability visualize trace.jsonl -o output.html
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse


def load_trace(filepath: str) -> List[Dict[str, Any]]:
    """Load trace events from .jsonl file."""
    events = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def generate_html(events: List[Dict[str, Any]], output_path: str):
    """Generate interactive HTML visualization."""

    # Convert events to JSON for embedding
    events_json = json.dumps(events, ensure_ascii=False, indent=2)

    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Agent Trace Visualization</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .header {{
            padding: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}

        h1 {{
            font-size: 24px;
            color: #333;
            margin-bottom: 10px;
        }}

        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }}

        .stat {{
            padding: 8px 16px;
            background: #f0f0f0;
            border-radius: 4px;
            font-size: 14px;
        }}

        .stat-label {{
            color: #666;
            font-weight: 500;
        }}

        .stat-value {{
            color: #333;
            font-weight: bold;
            margin-left: 5px;
        }}

        .tabs {{
            display: flex;
            border-bottom: 1px solid #e0e0e0;
            padding: 0 20px;
        }}

        .tab {{
            padding: 12px 20px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            color: #666;
            font-weight: 500;
            transition: all 0.2s;
        }}

        .tab:hover {{
            color: #333;
        }}

        .tab.active {{
            color: #2196F3;
            border-bottom-color: #2196F3;
        }}

        .content {{
            padding: 20px;
        }}

        .view {{
            display: none;
        }}

        .view.active {{
            display: block;
        }}

        /* Timeline View */
        .timeline {{
            position: relative;
            padding: 20px 0;
        }}

        .timeline-event {{
            margin-bottom: 10px;
            padding: 12px;
            border-left: 4px solid #ddd;
            background: #fafafa;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .timeline-event:hover {{
            background: #f0f0f0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .timeline-event.depth-0 {{ margin-left: 0; }}
        .timeline-event.depth-1 {{ margin-left: 40px; }}
        .timeline-event.depth-2 {{ margin-left: 80px; }}
        .timeline-event.depth-3 {{ margin-left: 120px; }}

        .event-type-agent_start {{ border-left-color: #4CAF50; }}
        .event-type-agent_end {{ border-left-color: #8BC34A; }}
        .event-type-agent_delegate {{ border-left-color: #FF9800; }}
        .event-type-delegation_end {{ border-left-color: #FFC107; }}
        .event-type-tool_call {{ border-left-color: #2196F3; }}
        .event-type-tool_result {{ border-left-color: #03A9F4; }}
        .event-type-error {{ border-left-color: #F44336; }}

        .event-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }}

        .event-type {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .type-agent_start {{ background: #4CAF50; color: white; }}
        .type-agent_end {{ background: #8BC34A; color: white; }}
        .type-agent_delegate {{ background: #FF9800; color: white; }}
        .type-delegation_end {{ background: #FFC107; color: #333; }}
        .type-tool_call {{ background: #2196F3; color: white; }}
        .type-tool_result {{ background: #03A9F4; color: white; }}
        .type-error {{ background: #F44336; color: white; }}

        .event-time {{
            color: #999;
            font-size: 12px;
        }}

        .event-body {{
            color: #333;
            font-size: 14px;
        }}

        .event-agent {{
            font-weight: 600;
            color: #333;
        }}

        .event-detail {{
            color: #666;
            font-size: 13px;
            margin-top: 4px;
        }}

        /* Hierarchy View */
        .hierarchy {{
            padding: 20px;
        }}

        .hierarchy-node {{
            margin-bottom: 10px;
        }}

        .hierarchy-node.depth-0 {{ margin-left: 0; }}
        .hierarchy-node.depth-1 {{ margin-left: 40px; }}
        .hierarchy-node.depth-2 {{ margin-left: 80px; }}
        .hierarchy-node.depth-3 {{ margin-left: 120px; }}

        .node-content {{
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            background: #f0f0f0;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}

        .node-icon {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4CAF50;
            margin-right: 8px;
        }}

        .node-parent {{
            color: #999;
            font-size: 12px;
            margin-left: 8px;
        }}

        /* Event List View */
        .event-list {{
            padding: 10px;
        }}

        .event-item {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .event-item:hover {{
            background: #f9f9f9;
        }}

        .event-item:last-child {{
            border-bottom: none;
        }}

        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }}

        .modal.active {{
            display: flex;
        }}

        .modal-content {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}

        .modal-title {{
            font-size: 18px;
            font-weight: 600;
        }}

        .modal-close {{
            cursor: pointer;
            font-size: 24px;
            color: #999;
            line-height: 1;
        }}

        .modal-close:hover {{
            color: #333;
        }}

        .detail-row {{
            margin-bottom: 10px;
        }}

        .detail-label {{
            font-weight: 600;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        .detail-value {{
            color: #333;
            font-size: 14px;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
            word-break: break-word;
        }}

        .detail-value pre {{
            margin: 0;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agent Trace Visualization</h1>
            <div class="stats">
                <div class="stat">
                    <span class="stat-label">Total Events:</span>
                    <span class="stat-value" id="stat-events">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Agents:</span>
                    <span class="stat-value" id="stat-agents">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Tool Calls:</span>
                    <span class="stat-value" id="stat-tools">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Delegations:</span>
                    <span class="stat-value" id="stat-delegations">0</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Duration:</span>
                    <span class="stat-value" id="stat-duration">0s</span>
                </div>
            </div>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('timeline')">Timeline</div>
            <div class="tab" onclick="switchTab('hierarchy')">Hierarchy</div>
            <div class="tab" onclick="switchTab('events')">Event List</div>
        </div>

        <div class="content">
            <div id="view-timeline" class="view active">
                <div class="timeline" id="timeline"></div>
            </div>

            <div id="view-hierarchy" class="view">
                <div class="hierarchy" id="hierarchy"></div>
            </div>

            <div id="view-events" class="view">
                <div class="event-list" id="event-list"></div>
            </div>
        </div>
    </div>

    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title" id="modal-title">Event Details</div>
                <div class="modal-close" onclick="closeModal()">&times;</div>
            </div>
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        // Embedded trace data
        const TRACE_EVENTS = {events_json};

        // State
        let currentTab = 'timeline';

        // Initialize
        function init() {{
            renderStats();
            renderTimeline();
            renderHierarchy();
            renderEventList();
        }}

        // Render statistics
        function renderStats() {{
            const agents = new Set();
            let toolCalls = 0;
            let delegations = 0;

            TRACE_EVENTS.forEach(event => {{
                agents.add(event.agent_name);
                if (event.event_type === 'tool_call') toolCalls++;
                if (event.event_type === 'agent_delegate') delegations++;
            }});

            const duration = TRACE_EVENTS.length > 0
                ? (TRACE_EVENTS[TRACE_EVENTS.length - 1].timestamp - TRACE_EVENTS[0].timestamp).toFixed(2)
                : 0;

            document.getElementById('stat-events').textContent = TRACE_EVENTS.length;
            document.getElementById('stat-agents').textContent = agents.size;
            document.getElementById('stat-tools').textContent = toolCalls;
            document.getElementById('stat-delegations').textContent = delegations;
            document.getElementById('stat-duration').textContent = duration + 's';
        }}

        // Render timeline view
        function renderTimeline() {{
            const container = document.getElementById('timeline');
            container.innerHTML = '';

            TRACE_EVENTS.forEach((event, index) => {{
                const div = document.createElement('div');
                div.className = `timeline-event depth-${{event.delegation_depth}} event-type-${{event.event_type}}`;
                div.onclick = () => showEventDetails(event);

                const relTime = index > 0
                    ? `+${{(event.timestamp - TRACE_EVENTS[0].timestamp).toFixed(3)}}s`
                    : '0.000s';

                let bodyText = '';
                if (event.event_type === 'agent_start') {{
                    bodyText = `<span class="event-agent">${{event.agent_name}}</span> started`;
                }} else if (event.event_type === 'agent_end') {{
                    bodyText = `<span class="event-agent">${{event.agent_name}}</span> ended`;
                    if (event.elapsed_time) {{
                        bodyText += ` (took ${{event.elapsed_time.toFixed(3)}}s)`;
                    }}
                }} else if (event.event_type === 'agent_delegate') {{
                    const toAgent = event.arguments?.to_agent || 'unknown';
                    bodyText = `<span class="event-agent">${{event.agent_name}}</span> -> ${{toAgent}}`;
                }} else if (event.event_type === 'delegation_end') {{
                    const toAgent = event.metadata?.to_agent || 'unknown';
                    bodyText = `${{toAgent}} -> <span class="event-agent">${{event.agent_name}}</span>`;
                }} else if (event.event_type === 'tool_call') {{
                    bodyText = `<span class="event-agent">${{event.agent_name}}</span> calls <strong>${{event.tool_name}}</strong>`;
                }} else if (event.event_type === 'tool_result') {{
                    bodyText = `<strong>${{event.tool_name}}</strong> returned`;
                    if (event.elapsed_time) {{
                        bodyText += ` (${{event.elapsed_time.toFixed(3)}}s)`;
                    }}
                    if (event.error) {{
                        bodyText += ` <span style="color: #F44336">ERROR</span>`;
                    }}
                }} else if (event.event_type === 'error') {{
                    bodyText = `<span class="event-agent">${{event.agent_name}}</span> <span style="color: #F44336">ERROR</span>`;
                }}

                div.innerHTML = `
                    <div class="event-header">
                        <span class="event-type type-${{event.event_type}}">${{event.event_type.replace('_', ' ')}}</span>
                        <span class="event-time">${{relTime}}</span>
                    </div>
                    <div class="event-body">${{bodyText}}</div>
                `;

                container.appendChild(div);
            }});
        }}

        // Render hierarchy view
        function renderHierarchy() {{
            const container = document.getElementById('hierarchy');
            container.innerHTML = '';

            // Get unique agent starts
            const agentStarts = TRACE_EVENTS.filter(e => e.event_type === 'agent_start');

            agentStarts.forEach(event => {{
                const div = document.createElement('div');
                div.className = `hierarchy-node depth-${{event.delegation_depth}}`;

                const parentText = event.parent_agent
                    ? `<span class="node-parent">&larr; ${{event.parent_agent}}</span>`
                    : '';

                div.innerHTML = `
                    <div class="node-content">
                        <div class="node-icon"></div>
                        ${{event.agent_name}}
                        ${{parentText}}
                    </div>
                `;

                container.appendChild(div);
            }});
        }}

        // Render event list view
        function renderEventList() {{
            const container = document.getElementById('event-list');
            container.innerHTML = '';

            TRACE_EVENTS.forEach((event, index) => {{
                const div = document.createElement('div');
                div.className = 'event-item';
                div.onclick = () => showEventDetails(event);

                const relTime = index > 0
                    ? `+${{(event.timestamp - TRACE_EVENTS[0].timestamp).toFixed(3)}}s`
                    : '0.000s';

                div.innerHTML = `
                    <div class="event-header">
                        <span class="event-type type-${{event.event_type}}">${{event.event_type}}</span>
                        <span class="event-time">${{relTime}}</span>
                    </div>
                    <div class="event-detail">
                        Agent: ${{event.agent_name}} | Depth: ${{event.delegation_depth}}
                        ${{event.tool_name ? `| Tool: ${{event.tool_name}}` : ''}}
                        ${{event.parent_agent ? `| Parent: ${{event.parent_agent}}` : ''}}
                    </div>
                `;

                container.appendChild(div);
            }});
        }}

        // Show event details in modal
        function showEventDetails(event) {{
            const modal = document.getElementById('modal');
            const title = document.getElementById('modal-title');
            const body = document.getElementById('modal-body');

            title.textContent = `${{event.event_type}} - ${{event.agent_name}}`;

            let html = '';

            // Add all fields
            const fields = [
                {{ label: 'Event Type', value: event.event_type }},
                {{ label: 'Agent Name', value: event.agent_name }},
                {{ label: 'Timestamp', value: new Date(event.timestamp * 1000).toISOString() }},
                {{ label: 'Delegation Depth', value: event.delegation_depth }},
                {{ label: 'Parent Agent', value: event.parent_agent || 'None' }},
                {{ label: 'Tool Name', value: event.tool_name || 'N/A' }},
                {{ label: 'Elapsed Time', value: event.elapsed_time ? `${{event.elapsed_time.toFixed(3)}}s` : 'N/A' }},
                {{ label: 'Error', value: event.error || 'None' }},
            ];

            fields.forEach(field => {{
                html += `
                    <div class="detail-row">
                        <div class="detail-label">${{field.label}}</div>
                        <div class="detail-value">${{field.value}}</div>
                    </div>
                `;
            }});

            // Add arguments if present
            if (event.arguments && Object.keys(event.arguments).length > 0) {{
                html += `
                    <div class="detail-row">
                        <div class="detail-label">Arguments</div>
                        <div class="detail-value"><pre>${{JSON.stringify(event.arguments, null, 2)}}</pre></div>
                    </div>
                `;
            }}

            // Add result if present
            if (event.result) {{
                html += `
                    <div class="detail-row">
                        <div class="detail-label">Result</div>
                        <div class="detail-value">${{event.result}}</div>
                    </div>
                `;
            }}

            // Add metadata if present
            if (event.metadata && Object.keys(event.metadata).length > 0) {{
                html += `
                    <div class="detail-row">
                        <div class="detail-label">Metadata</div>
                        <div class="detail-value"><pre>${{JSON.stringify(event.metadata, null, 2)}}</pre></div>
                    </div>
                `;
            }}

            body.innerHTML = html;
            modal.classList.add('active');
        }}

        // Close modal
        function closeModal() {{
            document.getElementById('modal').classList.remove('active');
        }}

        // Switch tabs
        function switchTab(tabName) {{
            // Update tab buttons
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            event.target.classList.add('active');

            // Update views
            document.querySelectorAll('.view').forEach(view => {{
                view.classList.remove('active');
            }});
            document.getElementById(`view-${{tabName}}`).classList.add('active');

            currentTab = tabName;
        }}

        // Close modal on outside click
        document.getElementById('modal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                closeModal();
            }}
        }});

        // Initialize on load
        init();
    </script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def main():
    parser = argparse.ArgumentParser(
        description='Visualize agent trace files (.jsonl) as interactive HTML'
    )
    parser.add_argument(
        'input',
        help='Input trace file (.jsonl)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output HTML file (default: trace_visualization.html)',
        default='trace_visualization.html'
    )

    args = parser.parse_args()

    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Load trace events
    print(f"Loading trace from: {args.input}")
    events = load_trace(args.input)
    print(f"Loaded {len(events)} events")

    # Generate HTML
    output_path = args.output
    print(f"Generating visualization: {output_path}")
    generate_html(events, output_path)

    print(f"\n[OK] Visualization created!")
    print(f"     Open in browser: {Path(output_path).absolute()}")


if __name__ == '__main__':
    main()
