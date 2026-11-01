# get_gds_layers

Reads a GDS file and writes a report of the top cell: its size, scale factor, units, cell
list and layers. You can also pass sub-cells (IPs) to get a matrix that shows which
top-level layers each one uses.

There are two independent scripts, one per tool. Use the one for the tool you have:

| Tool | Script | Run with |
| --- | --- | --- |
| Cadence PVS | [pvs/get_all_gds_layers.py](pvs/get_all_gds_layers.py) | `k2_quake python` |
| Siemens Calibre | [calibre/get_all_gds_layers.tcl](calibre/get_all_gds_layers.tcl) | `calibredrv` |

Both take the same inputs (a GDS, plus optional cells with short column names and a layer
filter) and write the [same report](#output).

## PVS

Source your PVS setup, then run:

```bash
k2_quake python pvs/get_all_gds_layers.py design.gds
k2_quake python pvs/get_all_gds_layers.py design.gds -c very_long_ip_cell_name=ipA -c other_ip
```

| Option | Description |
| --- | --- |
| `gds` | Path to the GDS file. |
| `-c, --cell CELL[=ALIAS]` | Cell to compare against the top cell. Repeat for each cell. `ALIAS` is the report column name. |
| `--layer-filter REGEX` | Report only the layers whose names match this regex. Default: `.*lay.*`. |

Without arguments, the script uses the `GDS` and `CELL_LIST` values at its top.
It needs Python 3.6 or newer (whatever PVS ships with) and can't run under plain `python`.

## Calibre

Source your Calibre setup, then run:

```bash
calibredrv calibre/get_all_gds_layers.tcl design.gds
calibredrv calibre/get_all_gds_layers.tcl design.gds very_long_ip_cell_name=ipA other_ip
```

| Argument | Description |
| --- | --- |
| `gds` | Path to the GDS file (first argument). |
| `CELL[=ALIAS]` | Cell to compare against the top cell. List as many as needed, no `-c`. `ALIAS` is the report column name. |
| `-layer_filter REGEX` | Report only the layers whose names match this regex. Default: all layers. |

Without arguments, the script uses the `gds`, `cell_list` and `layer_filter` values at its
top. Layers are reported as `layer.datatype`. If precision, units or the bbox can't be read,
the script prints a warning and writes `?` in the report instead of failing.

## Notes for both tools

- Extracting large cells can take a while.
- Requested cells are checked against the GDS before any extraction starts, so a typo fails
  immediately.
- Each requested cell is extracted into a hidden temporary directory (`.gds_layers_*`) in the
  current directory. The directory is removed afterwards, even if the run fails.

## Output

Both scripts write the same two files to the current directory, in the same format:

- `<top_cell>_GDS_info`: summary and layer matrix (`+` means the cell uses the layer, `-` means it doesn't)
- `<top_cell>_GDS_cells`: every cell name in the GDS, one per line

Example `<top_cell>_GDS_info` (PVS; Calibre reports layers as `layer.datatype`, e.g. `31.0`):

```
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
```

## Development

The tests run without PVS or Calibre: the Python script uses a fake `k2_quake` module
([tests/conftest.py](tests/conftest.py)), and the Tcl script runs under `tclsh` with a fake
`layout` command:

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
vermin --no-tips --eval-annotations --violations -t=3.6- pvs/get_all_gds_layers.py
```

CI runs the same checks on every push.

## License

[Apache License 2.0](LICENSE)
