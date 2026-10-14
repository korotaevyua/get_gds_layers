import pytest

from gds_layers.backends import gdstk_backend

gdstk = pytest.importorskip('gdstk')


def make_gds(path):
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    ipa = lib.new_cell('IPA')
    ipa.add(gdstk.rectangle((0, 0), (1, 1), layer=1, datatype=0))
    ipa.add(gdstk.Label('pin', (0, 0), layer=63, texttype=5))
    leaf = lib.new_cell('LEAF')
    leaf.add(gdstk.FlexPath([(0, 0), (5, 0)], 0.1, layer=10, datatype=2))
    ipb = lib.new_cell('IPB')
    ipb.add(gdstk.rectangle((0, 0), (2, 2), layer=2, datatype=0))
    ipb.add(gdstk.Reference(leaf))
    top = lib.new_cell('TOP')
    top.add(gdstk.rectangle((0, 0), (100, 50), layer=3, datatype=1))
    top.add(gdstk.Reference(ipa, (10, 10)), gdstk.Reference(ipb, (20, 20)))
    lib.write_gds(str(path))


def test_collect_info(tmp_path):
    gds = tmp_path / 'design.gds'
    make_gds(gds)
    info = gdstk_backend.collect_info(str(gds), {'IPA': '', 'IPB': 'b'}, '.*', str(tmp_path))
    assert info['top_cell'] == 'TOP'
    assert info['top_layers'] == ['1.0', '2.0', '3.1', '10.2', '63.5']
    assert info['extent'] == (0, 0, 100, 50)
    assert info['scale_factor'] == 1000
    assert sorted(info['cells']) == ['IPA', 'IPB', 'LEAF', 'TOP']
    assert info['ip_layers'] == {'IPA': {'1.0', '63.5'}, 'IPB': {'2.0', '10.2'}}


def test_missing_cell(tmp_path):
    gds = tmp_path / 'design.gds'
    make_gds(gds)
    with pytest.raises(ValueError, match='NOPE'):
        gdstk_backend.collect_info(str(gds), {'NOPE': ''}, '.*', str(tmp_path))


def test_multiple_top_cells(tmp_path):
    lib = gdstk.Library()
    lib.new_cell('A')
    lib.new_cell('B')
    lib.write_gds(str(tmp_path / 'two.gds'))
    with pytest.raises(ValueError, match='2 top cells'):
        gdstk_backend.collect_info(str(tmp_path / 'two.gds'), {}, '.*', str(tmp_path))
