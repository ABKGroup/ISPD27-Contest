# Source after PLATFORM_DIR is set. Paths are relative to this benchmark.
set mcmm_directory [file dirname [file normalize [info script]]]
set mcmm_functional_mode functional
set mcmm_corners {BC TC WC}
set mcmm_scenes {TC BC WC TC_test BC_test WC_test}
set mcmm_checks {setup hold}
set mcmm_rc_file [file join $::env(PLATFORM_DIR) util setRC.tcl]
set mcmm_propagated_clocks 1
set mcmm_additional_ocv_derating 0
# Functional mode (scan enable 0) and shift test mode (scan enable 1) on every corner.
foreach corner $mcmm_corners {
    set scenario_mode($corner) functional_$corner
    set scenario_sdc($corner) [file join $mcmm_directory sdc ${corner}.sdc]
    set scenario_corner($corner) $corner
    set scenario_mode(${corner}_test) test_$corner
    set scenario_sdc(${corner}_test) [file join $mcmm_directory sdc ${corner}_test.sdc]
    set scenario_corner(${corner}_test) $corner
}
# Library file lists are defined in PLATFORM_DIR/util/libraries.tcl.
