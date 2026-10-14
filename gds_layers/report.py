"""Backend-independent report formatting.

Every backend returns an `info` dict with these keys:
    top_cell      name of the top cell
    top_layers    layers of the top cell, already filtered, in report order
    extent        top cell extent, printed as-is
    scale_factor  printed as-is
    units         printed as-is
    cells         all cell names in the GDS
    ip_layers     requested cell -> collection of layers used in it
"""
import datetime
import os


def parse_cell_args(items):
    """Turn ['A', 'B=b'] into {'A': '', 'B': 'b'}."""
    cell_list = {}
    for item in items:
        name, _, alias = item.partition('=')
        cell_list[name] = alias
    return cell_list


def column_name(cell_list, ip):
    return cell_list[ip] or ip


def check_cells(cells, cell_list, gds):
    missing = [ip for ip in cell_list if ip not in cells]
    if missing:
        raise ValueError('cells not found in %s: %s' % (gds, ', '.join(missing)))


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
