import builtins

import pytest

import get_all_gds_layers as cli
from gds_layers import backends


def test_parse_args():
    args = cli.parse_args(['a.gds', '-c', 'IPA', '-c', 'IPB=b', '--tool', 'gdstk', '--layer-filter', 'm.*'])
    assert (args.gds, args.cell_list, args.tool, args.layer_filter) == \
        ('a.gds', {'IPA': '', 'IPB': 'b'}, 'gdstk', 'm.*')


def test_parse_args_defaults(monkeypatch):
    monkeypatch.setattr(cli, 'GDS', 'default.gds')
    monkeypatch.setattr(cli, 'CELL_LIST', {'X': 'y'})
    args = cli.parse_args([])
    assert (args.gds, args.cell_list, args.tool, args.layer_filter) == \
        ('default.gds', {'X': 'y'}, 'auto', None)


@pytest.mark.parametrize('argv', [[], ['a.gds', '--layer-filter', '['], ['a.gds', '--tool', 'nope']])
def test_parse_args_errors(argv):
    with pytest.raises(SystemExit):
        cli.parse_args(argv)


def test_auto_prefers_pvs(k2, monkeypatch):
    monkeypatch.setattr(builtins, 'k2_quake', k2, raising=False)
    assert backends.get_backend('auto') is backends.pvs


def test_no_backend(monkeypatch):
    for b in backends.BACKENDS:
        monkeypatch.setattr(b, 'available', lambda: False)
    with pytest.raises(RuntimeError, match='no layout tool found'):
        backends.get_backend('auto')
    with pytest.raises(RuntimeError, match='calibre is not available'):
        backends.get_backend('calibre')


def test_main_pvs(k2, tmp_path, monkeypatch):
    monkeypatch.setattr(builtins, 'k2_quake', k2, raising=False)
    monkeypatch.chdir(tmp_path)
    cli.main(['top.gds', '-c', 'IPA'])
    report = (tmp_path / 'TOP_GDS_info').read_text()
    assert ' m1_lay  |  +  |' in report
    assert 'text' not in report  # PVS default filter applied


def test_main_calibre(fake_calibredrv, tmp_path, monkeypatch):
    fake_calibredrv('TOP {1.0 2.0} IPA {1.0}')
    monkeypatch.chdir(tmp_path)
    cli.main(['design.gds', '--tool', 'calibre', '-c', 'IPA'])
    assert '   1.0   |  +  |' in (tmp_path / 'TOP_GDS_info').read_text()


def test_main_error_exits(k2, tmp_path, monkeypatch):
    monkeypatch.setattr(builtins, 'k2_quake', k2, raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit, match='NOPE'):
        cli.main(['top.gds', '-c', 'NOPE'])
