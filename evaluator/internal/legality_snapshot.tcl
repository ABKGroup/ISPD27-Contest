# Snapshots use OpenDB's DEF writer so input whitespace and statement order do
# not determine legality. No contestant-supplied script is executed here.
proc legality_field {value} {
    if {[regexp {[\t\r\n]} $value]} { error "Unsupported control character in design identifier" }
    return $value
}
proc legality_snapshot {prefix {catalog 0}} {
    write_def ${prefix}.def
    set cells [open ${prefix}.cells.tsv w]
    set pins [open ${prefix}.pins.tsv w]
    puts $cells "instance\tmaster\tx\ty\torientation\tstatus\tmacro\tphysical"
    puts $pins "instance\tpin\tdirection\tsignal\tnet\tnet_signal"
    foreach inst [[ord::get_db_block] getInsts] {
        set master [$inst getMaster]
        set physical 1
        foreach p [$master getMTerms] {
            if {[$p getSigType] ni {POWER GROUND}} {set physical 0}
        }
        lassign [$inst getLocation] x y
        puts $cells [join [list [legality_field [$inst getName]] [$master getName] $x $y \
            [$inst getOrient] [$inst getPlacementStatus] [$master isBlock] $physical] "\t"]
        foreach p [$inst getITerms] {
            set m [$p getMTerm]; set net [$p getNet]; set name ""; set type ""
            if {$net ne "NULL"} {set name [legality_field [$net getName]]; set type [$net getSigType]}
            puts $pins [join [list [$inst getName] [$m getName] [$m getIoType] [$m getSigType] $name $type] "\t"]
        }
    }
    foreach p [[ord::get_db_block] getBTerms] {
        set net [$p getNet]; set name ""; set type ""
        if {$net ne "NULL"} {set name [legality_field [$net getName]]; set type [$net getSigType]}
        puts $pins [join [list "" [legality_field [$p getName]] [$p getIoType] [$p getSigType] $name $type] "\t"]
    }
    close $cells; close $pins
    if {$catalog} {
        set f [open ${prefix}.library.tsv w]
        puts $f "master\tpin\tdirection\tfunction\ttristate\tbuffer\tinverter"
        foreach cell [get_lib_cells *] {
            foreach pin [$cell find_liberty_ports_matching * 0 0] {
                puts $f [join [list [$cell name] [$pin name] [get_property $pin direction] \
                    [$pin function] [$pin tristate_enable] [$cell is_buffer] [$cell is_inverter]] "\t"]
            }
        }
        close $f
    }
}
