"""
Command-line entry point for observability tools.

Usage:
    fractal view trace.jsonl
    fractal visualize trace.jsonl -o output.html
"""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='Agent execution trace observability tools',
        usage='fractal {visualize,view} [options]'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Visualize command (HTML)
    visualize_parser = subparsers.add_parser(
        'visualize',
        help='Generate interactive HTML visualization'
    )
    visualize_parser.add_argument('input', help='Input trace file (.jsonl)')
    visualize_parser.add_argument(
        '-o', '--output',
        default='trace_visualization.html',
        help='Output HTML file'
    )

    # View command (Terminal)
    view_parser = subparsers.add_parser(
        'view',
        help='View trace in terminal (ASCII)'
    )
    view_parser.add_argument('input', help='Input trace file (.jsonl)')
    view_parser.add_argument('-c', '--compact', action='store_true', help='Compact timeline')
    view_parser.add_argument('-H', '--hierarchy', action='store_true', help='Hierarchy view only')
    view_parser.add_argument('-f', '--flow', action='store_true', help='Flow chart only')
    view_parser.add_argument('-s', '--summary', action='store_true', help='Summary only')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'visualize':
        from .html_visualizer import main as visualize_main
        sys.argv = ['html_visualizer', args.input, '-o', args.output]
        visualize_main()
    elif args.command == 'view':
        from .terminal_viewer import main as view_main
        sys.argv = ['terminal_viewer', args.input]
        if args.compact:
            sys.argv.append('--compact')
        if args.hierarchy:
            sys.argv.append('--hierarchy')
        if args.flow:
            sys.argv.append('--flow')
        if args.summary:
            sys.argv.append('--summary')
        view_main()


if __name__ == '__main__':
    main()
