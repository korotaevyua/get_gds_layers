"""Siemens Calibre, through a DESIGNrev Tcl script run with `calibredrv`.

Layers are reported as "layer.datatype" (the layout is opened with -dt_expand).
Mirrors the PVS flow: each requested cell is written to its own GDS with
`$L gdsout` and re-read to list its layers, so hierarchy is included.

NOTE: not yet run against a real Calibre installation. The Tcl is tested with
a fake `layout` command (tests/fake_calibredrv.tcl); check it on first use.
"""
import os
import re
import shutil
import subprocess
import tempfile

from ..report import check_cells

NAME = 'calibre'
REQUIREMENT = 'calibredrv on PATH (or set CALIBREDRV)'
LAYER_FILTER = '.*'

PREFIX = '@@GDSL'

TCL = r'''
proc out {key args} { puts "@@GDSL\t$key\t[join $args \t]" }
proc try_out {key script} {
    if {[catch {uplevel 1 $script} value]} { set value "?" }
    out $key $value
}

set gds %(gds)s
set extract_cells [list %(cells)s]
set extract_paths [list %(paths)s]

set L [layout create $gds -dt_expand]
set all_cells [$L cells]
set missing 0
foreach cell $extract_cells {
    if {[lsearch -exact $all_cells $cell] < 0} { out missing $cell; incr missing }
}
if {$missing} { exit 0 }

set top [$L topcell]
out top $top
foreach cell $all_cells { out cell $cell }
foreach layer [$L layers] { out layer $layer }
try_out extent { join [$L bbox $top] " " }
try_out scale_factor { $L units user }
try_out units { $L units database }

foreach cell $extract_cells path $extract_paths {
    puts "START $cell GDS extraction"
    $L gdsout $path $cell
    puts "FINISH $cell GDS extraction"
    set C [layout create $path -dt_expand]
    foreach layer [$C layers] { out ip_layer $cell $layer }
    catch { layout delete $C }
}
exit 0
'''


def tcl_quote(s):
    return '"' + re.sub(r'([\\"$\[\]{}])', r'\\\1', s) + '"'


def calibredrv():
    return os.environ.get('CALIBREDRV') or shutil.which('calibredrv')


def available():
    return calibredrv() is not None


def make_script(gds, cells, paths):
    return TCL % {
        'gds': tcl_quote(gds),
        'cells': ' '.join(tcl_quote(c) for c in cells),
        'paths': ' '.join(tcl_quote(p) for p in paths),
    }


def _number(s):
    for conv in (int, float):
        try:
            return conv(s)
        except ValueError:
            pass
    return s


def parse_output(text, cell_list):
    info = {'cells': [], 'ip_layers': {ip: set() for ip in cell_list}}
    layers, missing = [], []
    for line in text.splitlines():
        if not line.startswith(PREFIX + '\t'):
            continue  # Calibre banner and progress messages
        key, _, value = line[len(PREFIX) + 1:].partition('\t')
        if key == 'missing':
            missing.append(value)
        elif key == 'top':
            info['top_cell'] = value
        elif key == 'cell':
            info['cells'].append(value)
        elif key == 'layer':
            layers.append(value)
        elif key == 'extent':
            info['extent'] = tuple(_number(v) for v in value.split()) if value != '?' else value
        elif key in ('scale_factor', 'units'):
            info[key] = _number(value)
        elif key == 'ip_layer':
            cell, _, layer = value.partition('\t')
            info['ip_layers'][cell].add(layer)
    return info, layers, missing


def _layer_key(layer):
    return [_number(part) for part in layer.split('.')]


def collect_info(gds, cell_list, layer_filter, workdir='.'):
    with tempfile.TemporaryDirectory(prefix='.gds_layers_', dir=workdir) as tmp:
        paths = [os.path.join(os.path.abspath(tmp), 'cell%d.gds' % i) for i in range(len(cell_list))]
        script = os.path.join(tmp, 'gds_layers.tcl')
        with open(script, 'w') as f:
            f.write(make_script(gds, list(cell_list), paths))
        proc = subprocess.run([calibredrv(), script], stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, universal_newlines=True)  # noqa: UP021 (py3.6)
    info, layers, missing = parse_output(proc.stdout, cell_list)
    check_cells([c for c in cell_list if c not in missing], cell_list, gds)
    if proc.returncode != 0 or 'top_cell' not in info:
        raise RuntimeError('calibredrv failed (exit %d):\n%s' % (proc.returncode, proc.stdout))
    info['top_layers'] = [layer for layer in sorted(layers, key=_layer_key)
                          if re.match(layer_filter, layer)]
    return info
