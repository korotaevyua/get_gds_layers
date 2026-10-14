import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class FakeK2Quake:
    """Stand-in for the PVS k2_quake API, covering only what the script calls.

    `layout` maps cell name -> layers in that cell; the first entry is the top cell.
    """

    def __init__(self, layout, extent=(0, 0, 100, 100), scale_factor=1000, units='um'):
        self.layout = layout
        self.top = next(iter(layout))
        self.extent = extent
        self.scale_factor = scale_factor
        self.units = units
        self.extracted = {}  # path -> cell
        self.calls = []

    def data_read_file(self, path):
        self.calls.append(('read', path))
        if path in self.extracted:
            assert os.path.exists(path), 'extracted file was removed before reading'
            return self.extracted[path]
        return self.top

    def data_get_db_layers(self, db):
        return list(self.layout[db])

    def data_get_db_cell_name(self, db):
        return db

    def data_get_db_cell_extent(self, db):
        return self.extent

    def data_get_db_scale_factor(self, db):
        return self.scale_factor

    def data_get_db_units(self, db):
        return self.units

    def data_get_db_cell_names(self, db):
        return list(self.layout)

    def data_db_extract(self, db, path, cell):
        self.calls.append(('extract', path, cell))
        if cell not in self.layout:
            raise RuntimeError('no such cell: ' + cell)
        with open(path, 'w') as f:
            f.write('fake gds')
        self.extracted[path] = cell


@pytest.fixture
def k2():
    return FakeK2Quake({
        'TOP': ['m1_lay', 'm2_lay', 'via_lay', 'text'],
        'IPA': ['m1_lay'],
        'IPB': ['m2_lay', 'via_lay'],
    })


@pytest.fixture
def fake_calibredrv(tmp_path, monkeypatch):
    """Point CALIBREDRV at tclsh running tests/fake_calibredrv.tcl."""
    tclsh = shutil.which('tclsh')
    if tclsh is None:
        pytest.skip('tclsh not installed')
    exe = tmp_path / 'calibredrv'
    exe.write_text('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (
        tclsh, os.path.join(ROOT, 'tests', 'fake_calibredrv.tcl')))
    exe.chmod(0o755)
    monkeypatch.setenv('CALIBREDRV', str(exe))

    def set_layout(tcl_layout):
        monkeypatch.setenv('FAKE_LAYOUT', tcl_layout)
    return set_layout
