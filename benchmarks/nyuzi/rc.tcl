# Cap scaling: the platform RC applies to every scene, then each scene re-issues every set_layer_rc and
# set_wire_rc line with its capacitance multiplied by the factor of its corner below. Resistance is unchanged.
# Source this file after mcmm.tcl and after the scenes are defined. Scene names are those of mcmm.tcl:
# mcmm_scenes of a scan testcase, mcmm_corners otherwise. A scan test scene uses the RC of its corner.
set rc_platform_file [file join $::env(PLATFORM_DIR) util setRC.tcl]
source $rc_platform_file
set rc_cap_scale {BC 0.9 TC 1 WC 1.1}
if {[info exists mcmm_scenes]} { set rc_scenes $mcmm_scenes } else { set rc_scenes $mcmm_corners }
set fh [open $rc_platform_file]
set rc_lines [split [read $fh] "\n"]
close $fh
foreach {rc_corner rc_cap} $rc_cap_scale {
    if {[info exists ::env(CORNERS)] && $rc_corner ni $::env(CORNERS)} { continue }
    set issued 0
    foreach line $rc_lines {
        if {![regexp {^\s*(set_layer_rc|set_wire_rc)\s} $line]} { continue }
        set words [lrange $line 1 end]
        set out {}
        for {set i 0} {$i < [llength $words]} {incr i} {
            set w [lindex $words $i]
            if {$w eq "-capacitance"} {
                incr i
                lappend out $w [expr {[lindex $words $i] * $rc_cap}]
            } else {
                lappend out $w
            }
        }
        foreach rc_scene $rc_scenes {
            if {[info exists scenario_corner($rc_scene)]} {
                set rc_scene_corner $scenario_corner($rc_scene)
            } else {
                set rc_scene_corner $rc_scene
            }
            if {$rc_scene_corner eq $rc_corner} { [lindex $line 0] {*}$out -corner $rc_scene }
        }
        incr issued
    }
    puts "CAP_SCALE corner $rc_corner capacitance x$rc_cap ($issued commands)"
}
