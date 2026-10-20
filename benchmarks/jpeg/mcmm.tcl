# Source after PLATFORM_DIR is set. Paths are relative to this benchmark.
set mcmm_directory [file dirname [file normalize [info script]]]
set mcmm_functional_mode functional
set mcmm_corners {BC TC WC}
set mcmm_checks {setup hold}
set mcmm_rc_file [file join $::env(PLATFORM_DIR) util setRC.tcl]
set mcmm_propagated_clocks 1
set mcmm_additional_ocv_derating 0
# Independent SDC contexts express corner-dependent functional requirements.
foreach corner $mcmm_corners {
    set scenario_mode($corner) functional_$corner
    set scenario_sdc($corner) [file join $mcmm_directory sdc ${corner}.sdc]
}
# Library file lists are defined in PLATFORM_DIR/util/libraries.tcl.
