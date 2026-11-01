# Calibre DESIGNrev version of pvs/get_all_gds_layers.py.
#
# Creates report file <top_cell>_GDS_info with all layers of the top cell
# and, optionally, which of them are used by selected cells, plus
# <top_cell>_GDS_cells with the list of all cells.
#
# Usage:
#   calibredrv calibre/get_all_gds_layers.tcl design.gds [CELL[=ALIAS] ...] [-layer_filter REGEX]
#
#   CELL=ALIAS      ALIAS is used as the column name in the report.
#   -layer_filter   report only layers matching REGEX (default: all layers).
#
# Without arguments, the gds / cell_list / layer_filter values below are used.
# Extraction may take time for large GDS cells.
#
# The DESIGNrev commands used are collected in one place (open_layout ...
# layout_precision). Besides real Calibre runs, CI tests the script under plain
# tclsh with a fake `layout` command (tests/fake_calibredrv.tcl).
# Written for Tcl 8.4 (no dict/lassign/{*}).

set gds ""
# Pairs of actual cell name and short name for the report column ("" keeps
# the name), e.g.  set cell_list {{cell name} {optional short name} IPB {}}
set cell_list {}
set layer_filter {.*}

# ---------------------------------------------------------------------------
# DESIGNrev commands.

proc open_layout {path} {
    return [layout create $path -dt_expand]
}

proc close_layout {L} {
    catch {layout delete $L}
}

# Layers as "layer.datatype". Some versions/commands return {layer datatype}
# pairs; normalize both forms.
proc layout_layers {L} {
    set result {}
    foreach layer [$L layers] {
        if {[llength $layer] == 2} {
            set layer "[lindex $layer 0].[lindex $layer 1]"
        }
        lappend result $layer
    }
    return $result
}

# Write `cell` with its hierarchy to `path`.
proc extract_cell {L cell path} {
    $L gdsout $path $cell
}

# Database units per user unit (e.g. 1000.0), as `layout peek` reports it.
proc layout_precision {gds} {
    if {[catch {layout peek $gds -precision} value]} {
        # Without options layout peek also reports the precision.
        set value [layout peek $gds]
    }
    return $value
}

# ---------------------------------------------------------------------------

# Value of `script`, or "?" with a warning if the command is not supported.
proc try_value {what script} {
    if {[catch {uplevel 1 $script} value]} {
        puts stderr "WARNING: cannot get $what: $value"
        return "?"
    }
    return $value
}

# Center like Python's f"{s:^{width}}" (extra space goes to the right).
proc center {s width} {
    set pad [expr {$width - [string length $s]}]
    if {$pad <= 0} { return $s }
    set left [expr {$pad / 2}]
    return "[string repeat { } $left]$s[string repeat { } [expr {$pad - $left}]]"
}

proc parse_args {argv} {
    global gds cell_list layer_filter
    if {[llength $argv] == 0} { return }
    set gds ""
    set cell_list {}
    for {set i 0} {$i < [llength $argv]} {incr i} {
        set arg [lindex $argv $i]
        if {$arg eq "-layer_filter"} {
            incr i
            set layer_filter [lindex $argv $i]
        } elseif {$gds eq ""} {
            set gds $arg
        } else {
            set eq [string first = $arg]
            if {$eq < 0} {
                lappend cell_list $arg {}
            } else {
                lappend cell_list [string range $arg 0 [expr {$eq - 1}]] \
                                  [string range $arg [expr {$eq + 1}] end]
            }
        }
    }
}

proc main {argv} {
    global gds cell_list layer_filter
    parse_args $argv
    if {$gds eq ""} {
        error "no GDS given\nusage: calibredrv get_all_gds_layers.tcl design.gds\
               \[CELL\[=ALIAS\] ...\] \[-layer_filter REGEX\]"
    }
    if {[catch {regexp -- $layer_filter ""} err]} {
        error "invalid -layer_filter: $err"
    }

    # Read full GDS.
    set L [open_layout $gds]
    set top_cell [$L topcell]
    set cells [$L cells]

    # Fail before the (slow) extraction rather than halfway through it.
    set missing {}
    foreach {ip alias} $cell_list {
        if {[lsearch -exact $cells $ip] < 0} { lappend missing $ip }
    }
    if {[llength $missing]} {
        error "cells not found in $gds: [join $missing {, }]"
    }

    set top_layers {}
    foreach layer [lsort -dictionary [layout_layers $L]] {
        if {[regexp -- "^(?:$layer_filter)" $layer]} { lappend top_layers $layer }
    }
    set extent [try_value "top cell extent" {$L bbox $top_cell}]
    set scale [try_value "precision" {layout_precision $gds}]
    set units [try_value "user units" {$L units user}]

    # Extract each requested cell into a private temporary directory and read
    # its layers; the directory is removed even if extraction fails.
    set tmp [file join [pwd] .gds_layers_[pid]]
    file mkdir $tmp
    set failed [catch {
        set i 0
        foreach {ip alias} $cell_list {
            set path [file join $tmp cell[incr i].gds]
            puts "START $ip GDS extraction"
            extract_cell $L $ip $path
            puts "FINISH $ip GDS extraction"
            set C [open_layout $path]
            set ip_layers($ip) [layout_layers $C]
            close_layout $C
        }
    } err]
    if {$failed} { set info $::errorInfo }
    file delete -force $tmp
    if {$failed} { error $err $info }

    # Report to file.
    set f [open ${top_cell}_GDS_cells w]
    foreach cell $cells { puts $f $cell }
    close $f

    set names "[center $top_cell [expr {[string length $top_cell] + 6}]]|"
    set dash_line [string repeat - [expr {[string length $top_cell] + 6}]]
    foreach {ip alias} $cell_list {
        set col [expr {$alias eq "" ? $ip : $alias}]
        append names "[center $col [expr {[string length $col] + 2}]]|"
        append dash_line - [string repeat - [expr {[string length $col] + 2}]]
    }

    set f [open ${top_cell}_GDS_info w]
    puts $f "GDS: $gds"
    puts $f "Generated at [clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"
    puts $f ""
    puts $f "Top cell:    $top_cell"
    puts $f "All layers:  [llength $top_layers]"
    puts $f "Top size:    $extent"
    puts $f "Scale factor: $scale"
    puts $f "dbUnits:     $units"
    puts $f "All cells:   ./${top_cell}_GDS_cells"
    puts $f ""
    puts $f $dash_line
    puts $f ""
    puts $f $names
    puts $f $dash_line
    foreach layer $top_layers {
        set row "[center $layer [expr {[string length $top_cell] + 6}]]|"
        foreach {ip alias} $cell_list {
            set col [expr {$alias eq "" ? $ip : $alias}]
            set mark [expr {[lsearch -exact $ip_layers($ip) $layer] >= 0 ? "+" : "-"}]
            append row "[center $mark [expr {[string length $col] + 2}]]|"
        }
        puts $f $row
        puts $f $dash_line
    }
    close $f
    close_layout $L
}

if {[catch {main $argv} err]} {
    puts stderr "ERROR: $err"
    exit 1
}
exit 0
