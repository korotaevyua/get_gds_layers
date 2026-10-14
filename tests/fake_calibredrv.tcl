# Fake `calibredrv`: runs a DESIGNrev script under plain tclsh with a fake
# `layout` command. Usage: tclsh fake_calibredrv.tcl script.tcl
#
# The design comes from $env(FAKE_LAYOUT): a Tcl list of cell / layers pairs,
# top cell first, layers already including the cell's hierarchy, e.g.
#   TOP {1.0 2.0 3.0} IPA {1.0}

set fake_layout $env(FAKE_LAYOUT)
set fake_top [lindex $fake_layout 0]
set fake_n 0

proc layout {sub args} {
    global fake_layout fake_top fake_n
    switch -- $sub {
        create {
            # Extracted files hold their cell name; anything else is the full design.
            set path [lindex $args 0]
            set cell $fake_top
            if {[file exists $path]} {
                set f [open $path]
                set content [string trim [read $f]]
                close $f
                if {[dict exists $fake_layout $content]} { set cell $content }
            }
            set handle fakelayout[incr fake_n]
            interp alias {} $handle {} fake_handle $cell
            return $handle
        }
        delete { interp alias {} [lindex $args 0] {} }
        default { error "fake layout: unsupported subcommand $sub" }
    }
}

proc fake_handle {cell sub args} {
    global fake_layout
    switch -- $sub {
        topcell { return $cell }
        cells { return [dict keys $fake_layout] }
        layers { return [dict get $fake_layout $cell] }
        bbox { return {0 0 100000 50000} }
        units {
            switch -- [lindex $args 0] {
                user { return 0.001 }
                database { return 1e-09 }
            }
        }
        gdsout {
            lassign $args path c
            if {![dict exists $fake_layout $c]} { error "no such cell $c" }
            set f [open $path w]
            puts $f $c
            close $f
        }
        default { error "fake layout: unsupported subcommand $sub" }
    }
}

puts "//  Calibre DESIGNrev (fake banner)"
source [lindex $argv 0]
