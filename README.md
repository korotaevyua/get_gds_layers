# get_gds_layers

A small script for the PVS `k2_quake` Python environment. It reads a GDS file and writes a
report of the top cell: its size, scale factor, units, cell list and layers. You can also
pass sub-cells (IPs) to get a matrix that shows which top-level layers each one uses.

## Requirements

- A sourced PVS setup that provides the `k2_quake` command and Python module.
  The script can't run under plain `python`.

## Usage

```bash
k2_quake python get_all_gds_layers.py path/to/design.gds
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
| `--layer-filter REGEX` | Report only the layers whose names match this regex. Default: `.*lay.*`. |

If you don't pass any arguments, the script uses the `GDS` and `CELL_LIST` values set at
the top of `get_all_gds_layers.py`.

> Extracting large cells can take a while. Each requested cell is written to a temporary
> `<cell>.gds` in the current directory, and that file is deleted afterwards.

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

## License

[Apache License 2.0](LICENSE)
