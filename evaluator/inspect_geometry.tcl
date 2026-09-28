# Read an ODB only to measure generated geometry; no timing or optimization.
if {[info exists ::env(INSPECT_DB)]} { read_db $::env(INSPECT_DB) }
set block [ord::get_db_block]
set dbu [$block getDbUnitsPerMicron]
set core [$block getCoreArea]
set die [$block getDieArea]
set core_area [expr {double([$core dx])*[$core dy]/$dbu/$dbu}]
set die_area [expr {double([$die dx])*[$die dy]/$dbu/$dbu}]
set area 0.0
set cells 0
foreach inst [$block getInsts] {
    set master [$inst getMaster]
    set functional 0
    foreach pin [$master getMTerms] {
        if {[$pin getSigType] ni {POWER GROUND}} { set functional 1; break }
    }
    if {!$functional} { continue }
    incr cells
    set area [expr {$area + double([$master getWidth])*[$master getHeight]/$dbu/$dbu}]
}
set f [open $::env(INSPECT_OUTPUT) w]
puts $f [format {{"core_area_um2": %.9f, "die_area_um2": %.9f, "functional_cell_area_um2": %.9f, "functional_instances": %d, "functional_utilization_percent": %.9f, "dbu_per_um": %d}} $core_area $die_area $area $cells [expr {100*$area/$core_area}] $dbu]
close $f
