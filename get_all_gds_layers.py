"""Report the layers used by a GDS top cell and, optionally, by selected sub-cells.

Works with whichever layout tool is available (see --tool):

    k2_quake python get_all_gds_layers.py design.gds [-c CELL[=ALIAS] ...]   # PVS
    python get_all_gds_layers.py design.gds --tool calibre [-c ...]           # Calibre
    python get_all_gds_layers.py design.gds --tool gdstk [-c ...]             # open source

Writes two files into the current directory:
    <top_cell>_GDS_info   - summary and layer/cell presence matrix
    <top_cell>_GDS_cells  - list of all cell names in the GDS

Extraction may take time for large GDS cells.
Reconstructed from photographs; verify cell names against your GDS.
"""
import argparse
import re
import sys

from gds_layers.backends import BY_NAME, get_backend
from gds_layers.report import parse_cell_args, write_reports

# Defaults used when no command-line arguments are given.
# GDS: path to the GDS file.
# CELL_LIST: actual cell name -> short name used as the report column header
# ('' keeps the actual name). Leave empty to report the top cell only.
GDS = ""
CELL_LIST = {
    # 'cell name': 'optional short name',
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('gds', nargs='?', default=GDS, help='path to the GDS file')
    parser.add_argument('-c', '--cell', action='append', metavar='CELL[=ALIAS]',
                        help='cell to compare against the top cell; may be repeated')
    parser.add_argument('-t', '--tool', choices=['auto'] + list(BY_NAME), default='auto',
                        help='layout tool to read the GDS with (default: first available, '
                             'in order %s)' % ', '.join(BY_NAME))
    parser.add_argument('--layer-filter',
                        help='regex for layers to report (default depends on the tool: %s)' %
                             ', '.join('%s %r' % (n, b.LAYER_FILTER) for n, b in BY_NAME.items()))
    args = parser.parse_args(argv)
    if not args.gds:
        parser.error('no GDS given (pass it as an argument or set GDS in the script)')
    if args.layer_filter is not None:
        try:
            re.compile(args.layer_filter)
        except re.error as e:
            parser.error('invalid --layer-filter: %s' % e)
    args.cell_list = parse_cell_args(args.cell) if args.cell else dict(CELL_LIST)
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        backend = get_backend(args.tool)
        layer_filter = args.layer_filter or backend.LAYER_FILTER
        info = backend.collect_info(args.gds, args.cell_list, layer_filter)
    except (RuntimeError, ValueError) as e:
        sys.exit('error: %s' % e)
    write_reports(info, args.gds, args.cell_list)


if __name__ == '__main__':
    main()
