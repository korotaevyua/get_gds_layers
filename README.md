# get_gds_layers

Reads a GDS file and writes a report of the top cell: its size, scale factor, units, cell
list and layers. You can also pass sub-cells (IPs) to get a matrix that shows which
top-level layers each one uses.

It works with whichever layout tool you have:

| `--tool` | Needs | Layer names |
| --- | --- | --- |
| `pvs` | Cadence PVS: a sourced PVS setup; run with `k2_quake python` | as PVS reports them |
| `calibre` | Siemens Calibre: `calibredrv` on `PATH` (or set `CALIBREDRV`) | `layer.datatype` |
| `gdstk` | open source: `pip install gdstk` | `layer.datatype` |

With the default `--tool auto`, the first available tool is used, in the order above.

> **Calibre:** the backend hasn't been run against a real Calibre yet. Its DESIGNrev Tcl
> script is tested under `tclsh` with a fake `layout` command
> ([tests/fake_calibredrv.tcl](tests/fake_calibredrv.tcl)), so check the first real run.

Requires Python 3.6 or newer.

## Usage

```bash
k2_quake python get_all_gds_layers.py design.gds          # PVS
python3 get_all_gds_layers.py design.gds --tool calibre   # Calibre
python3 get_all_gds_layers.py design.gds --tool gdstk     # open source
```

To compare sub-cells against the top cell, add `-c CELL` once per cell. You can also give
a short column name with `CELL=ALIAS`:

```bash
k2_quake python get_all_gds_layers.py design.gds -c very_long_ip_cell_name=ipA -c other_ip
```

| Option | Description |
| --- | --- |
| `gds` | Path to the GDS file. |
| `-c, --cell CELL[=ALIAS]` | Cell to compare against the top cell. Can be repeated. |
| `-t, --tool {auto,pvs,calibre,gdstk}` | Layout tool to read the GDS with. Default: `auto`. |
| `--layer-filter REGEX` | Report only the layers whose names match this regex. Default: `.*lay.*` for PVS, everything for the other tools. |

If you don't pass any arguments, the script uses the `GDS` and `CELL_LIST` values set at
the top of `get_all_gds_layers.py`.

> Extracting large cells can take a while with PVS and Calibre. Each requested cell is
> extracted into a hidden temporary directory (`.gds_layers_*`) in the current directory,
> which is removed afterwards, even if the run fails. Requested cells are checked against
> the GDS before any extraction starts. gdstk reads the hierarchy directly and doesn't
> extract anything.

## Adding a tool

Add a module to [gds_layers/backends/](gds_layers/backends/) with `NAME`, `REQUIREMENT`,
`LAYER_FILTER`, `available()` and `collect_info()` (see
[gds_layers/backends/__init__.py](gds_layers/backends/__init__.py)), then list it in
`BACKENDS`. The report itself is built in [gds_layers/report.py](gds_layers/report.py).

## Output

The script writes two files to the current directory:

- `<top_cell>_GDS_info`: summary and layer matrix (`+` means the cell uses the layer, `-` means it doesn't)
- `<top_cell>_GDS_cells`: every cell name in the GDS, one per line

Example `<top_cell>_GDS_info`:

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

The tests run without any EDA tool: PVS uses a fake `k2_quake` module
([tests/conftest.py](tests/conftest.py)), Calibre uses `tclsh` with a fake `layout` command, and
gdstk reads real GDS files that the tests generate.

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
vermin --no-tips --eval-annotations --violations -t=3.6- get_all_gds_layers.py gds_layers
```

CI runs the same checks on every push.

## License

[Apache License 2.0](LICENSE)
