# nyuzi MCMM scenario constraint. Units: ps (ASAP7 liberty time_unit).
# Generated from the delivered SDC: every clock is scaled from clk_period so
# the delivered period ratios survive compression.
set clk_period 1444
set clk_io_pct 0.2
current_design NyuziProcessor

set clk_io_pct 0.2

create_clock -name clk -period $clk_period [get_ports clk]

set_input_delay  [expr $clk_period * $clk_io_pct] -clock clk [all_inputs -no_clocks]
set_output_delay [expr $clk_period * $clk_io_pct] -clock clk [all_outputs]

set_false_path -from [get_ports reset]

# ISPD27: m_aclk is clk forwarded to an output port. The clock network is not sizable, so it is not a timed data path.
set_false_path -to [get_ports m_aclk]


# Contest section 3.1: input port transition and output port capacitance.
set io_slew_ps 20
set_input_transition $io_slew_ps [all_inputs]
set io_load_ff 2
set_load $io_load_ff [all_outputs]

set_clock_uncertainty -setup 0 [all_clocks]
set_clock_uncertainty -hold 50 [all_clocks]

# ISPD27: hold is not checked on paths that start at an input port or end at a hard-macro input.
set_false_path -hold -from [all_inputs -no_clocks]
set _macro_inputs [get_pins -quiet -of_objects [get_cells -quiet -hier -filter "ref_name =~ ht_asap7_*"] -filter "direction == input"]
if { [llength $_macro_inputs] > 0 } {
  set_false_path -hold -to $_macro_inputs
}
