"""Run calibre/get_all_gds_layers.tcl under tclsh with a fake `layout` command."""
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'calibre', 'get_all_gds_layers.tcl')
FAKE = os.path.join(ROOT, 'tests', 'fake_calibredrv.tcl')
TCLSH = shutil.which('tclsh')

pytestmark = pytest.mark.skipif(TCLSH is None, reason='tclsh not installed')

LAYOUT = 'TOP {10.0 2.0 1.0 3.1} IPA {1.0} {lib/ip $x} {2.0 10.0}'

EXPECTED = """\
GDS: design.gds
Generated at <now>

Top cell:    TOP
All layers:  4
Top size:    0 0 100000 50000
Scale factor: 1000.0
dbUnits:     0.001
All cells:   ./TOP_GDS_cells

-------------------

   TOP   | IPA | x |
-------------------
   1.0   |  +  | - |
-------------------
   2.0   |  -  | + |
-------------------
   3.1   |  -  | - |
-------------------
  10.0   |  -  | + |
-------------------
"""


def run(tmp_path, *args, layout=LAYOUT, env=None):
    full_env = dict(os.environ, FAKE_LAYOUT=layout, **(env or {}))
    return subprocess.run([TCLSH, FAKE, SCRIPT] + list(args), cwd=str(tmp_path), env=full_env,
                          capture_output=True, text=True)


def report(tmp_path):
    text = (tmp_path / 'TOP_GDS_info').read_text()
    return re.sub(r'Generated at .*', 'Generated at <now>', text)


def test_report(tmp_path):
    proc = run(tmp_path, 'design.gds', 'IPA', 'lib/ip $x=x')
    assert proc.returncode == 0, proc.stderr
    assert report(tmp_path) == EXPECTED
    assert (tmp_path / 'TOP_GDS_cells').read_text() == 'TOP\nIPA\nlib/ip $x\n'
    assert 'START IPA GDS extraction' in proc.stdout
    assert sorted(os.listdir(str(tmp_path))) == ['TOP_GDS_cells', 'TOP_GDS_info']


def test_top_only(tmp_path):
    proc = run(tmp_path, 'design.gds')
    assert proc.returncode == 0, proc.stderr
    assert report(tmp_path).endswith('---------\n\n   TOP   |\n---------\n   1.0   |\n---------\n'
                                      '   2.0   |\n---------\n   3.1   |\n---------\n  10.0   |\n---------\n')


def test_layer_filter(tmp_path):
    proc = run(tmp_path, 'design.gds', '-layer_filter', '1')
    assert proc.returncode == 0, proc.stderr
    assert 'All layers:  2' in report(tmp_path)


def test_missing_cell(tmp_path):
    proc = run(tmp_path, 'design.gds', 'IPA', 'NOPE')
    assert proc.returncode == 1
    assert 'cells not found in design.gds: NOPE' in proc.stderr
    assert 'START' not in proc.stdout
    assert os.listdir(str(tmp_path)) == []


def test_extraction_failure_cleans_up(tmp_path):
    proc = run(tmp_path, 'design.gds', 'IPA', env={'FAKE_GDSOUT_FAIL': '1'})
    assert proc.returncode == 1
    assert 'fake gdsout failure' in proc.stderr
    assert os.listdir(str(tmp_path)) == []


def test_no_gds(tmp_path):
    proc = run(tmp_path)
    assert proc.returncode == 1
    assert 'no GDS given' in proc.stderr


def test_unsupported_commands_only_warn(tmp_path):
    # Simulate a Calibre without `layout peek -precision`: falls back to bare peek,
    # which the fake does not support either, so the value becomes "?".
    fake = (tmp_path / 'fake.tcl')
    fake.write_text(open(FAKE).read().replace('-precision { return 1000.0 }', ''))
    (tmp_path / 'out').mkdir()
    proc = subprocess.run([TCLSH, str(fake), SCRIPT, 'design.gds'], cwd=str(tmp_path / 'out'),
                          env=dict(os.environ, FAKE_LAYOUT=LAYOUT),
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert 'WARNING: cannot get precision' in proc.stderr
    assert 'Scale factor: ?' in (tmp_path / 'out' / 'TOP_GDS_info').read_text()
