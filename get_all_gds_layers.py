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
import datetime
import os
import re

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


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('gds', nargs='?', default=GDS, help='path to the GDS file')
    parser.add_argument('-c', '--cell', action='append', metavar='CELL[=ALIAS]',
                        help='cell to compare against the top cell; may be repeated')
    parser.add_argument('--layer-filter', default=LAYER_FILTER,
                        help=f'regex for layers to report (default: {LAYER_FILTER!r})')
    args = parser.parse_args()
    if not args.gds:
        parser.error('no GDS given (pass it as an argument or set GDS in the script)')

    if args.cell:
        cell_list = {}
        for item in args.cell:
            name, _, alias = item.partition('=')
            cell_list[name] = alias
    else:
        cell_list = dict(CELL_LIST)
    return args.gds, cell_list, args.layer_filter


def column_name(cell_list, ip):
    return cell_list[ip] or ip


def main():
    gds, cell_list, layer_filter = parse_args()

    # Read full GDS.
    dbId = k2_quake.data_read_file(gds)
    all_layers = k2_quake.data_get_db_layers(dbId)
    top_layers = [layer for layer in all_layers if re.match(layer_filter, layer)]

    top_cell = k2_quake.data_get_db_cell_name(dbId)
    cellExtents = k2_quake.data_get_db_cell_extent(dbId)
    scaleFactor = k2_quake.data_get_db_scale_factor(dbId)
    dbUnits = k2_quake.data_get_db_units(dbId)
    cells = k2_quake.data_get_db_cell_names(dbId)

    # Extract each requested cell to a temporary GDS and read its layers.
    ip_layers_info = {}
    try:
        for ip in cell_list:
            print(f'START {ip} GDS extraction')
            k2_quake.data_db_extract(dbId, ip + '.gds', ip)
            print(f'FINISH {ip} GDS extraction')
            db = k2_quake.data_read_file(ip + '.gds')
            ip_layers_info[ip] = k2_quake.data_get_db_layers(db)
    finally:
        # Clean up work dir.
        for ip in cell_list:
            if os.path.exists(ip + '.gds'):
                os.remove(ip + '.gds')

    with open(top_cell + '_GDS_cells', 'w') as report_cells:
        for cell in cells:
            report_cells.write(cell + '\n')

    names = f"{top_cell:^{len(top_cell)+6}}|"
    dash_line = '-' * (len(top_cell) + 6)
    for ip in cell_list:
        col = column_name(cell_list, ip)
        names = names + f"{col:^{len(col)+2}}|"
        dash_line = dash_line + '-' + '-' * (len(col) + 2)

    with open(top_cell + '_GDS_info', 'w') as report:
        report.write('GDS: ' + gds + '\n')
        report.write('Generated at ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n' * 2)

        report.write('Top cell:    ' + top_cell + '\n')
        report.write('All layers:  ' + str(len(top_layers)) + '\n')
        report.write('Top size:    ' + str(cellExtents) + '\n')
        report.write('Scale factor: ' + str(scaleFactor) + '\n')
        report.write('dbUnits:     ' + str(dbUnits) + '\n')
        report.write('All cells:   ' + './' + top_cell + '_GDS_cells' + '\n')

        report.write('\n' + dash_line + '\n' + '\n')
        report.write(names + '\n' + dash_line + '\n')

        for layer in top_layers:
            layer_info = f"{layer:^{len(top_cell)+6}}|"
            for ip in cell_list:
                col = column_name(cell_list, ip)
                mark = '+' if layer in ip_layers_info[ip] else '-'
                layer_info = layer_info + f"{mark:^{len(col)+2}}|"
            report.write(layer_info + '\n' + dash_line + '\n')


if __name__ == '__main__':
    main()
