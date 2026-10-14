import os

import pytest

from gds_layers.backends import calibre

LAYOUT = 'TOP {1.0 2.0 10.0 3.1} IPA {1.0} {lib/ip $x} {2.0 10.0}'


def test_tcl_quote():
    assert calibre.tcl_quote('a b') == '"a b"'
    assert calibre.tcl_quote('x$[y]{z}"\\') == r'"x\$\[y\]\{z\}\"\\"'


def test_collect_info(fake_calibredrv, tmp_path):
    fake_calibredrv(LAYOUT)
    cells = {'IPA': '', 'lib/ip $x': 'x'}
    info = calibre.collect_info('design.gds', cells, '.*', str(tmp_path))
    assert info['top_cell'] == 'TOP'
    assert info['top_layers'] == ['1.0', '2.0', '3.1', '10.0']
    assert info['cells'] == ['TOP', 'IPA', 'lib/ip $x']
    assert info['extent'] == (0, 0, 100000, 50000)
    assert info['scale_factor'] == 0.001
    assert info['units'] == 1e-09
    assert info['ip_layers'] == {'IPA': {'1.0'}, 'lib/ip $x': {'2.0', '10.0'}}
    assert os.listdir(str(tmp_path)) == ['calibredrv']  # temp dir removed


def test_layer_filter(fake_calibredrv, tmp_path):
    fake_calibredrv(LAYOUT)
    info = calibre.collect_info('design.gds', {}, '1', str(tmp_path))
    assert info['top_layers'] == ['1.0', '10.0']


def test_missing_cell_skips_extraction(fake_calibredrv, tmp_path):
    fake_calibredrv(LAYOUT)
    with pytest.raises(ValueError, match='NOPE'):
        calibre.collect_info('design.gds', {'IPA': '', 'NOPE': ''}, '.*', str(tmp_path))


def test_calibredrv_failure(fake_calibredrv, tmp_path):
    fake_calibredrv('TOP')  # odd-length list: the fake fails on startup
    with pytest.raises(RuntimeError, match='calibredrv failed'):
        calibre.collect_info('design.gds', {}, '.*', str(tmp_path))
