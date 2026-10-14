"""Layout tools that can read a GDS.

Each backend module provides:
    NAME            name used with --tool
    LAYER_FILTER    default --layer-filter for the layer names it reports
    available()     True if the tool can be used here
    collect_info(gds, cell_list, layer_filter, workdir) -> info dict (see gds_layers.report)
"""
from . import calibre, gdstk_backend, pvs

# Order of preference for --tool auto.
BACKENDS = [pvs, calibre, gdstk_backend]
BY_NAME = {b.NAME: b for b in BACKENDS}


def get_backend(name='auto'):
    if name != 'auto':
        backend = BY_NAME[name]
        if not backend.available():
            raise RuntimeError('%s is not available here: %s' % (name, backend.REQUIREMENT))
        return backend
    for backend in BACKENDS:
        if backend.available():
            return backend
    raise RuntimeError('no layout tool found; need one of:\n' +
                       '\n'.join('  %-8s %s' % (b.NAME, b.REQUIREMENT) for b in BACKENDS))
