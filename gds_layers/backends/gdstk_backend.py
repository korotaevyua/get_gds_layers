"""Open-source backend using gdstk (pip install gdstk); no EDA license needed.

Layers are reported as "layer.datatype" (text layers as "layer.texttype").
"""
import re

from ..report import check_cells

NAME = 'gdstk'
REQUIREMENT = 'pip install gdstk'
LAYER_FILTER = '.*'


def available():
    try:
        import gdstk  # noqa: F401
    except ImportError:
        return False
    return True


def _own_layers(cell):
    """Layers drawn directly in `cell`, ignoring references."""
    layers = {(p.layer, p.datatype) for p in cell.polygons}
    for path in cell.paths:
        layers.update(zip(path.layers, path.datatypes))
    layers.update((label.layer, label.texttype) for label in cell.labels)
    return layers


def _layer_name(layer):
    return '%d.%d' % layer


def collect_info(gds, cell_list, layer_filter, workdir='.'):
    import gdstk

    lib = gdstk.read_gds(gds)
    by_name = {cell.name: cell for cell in lib.cells}
    tops = lib.top_level()
    if len(tops) != 1:
        raise ValueError('%s has %d top cells (%s); expected exactly one' %
                         (gds, len(tops), ', '.join(c.name for c in tops)))
    top = tops[0]
    check_cells(by_name, cell_list, gds)

    # Layers of a cell including its whole hierarchy, without flattening it.
    own = {name: _own_layers(cell) for name, cell in by_name.items()}

    def hierarchy_layers(cell):
        layers = set(own[cell.name])
        for dep in cell.dependencies(True):
            if isinstance(dep, gdstk.Cell):  # skip RawCell
                layers |= own[dep.name]
        return layers

    top_layers = [_layer_name(layer) for layer in sorted(hierarchy_layers(top))]
    bbox = top.bounding_box()
    return {
        'top_cell': top.name,
        'top_layers': [layer for layer in top_layers if re.match(layer_filter, layer)],
        'extent': None if bbox is None else tuple(round(v, 6) for xy in bbox for v in xy),
        # Database units per user unit, and the user unit in meters.
        'scale_factor': round(lib.unit / lib.precision),
        'units': lib.unit,
        'cells': list(by_name),
        'ip_layers': {ip: {_layer_name(layer) for layer in hierarchy_layers(by_name[ip])}
                      for ip in cell_list},
    }
