import datetime
import os

import pytest

from gds_layers.backends import pvs
from gds_layers.report import parse_cell_args, write_reports

NOW = datetime.datetime(2026, 10, 6, 12, 0, 0)

# Produced by the original script (commit 5136add) for the same fake layout.
EXPECTED_WITH_CELLS = """\
GDS: top.gds
Generated at 2026-10-06 12:00:00

Top cell:    TOP
All layers:  3
Top size:    (0, 0, 100, 100)
Scale factor: 1000
dbUnits:     um
All cells:   ./TOP_GDS_cells

-------------------

   TOP   | IPA | b |
-------------------
 m1_lay  |  +  | - |
-------------------
 m2_lay  |  -  | + |
-------------------
 via_lay |  -  | + |
-------------------
"""

EXPECTED_TOP_ONLY = """\
GDS: top.gds
Generated at 2026-10-06 12:00:00

Top cell:    TOP
All layers:  3
Top size:    (0, 0, 100, 100)
Scale factor: 1000
dbUnits:     um
All cells:   ./TOP_GDS_cells

---------

   TOP   |
---------
 m1_lay  |
---------
 m2_lay  |
---------
 via_lay |
---------
"""


def run(k2, tmp_path, cell_list, layer_filter=pvs.LAYER_FILTER):
    info = pvs.collect_info('top.gds', cell_list, layer_filter, workdir=str(tmp_path), k2=k2)
    write_reports(info, 'top.gds', cell_list, outdir=str(tmp_path), now=NOW)
    return info


def test_report_matches_original_format(k2, tmp_path):
    run(k2, tmp_path, {'IPA': '', 'IPB': 'b'})
    assert (tmp_path / 'TOP_GDS_info').read_text() == EXPECTED_WITH_CELLS
    assert (tmp_path / 'TOP_GDS_cells').read_text() == 'TOP\nIPA\nIPB\n'


def test_top_only_report(k2, tmp_path):
    run(k2, tmp_path, {})
    assert (tmp_path / 'TOP_GDS_info').read_text() == EXPECTED_TOP_ONLY
    assert not any(c[0] == 'extract' for c in k2.calls)


def test_layer_filter(k2, tmp_path):
    info = run(k2, tmp_path, {}, layer_filter='m.*')
    assert info['top_layers'] == ['m1_lay', 'm2_lay']


def test_temp_files_removed_and_existing_files_untouched(k2, tmp_path):
    # A user file with the same name as a cell must survive the run.
    (tmp_path / 'IPA.gds').write_text('keep me')
    run(k2, tmp_path, {'IPA': ''})
    assert (tmp_path / 'IPA.gds').read_text() == 'keep me'
    assert sorted(os.listdir(str(tmp_path))) == ['IPA.gds', 'TOP_GDS_cells', 'TOP_GDS_info']


def test_temp_files_removed_on_failure(k2, tmp_path):
    def boom(db, path, cell):
        open(path, 'w').close()
        raise RuntimeError('extraction failed')
    k2.data_db_extract = boom
    with pytest.raises(RuntimeError):
        run(k2, tmp_path, {'IPA': ''})
    assert os.listdir(str(tmp_path)) == []


def test_cell_names_with_path_characters(k2, tmp_path):
    k2.layout['lib/cell$1'] = ['m1_lay']
    run(k2, tmp_path, {'lib/cell$1': 'x'})
    assert ' m1_lay  | + |' in (tmp_path / 'TOP_GDS_info').read_text()


def test_missing_cell_fails_before_extraction(k2, tmp_path):
    with pytest.raises(ValueError, match='NOPE'):
        run(k2, tmp_path, {'IPA': '', 'NOPE': ''})
    assert not any(c[0] == 'extract' for c in k2.calls)


def test_parse_cell_args():
    assert parse_cell_args(['A', 'B=b', 'C=']) == {'A': '', 'B': 'b', 'C': ''}
