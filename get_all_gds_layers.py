"""Report the layers used by a GDS top cell and, optionally, by selected sub-cells.

Run inside a PVS environment, where the ``k2_quake`` module is provided:

    k2_quake python get_all_gds_layers.py <path/to/design.gds> [-c CELL[=ALIAS] ...]

Writes two files into the current directory:
    <top_cell>_GDS_info   - summary and layer/cell presence matrix
    <top_cell>_GDS_cells  - list of all cell names in the GDS

Extraction may take time for large GDS cells.
Reconstructed from photographs; verify cell names against your GDS.
"""
import argparse
import builtins
import datetime
import os
import re
import sys
import tempfile

# Defaults used when no command-line arguments are given.
# GDS: path to the GDS file.
# CELL_LIST: actual cell name -> short name used as the report column header
# ('' keeps the actual name). Leave empty to report the top cell only.
GDS = ""
CELL_LIST = {
    # 'cell name': 'optional short name',
}
# Only layers whose name matches this regex are reported.
LAYER_FILTER = '.*lay.*'


def parse_cell_args(items):
    """Turn ['A', 'B=b'] into {'A': '', 'B': 'b'}."""
    cell_list = {}
    for item in items:
        name, _, alias = item.partition('=')
        cell_list[name] = alias
    return cell_list


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('gds', nargs='?', default=GDS, help='path to the GDS file')
    parser.add_argument('-c', '--cell', action='append', metavar='CELL[=ALIAS]',
                        help='cell to compare against the top cell; may be repeated')
    parser.add_argument('--layer-filter', default=LAYER_FILTER,
                        help='regex for layers to report (default: %(default)r)')
    args = parser.parse_args(argv)
    if not args.gds:
        parser.error('no GDS given (pass it as an argument or set GDS in the script)')
    try:
        re.compile(args.layer_filter)
    except re.error as e:
        parser.error('invalid --layer-filter: %s' % e)

    cell_list = parse_cell_args(args.cell) if args.cell else dict(CELL_LIST)
    return args.gds, cell_list, args.layer_filter


def get_k2_quake():
    """Return the k2_quake API, which `k2_quake python` provides as a global."""
    k2 = globals().get('k2_quake') or getattr(builtins, 'k2_quake', None)
    if k2 is not None:
        return k2
    try:
        import k2_quake
    except ImportError:
        sys.exit('k2_quake is not available: source a PVS setup and run\n'
                 '    k2_quake python get_all_gds_layers.py ...')
    return k2_quake


def column_name(cell_list, ip):
    return cell_list[ip] or ip


def collect_info(k2, gds, cell_list, layer_filter, workdir='.'):
    """Read the GDS and return everything the report needs."""
    dbId = k2.data_read_file(gds)
    all_layers = k2.data_get_db_layers(dbId)
    cells = k2.data_get_db_cell_names(dbId)

    # Fail before the (slow) extraction rather than halfway through it.
    missing = [ip for ip in cell_list if ip not in cells]
    if missing:
        raise ValueError('cells not found in %s: %s' % (gds, ', '.join(missing)))

    info = {
        'top_cell': k2.data_get_db_cell_name(dbId),
        'top_layers': [layer for layer in all_layers if re.match(layer_filter, layer)],
        'extent': k2.data_get_db_cell_extent(dbId),
        'scale_factor': k2.data_get_db_scale_factor(dbId),
        'units': k2.data_get_db_units(dbId),
        'cells': cells,
        'ip_layers': {},
    }

    # Extract each requested cell to its own GDS in a private temporary
    # directory, so that existing files in the work dir are never touched.
    with tempfile.TemporaryDirectory(prefix='.gds_layers_', dir=workdir) as tmp:
        for i, ip in enumerate(cell_list):
            path = os.path.join(tmp, 'cell%d.gds' % i)
            print(f'START {ip} GDS extraction')
            k2.data_db_extract(dbId, path, ip)
            print(f'FINISH {ip} GDS extraction')
            info['ip_layers'][ip] = k2.data_get_db_layers(k2.data_read_file(path))
    return info


def format_report(info, gds, cell_list, now):
    top_cell = info['top_cell']
    lines = [
        'GDS: ' + gds,
        'Generated at ' + now.strftime('%Y-%m-%d %H:%M:%S'),
        '',
        'Top cell:    ' + top_cell,
        'All layers:  ' + str(len(info['top_layers'])),
        'Top size:    ' + str(info['extent']),
        'Scale factor: ' + str(info['scale_factor']),
        'dbUnits:     ' + str(info['units']),
        'All cells:   ' + './' + top_cell + '_GDS_cells',
    ]

    names = f"{top_cell:^{len(top_cell)+6}}|"
    dash_line = '-' * (len(top_cell) + 6)
    for ip in cell_list:
        col = column_name(cell_list, ip)
        names += f"{col:^{len(col)+2}}|"
        dash_line += '-' + '-' * (len(col) + 2)

    lines += ['', dash_line, '', names, dash_line]
    for layer in info['top_layers']:
        row = f"{layer:^{len(top_cell)+6}}|"
        for ip in cell_list:
            col = column_name(cell_list, ip)
            mark = '+' if layer in info['ip_layers'][ip] else '-'
            row += f"{mark:^{len(col)+2}}|"
        lines += [row, dash_line]
    return '\n'.join(lines) + '\n'


def write_reports(info, gds, cell_list, outdir='.', now=None):
    now = now or datetime.datetime.now()
    top_cell = info['top_cell']
    with open(os.path.join(outdir, top_cell + '_GDS_cells'), 'w') as f:
        f.write(''.join(cell + '\n' for cell in info['cells']))
    with open(os.path.join(outdir, top_cell + '_GDS_info'), 'w') as f:
        f.write(format_report(info, gds, cell_list, now))


def main(argv=None):
    gds, cell_list, layer_filter = parse_args(argv)
    k2 = get_k2_quake()
    try:
        info = collect_info(k2, gds, cell_list, layer_filter)
    except ValueError as e:
        sys.exit('error: %s' % e)
    write_reports(info, gds, cell_list)


if __name__ == '__main__':
    main()
