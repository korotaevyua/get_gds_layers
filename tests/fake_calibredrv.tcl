# Fake `calibredrv`: runs a DESIGNrev script under plain tclsh with a fake
# `layout` command. Usage: tclsh fake_calibredrv.tcl script.tcl args...
#
# The design comes from $env(FAKE_LAYOUT): a Tcl list of cell / layers pairs,
# top cell first, layers already including the cell's hierarchy, e.g.
#   TOP {1.0 2.0 3.0} IPA {1.0}

set fake_layout $env(FAKE_LAYOUT)
set fake_top [lindex $fake_layout 0]
set fake_n 0

# Extracted files hold their cell name; anything else is the full design.
proc fake_cell_of {path} {
    global fake_layout fake_top
    if {[file exists $path]} {
        set f [open $path]
        set content [string trim [read $f]]
        close $f
        if {[dict exists $fake_layout $content]} { return $content }
    }
    return $fake_top
}

proc layout {sub args} {
    global fake_n
    switch -- $sub {
        create {
            set handle fakelayout[incr fake_n]
            interp alias {} $handle {} fake_handle [fake_cell_of [lindex $args 0]]
            return $handle
        }
        delete { interp alias {} [lindex $args 0] {} }
        peek {
            switch -- [lindex $args 1] {
                -precision { return 1000.0 }
                default { error "fake layout peek: unsupported option [lindex $args 1]" }
            }
        }
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
            if {[lindex $args 0] eq "user"} { return 0.001 }
            error "fake units: unsupported $args"
        }
        gdsout {
            set path [lindex $args 0]
            set c [lindex $args 1]
            if {![dict exists $fake_layout $c]} { error "no such cell $c" }
            if {[info exists ::env(FAKE_GDSOUT_FAIL)]} {
                close [open $path w]
                error "fake gdsout failure"
            }
            set f [open $path w]
            puts $f $c
            close $f
        }
        default { error "fake layout: unsupported subcommand $sub" }
    }
}

puts "//  Calibre DESIGNrev (fake banner)"
set argv0 [lindex $argv 0]
set argv [lrange $argv 1 end]
set argc [llength $argv]
source $argv0
