# Standalone OpenROAD evaluator. No ORFS Tcl or Makefile is loaded.
proc out {name} { return [file join $::env(OUTPUT_DIR) $name] }
proc timed {label script} {
    set start [clock milliseconds]
    uplevel 1 $script
    set ::runtime($label) [expr {([clock milliseconds]-$start)/1000.0}]
}
proc physical_only {} {
    set result {}
    foreach master [[ord::get_db] getLibs] {
        foreach cell [$master getMasters] {
            set signal 0
            foreach pin [$cell getMTerms] {
                if {[$pin getSigType] ni {POWER GROUND}} { set signal 1 }
            }
            if {!$signal} { lappend result [$cell getName] }
        }
    }
    return $result
}
proc placement_snapshot {filename} {
    set fp [open $filename w]
    puts $fp "instance\tmaster\tx_dbu\ty_dbu\torientation\tstatus"
    foreach inst [[ord::get_db_block] getInsts] {
        lassign [$inst getLocation] x y
        puts $fp "[$inst getName]\t[[$inst getMaster] getName]\t$x\t$y\t[$inst getOrient]\t[$inst getPlacementStatus]"
    }
    close $fp
}
proc clock_snapshot {} {
    set nets {}; set insts [dict create]
    foreach net [[ord::get_db_block] getNets] {
        if {[$net getSigType] ne "CLOCK"} { continue }
        set pins {}
        foreach pin [$net getITerms] {
            set inst [$pin getInst]
            dict set insts [$inst getName] $inst
            lappend pins [list I [$inst getName] [[$pin getMTerm] getName]]
        }
        foreach pin [$net getBTerms] { lappend pins [list B [$pin getName]] }
        lappend nets [list [$net getName] [lsort $pins]]
    }
    if {[llength $nets] == 0} { error "No clock nets found in the post-CTS DEF" }
    set cells {}
    dict for {name inst} $insts {
        lappend cells [list $name [[$inst getMaster] getName] [$inst getLocation] [$inst getOrient]]
    }
    return [list [lsort $nets] [lsort $cells]]
}
proc protect_clocks {} {
    # Freeze clock cells AND sequential sink instances for this prototype.
    foreach net [[ord::get_db_block] getNets] {
        if {[$net getSigType] ne "CLOCK"} { continue }
        $net setDoNotTouch true
        foreach pin [$net getITerms] {
            set inst [$pin getInst]
            $inst setDoNotTouch true
            $inst setPlacementStatus FIRM
        }
    }
}
proc timing_metrics {scene} {
    set values [list $::env(BENCHMARK) $::env(RUN_RESIZER) $scene]
    foreach delay {max min} {
        lappend values [sta::worst_slack -scene $scene -$delay]
        lappend values [sta::total_negative_slack -scene $scene -$delay]
        set endpoints [dict create]
        foreach path [find_timing_paths -scenes $scene -path_delay $delay \
                      -group_path_count 1000000 -endpoint_path_count 1 -slack_max 0] {
            dict set endpoints [get_full_name [get_property $path endpoint]] 1
        }
        lappend values [dict size $endpoints]
        report_checks -scenes $scene -path_delay $delay -group_path_count 20 \
            -format full_clock_expanded -fields {slew capacitance fanout} -digits 6 \
            > [out ${scene}_${delay}_paths.rpt]
    }
    foreach type {max_slew max_capacitance max_fanout} {
        report_check_types -scenes $scene -$type -violators -digits 9 -no_line_splits \
            > [out ${scene}_${type}.rpt]
    }
    report_power -scene $scene -format json > [out ${scene}_power.json]
    return $values
}

