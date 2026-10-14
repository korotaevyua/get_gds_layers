"""Cadence PVS, through the k2_quake API (run the script with `k2_quake python`)."""
import builtins
import os
import re
import tempfile

from ..report import check_cells

NAME = 'pvs'
REQUIREMENT = 'source a PVS setup and run the script with `k2_quake python ...`'
LAYER_FILTER = '.*lay.*'


def get_k2_quake():
    """Return the k2_quake API, which `k2_quake python` provides as a global, or None."""
    k2 = getattr(builtins, 'k2_quake', None)
    if k2 is not None:
        return k2
    import __main__
    k2 = getattr(__main__, 'k2_quake', None)
    if k2 is not None:
        return k2
    try:
        import k2_quake
    except ImportError:
        return None
    return k2_quake


def available():
    return get_k2_quake() is not None


def collect_info(gds, cell_list, layer_filter, workdir='.', k2=None):
    k2 = k2 or get_k2_quake()
    dbId = k2.data_read_file(gds)
    all_layers = k2.data_get_db_layers(dbId)
    cells = k2.data_get_db_cell_names(dbId)
    # Fail before the (slow) extraction rather than halfway through it.
    check_cells(cells, cell_list, gds)

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
