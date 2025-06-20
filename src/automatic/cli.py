"""Command line interface for automatic."""

import sys
import argparse
from .scaffold import ScaffoldGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automatic - Runtime OpenAPI to FastAPI framework"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scaffold command
    scaffold_parser = subparsers.add_parser(
        'scaffold', 
        help='Generate implementation scaffold from OpenAPI spec'
    )
    scaffold_parser.add_argument(
        'spec_path',
        help='Path to OpenAPI specification file'
    )
    scaffold_parser.add_argument(
        '-o', '--output',
        help='Output file path (default: implementation.py)',
        default='implementation.py'
    )
    scaffold_parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Overwrite existing file without confirmation'
    )
    
    args = parser.parse_args()
    
    if args.command == 'scaffold':
        generate_scaffold(args.spec_path, args.output, args.force)
    else:
        parser.print_help()


def generate_scaffold(spec_path: str, output_path: str, force: bool = False):
    """Generate implementation scaffold from OpenAPI spec."""
    try:
        generator = ScaffoldGenerator(spec_path)
        generator.generate_scaffold(output_path, force)
        print(f"✅ Scaffold generated: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()