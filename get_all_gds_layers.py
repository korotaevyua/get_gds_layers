import re, datetime, os

# Script to create report file <top_cell>_GDS_info with all layers for
# top-level cell and any other cell and some other information.
# Usage:
# Set path to gds.
# Set cell_list: actual cell name -> simplified name for convenience.
# If no specific cell is needed, comment out cell_list.
# Source a PVS setup, then run:
# k2_quake python get_all_gds_layers.py
# Extraction may take time for large GDS cells.
# Reconstructed from photographs; verify cell names against your GDS.

gds = ""

cell_list = {
    'cell name': 'optional short name',
}

# Read full GDS.
dbId = k2_quake.data_read_file(gds)
all_layers = k2_quake.data_get_db_layers(dbId)

top_layers = []
for layer in all_layers:
    if re.match('.*lay.*', layer):
        top_layers.append(layer)

# Get top name.
top_cell = k2_quake.data_get_db_cell_name(dbId)

# Size.
cellExtents = k2_quake.data_get_db_cell_extent(dbId)

# Scale factor.
scaleFactor = k2_quake.data_get_db_scale_factor(dbId)

# Units.
dbUnits = k2_quake.data_get_db_units(dbId)

# Cell names.
cells = k2_quake.data_get_db_cell_names(dbId)

if 'cell_list' in locals():
    # Extract cell GDS.
    for ip in cell_list:
        print(f'START {ip} GDS extraction')
        k2_quake.data_db_extract(dbId, ip + '.gds', ip)
        print(f'FINISH {ip} GDS extraction')

    # Get layers info for each cell.
    ip_layers_info = {}
    for ip in cell_list:
        db = k2_quake.data_read_file(ip + '.gds')
        layers = k2_quake.data_get_db_layers(db)
        ip_layers_info[ip] = layers

# Report to file.
report = open(top_cell + '_GDS_info', 'w')
report_cells = open(top_cell + '_GDS_cells', 'w')

for cell in cells:
    report_cells.write(cell + '\n')

report.write('GDS: ' + gds + '\n')
report.write('Generated at ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n' * 2)

report.write('Top cell:    ' + top_cell + '\n')
report.write('All layers:  ' + str(len(top_layers)) + '\n')
report.write('Top size:    ' + str(cellExtents) + '\n')
report.write('Scale factor: ' + str(scaleFactor) + '\n')
report.write('dbUnits:     ' + str(dbUnits) + '\n')
report.write('All cells:   ' + str('./' + top_cell + '_GDS_cells') + '\n')

names = f"{top_cell:^{len(top_cell)+6}}|"
dash_line = '-' * (len(top_cell) + 6)

if 'cell_list' in locals():
    for ip in cell_list:
        if cell_list[ip] != '':
            ip = cell_list[ip]
        names = names + f"{ip:^{len(ip)+2}}|"

    for ip in cell_list:
        ip_coll = ip
        if cell_list[ip] != '':
            ip_coll = cell_list[ip]
        dash_line = dash_line + '-' + '-' * (len(ip_coll) + 2)

    report.write('\n' + dash_line + '\n' + '\n')
    report.write(names + '\n' + dash_line + '\n')

    for layer in top_layers:
        layer_info = f"{layer:^{len(top_cell)+6}}|"
        for ip in ip_layers_info:
            ip_coll = ip
            if cell_list[ip] != '':
                ip_coll = cell_list[ip]
            plus = '+'
            minus = '-'
            if layer in ip_layers_info[ip]:
                layer_info = layer_info + f"{plus:^{len(ip_coll)+2}}|"
            else:
                layer_info = layer_info + f"{minus:^{len(ip_coll)+2}}|"
        report.write(layer_info + '\n' + dash_line + '\n')

    # Clean up work dir.
    for ip in cell_list:
        os.remove(ip + '.gds')
else:
    report.write('\n' + dash_line + '\n' + '\n')
    report.write(names + '\n' + dash_line + '\n')

    for layer in top_layers:
        layer_info = f"{layer:^{len(top_cell)+6}}|"
        report.write(layer_info + '\n' + dash_line + '\n')