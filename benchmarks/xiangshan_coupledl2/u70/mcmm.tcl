# ISPD27 MCMM configuration for xiangshan_coupledl2__u70.
#
# Modes, PVT corners and mode-corner scenes for timing analysis, in the
# same order and with the same commands the evaluation flow uses, so a
# run here matches the one that scores a submission.
#
#   BC   FF  0.77 V    0 C
#   TC   TT  0.70 V   25 C
#   WC   SS  0.63 V  100 C
#
# Units are ps, fF and um. One nominal interconnect RC model serves all
# three cell PVT scenes, which is the platform policy, not a shortcut.
#
# The macro abstracts are characterised at a single corner, so the same
# macro library appears in all three scenes. The standard cells have a
# separate library set per corner.
#
# Call order, because read_sdc needs a design and define_scene needs the
# libraries:
#     source mcmm.tcl
#     ispd27_read_libraries
#     read_def <your>.def          ;# or the released input.def
#     ispd27_define_scenes

# This file sits in the design directory, so its own directory is the
# design directory and the release root is one level above. Adding a
# ".." to the first of those put every path one level too high and the
# first read_lef failed on /home/jal216/common instead of the release.
set ispd27_design_dir [file normalize [file dirname [info script]]]
set ispd27_root [file normalize [file join $ispd27_design_dir .. .. ..]]

proc ispd27_read_libraries {} {
    global ispd27_root ispd27_corner_libs ispd27_macro_libs
    foreach lef {
        platform/asap7/lef/asap7_tech_1x_260907.lef
        platform/asap7/lef/asap7sc7p5t_28_R_1x_220121a.lef
        platform/asap7/lef/asap7sc7p5t_28_L_1x_220121a.lef
        platform/asap7/lef/asap7sc7p5t_28_SL_1x_220121a.lef
    } { read_lef [file join $ispd27_root $lef] }
    foreach lef {
        platform/xiangshan_coupledl2/lef/array_2048x137_bk.lef
        platform/xiangshan_coupledl2/lef/array_256x104.lef
        platform/xiangshan_coupledl2/lef/array_256x13.lef
        platform/xiangshan_coupledl2/lef/array_256x16.lef
        platform/xiangshan_coupledl2/lef/array_256x164.lef
        platform/xiangshan_coupledl2/lef/array_256x8_0.lef
    } { read_lef [file join $ispd27_root $lef] }
    set ispd27_corner_libs(BC) [list \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_RVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_RVT_FF_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_RVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_LVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_LVT_FF_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_LVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_LVT_FF_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_LVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_SLVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_SLVT_FF_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_SLVT_FF_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_SLVT_FF_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_SLVT_FF_nldm_211120.lib.gz]]
    set ispd27_corner_libs(TC) [list \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_RVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_RVT_TT_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_RVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_RVT_TT_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_RVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_LVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_LVT_TT_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_LVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_LVT_TT_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_LVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_SLVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_SLVT_TT_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_SLVT_TT_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_SLVT_TT_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_SLVT_TT_nldm_211120.lib.gz]]
    set ispd27_corner_libs(WC) [list \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_RVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_RVT_SS_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_RVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_RVT_SS_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_LVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_LVT_SS_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_LVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_LVT_SS_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_LVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_AO_SLVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_INVBUF_SLVT_SS_nldm_220122.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_OA_SLVT_SS_nldm_211120.lib.gz] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SEQ_SLVT_SS_nldm_220123.lib] \
        [file join $ispd27_root platform/asap7/lib/NLDM/asap7sc7p5t_SIMPLE_SLVT_SS_nldm_211120.lib.gz]]
    set ispd27_macro_libs [list \
        [file join $ispd27_root platform/xiangshan_coupledl2/lib/array_2048x137_bk.lib.gz] \
        [file join $ispd27_root platform/xiangshan_coupledl2/lib/array_256x104.lib.gz] \
        [file join $ispd27_root platform/xiangshan_coupledl2/lib/array_256x13.lib.gz] \
        [file join $ispd27_root platform/xiangshan_coupledl2/lib/array_256x16.lib.gz] \
        [file join $ispd27_root platform/xiangshan_coupledl2/lib/array_256x164.lib.gz] \
        [file join $ispd27_root platform/xiangshan_coupledl2/lib/array_256x8_0.lib.gz]]
    foreach corner {BC TC WC} {
        foreach lib [concat $ispd27_corner_libs($corner) $ispd27_macro_libs] {
            read_liberty $lib
        }
    }
}

proc ispd27_define_scenes {} {
    global ispd27_design_dir ispd27_corner_libs ispd27_macro_libs
    foreach corner {BC TC WC} {
        set mode functional_$corner
        read_sdc -mode $mode [file join $ispd27_design_dir scenario ${corner}.sdc]
        set_mode $mode
        # Post-CTS timing uses the synthesized tree, so every real clock
        # is propagated. A virtual clock has no network to propagate.
        foreach clk [all_clocks] {
            if {![get_property $clk is_virtual]} {
                set_propagated_clock $clk
            }
        }
        define_scene $corner -mode $mode \
            -liberty [concat $ispd27_corner_libs($corner) $ispd27_macro_libs]
    }
}