source $::env(MCMM_CONFIG)
set started [clock milliseconds]
set_thread_count $::env(NUM_CORES)
source $::env(PLATFORM_DIR)/liberty_suppressions.tcl
source $::env(PLATFORM_DIR)/libraries.tcl
foreach lef [list asap7_tech_1x_201209.lef asap7sc7p5t_28_R_1x_220121a.lef \
                  asap7sc7p5t_28_L_1x_220121a.lef asap7sc7p5t_28_SL_1x_220121a.lef] {
    read_lef [file join $::env(PLATFORM_DIR) lef $lef]
}
foreach corner $::env(LIBRARY_CORNERS) {
    foreach lib $corner_libs($corner) { read_liberty $lib }
}
if {$::env(PHASE) eq "verilog_check"} {
    read_verilog $::env(INPUT_VERILOG)
    link_design $::env(DESIGN_NAME)
    write_verilog -remove_cells [physical_only] [out verilog_source.v]
    exit
}
# Snapshot immutable R0 for submission checks and displacement.
if {$::env(PHASE) eq "baseline_snapshot"} {
    read_def $::env(BASELINE_DEF)
    set fp [open [out baseline_clock.txt] w]
    puts $fp [clock_snapshot]
    close $fp
    placement_snapshot [out baseline_placement.tsv]
    exit
}
# Import the complete physical DEF, including physical-only cells and PDN.
# A separate invocation of this same script canonicalizes the supplied Verilog;
# compare those graphs before optimization so neither input can be ignored.
read_def $::env(INPUT_DEF)
if {[[ord::get_db_block] getName] ne $::env(DESIGN_NAME)} { error "Top module mismatch" }
# Separate constraint modes prevent one corner's clock period overwriting another.
foreach corner $::env(CORNERS) {
    set mode $scenario_mode($corner)
    read_sdc -mode $mode $scenario_sdc($corner)
    set_mode $mode
    foreach clk [all_clocks] {
        if {![get_property $clk is_virtual]} { set_propagated_clock $clk }
    }
    if {$::env(PHASE) eq "timing"} {
        read_spef -name rc_$corner $::env(SPEF_PREFIX)_$corner.spef
        define_scene $corner -mode $mode -liberty $corner_libs($corner) -spef rc_$corner
        report_parasitic_annotation -name rc_$corner -report_unannotated > [out ${corner}_parasitic_annotation.rpt]
    } else {
        define_scene $corner -mode $mode -liberty $corner_libs($corner)
    }
}
if {"TC" in $::env(CORNERS)} { set_scene TC } else { set_scene [lindex $::env(CORNERS) 0] }
source $::env(PLATFORM_DIR)/setRC.tcl
report_units
set fp [open [out clocks.tsv] w]
puts $fp "corner\tmode\tclock\tperiod_ps\tvirtual\tpropagated"
foreach corner $::env(CORNERS) {
    set_mode $scenario_mode($corner)
    check_setup -verbose > [out ${corner}_constraint_coverage.rpt]
    foreach clk [all_clocks] {
        puts $fp "$corner\t$scenario_mode($corner)\t[get_full_name $clk]\t[get_property $clk period]\t[get_property $clk is_virtual]\t[get_property $clk is_propagated]"
    }
}
close $fp
if {"TC" in $::env(CORNERS)} { set_scene TC } else { set_scene [lindex $::env(CORNERS) 0] }
check_setup -verbose > [out constraint_coverage.rpt]
set_dont_use {*x1p*_ASAP7* *xp*_ASAP7* SDF* ICG*}
set original_clock [clock_snapshot]
set fp [open [out clock_before.txt] w]; puts $fp $original_clock; close $fp
check_placement -verbose
write_verilog -remove_cells [physical_only] [out loaded.v]
placement_snapshot [out placement_before.tsv]
exec python3 [file join [file dirname [info script]] audit.py] input
set runtime(load) [expr {([clock milliseconds]-$started)/1000.0}]
set runtime(resizer) 0.0
set runtime(legalize) 0.0
set runtime(route) 0.0
if {$::env(PHASE) eq "full"} {
    protect_clocks
    if {$::env(RUN_RESIZER)} {
        timed resizer {
            estimate_parasitics -placement
            repair_design
            # Contest moves: VT swap, gate sizing, equivalent-pin swap, buffering.
            # Critical-path VT swapping is also enabled by omitting its skip flag.
            if {$::env(REPAIR_KIND) in {setup both}} {
                repair_timing -setup -sequence $::env(RSZ_SETUP_SEQUENCE) -skip_gate_cloning \
                    -skip_buffer_removal -skip_last_gasp -repair_tns $::env(RSZ_TNS_PERCENT) \
                    -max_iterations $::env(RSZ_MAX_ITERATIONS) -verbose
            }
            if {$::env(REPAIR_KIND) in {hold both}} {
                repair_timing -hold -max_iterations $::env(RSZ_MAX_ITERATIONS) -verbose
            }
        }
        timed legalize { detailed_placement; check_placement -verbose }
    }
    if {[clock_snapshot] ne $original_clock} { error "Clock tree or sink placement changed" }
    write_def [out evaluated.def]
    write_verilog -remove_cells [physical_only] [out evaluated.v]
    placement_snapshot [out placement_after.tsv]
    timed route {
        set_routing_layers -signal $::env(SIGNAL_LAYERS) -clock $::env(CLOCK_LAYERS)
        set_global_routing_layer_adjustment * $::env(ROUTE_ADJUSTMENT)
        set_global_routing_random -seed $::env(ROUTE_SEED)
        global_route -allow_congestion -congestion_iterations $::env(ROUTE_ITERATIONS) \
            -congestion_report_file [out congestion.rpt]
        estimate_parasitics -global_routing -spef_file [out parasitics.spef]
        write_guides [out route.guide]
    }
    if {[clock_snapshot] ne $original_clock} { error "Clock integrity changed during routing" }
    write_db [out routed.odb]
    # Preserve per-layer resource overflow; do not pool unused layer capacity.
    set grid [[ord::get_db_block] getGCellGrid]
    set fp [open [out routing.csv] w]
    puts $fp "layer,total_overflow,max_overflow,total_capacity,total_usage"
    foreach layer [[ord::get_db_tech] getLayers] {
        if {[$layer getRoutingLevel] <= 0} { continue }
        set total 0; set peak 0; set capacity 0; set usage 0
        for {set x 0} {$x < [llength [$grid getGridX]]} {incr x} {
            for {set y 0} {$y < [llength [$grid getGridY]]} {incr y} {
                set c [$grid getCapacity $layer $x $y]; set u [$grid getUsage $layer $x $y]
                set over [expr {max(0,$u-$c)}]
                set total [expr {$total+$over}]; set peak [expr {max($peak,$over)}]
                set capacity [expr {$capacity+$c}]; set usage [expr {$usage+$u}]
            }
        }
        puts $fp "[$layer getName],$total,$peak,$capacity,$usage"
    }
    close $fp
}
set fp [open [out timing.csv] w]
puts $fp "design,resizer,corner,setup_worst_slack_ps,setup_tns_ps,setup_violating_endpoints,hold_worst_slack_ps,hold_tns_ps,hold_violating_endpoints"
timed timing {
    foreach scene $::env(CORNERS) { puts $fp [join [timing_metrics $scene] ,] }
}
close $fp
set runtime(total_openroad) [expr {([clock milliseconds]-$started)/1000.0}]
set fp [open [out runtime.csv] w]; puts $fp "stage,seconds"
foreach key [lsort [array names runtime]] { puts $fp "$key,$runtime($key)" }
close $fp
if {$::env(PHASE) eq "timing"} {
    set ep [open [out endpoints.tsv] w]
    puts $ep "corner\tcheck\tendpoint\tstartpoint\tslack_ps"
    foreach corner $::env(CORNERS) {
        foreach {delay check} {max setup min hold} {
            set endpoints [dict create]
            foreach path [find_timing_paths -scenes $corner -path_delay $delay -group_path_count 1000000 -endpoint_path_count 1 -slack_max 1e30] {
                set name [get_full_name [get_property $path endpoint]]
                set slack [get_property $path slack]
                if {![dict exists $endpoints $name] || $slack < [lindex [dict get $endpoints $name] 0]} {
                    dict set endpoints $name [list $slack [get_full_name [get_property $path startpoint]]]
                }
            }
            dict for {name data} $endpoints { puts $ep "$corner\t$check\t$name\t[lindex $data 1]\t[lindex $data 0]" }
        }
    }
    close $ep
}
set ::env(INSPECT_OUTPUT) [out geometry.json]
source [file join [file dirname [info script]] inspect_geometry.tcl]
report_design_area
puts "EVALUATION_OPENROAD_SUCCESS"
