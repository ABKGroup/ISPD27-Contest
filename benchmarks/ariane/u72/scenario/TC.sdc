# ariane MCMM scenario constraint. Units: ps (ASAP7 liberty time_unit).
# Generated from the delivered SDC: every clock is scaled from clk_period so
# the delivered period ratios survive compression.
set clk_period 3736
set clk_io_pct 0.2
###############################################################
#  Design:            ariane
###############################################################
set_units -time ps -capacitance fF -resistance kOhm -voltage V -current mA -power pW
current_design ariane
set_clock_gating_check -rise -setup 0
set_clock_gating_check -fall -setup 0
create_clock [get_ports {clk_i}] -name core_clock -period $clk_period -waveform [list 0.0 [expr $clk_period/2.0]]


# The delivered SDC constrains no IO. Add the virtual IO clock so the
# boundary paths are timed, matching the reference benchmark template.
set clk_io_name vclk_io
create_clock -name $clk_io_name -period $clk_period
set non_clock_inputs [all_inputs -no_clocks]
set_input_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name $non_clock_inputs
set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name [all_outputs]
# Contest section 3.1: input port transition and output port capacitance.
set io_slew_ps 20
set_input_transition $io_slew_ps [all_inputs]
set io_load_ff 2
set_load $io_load_ff [all_outputs]


set_clock_uncertainty -setup 0 [all_clocks]
set_clock_uncertainty -hold 50 [all_clocks]
