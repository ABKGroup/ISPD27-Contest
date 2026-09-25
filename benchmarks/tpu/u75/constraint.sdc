# tpu MCMM scenario constraint. Units: ps (ASAP7 liberty time_unit).
# Generated from the delivered SDC: every clock is scaled from clk_period so
# the delivered period ratios survive compression.
set clk_period 1920
set clk_io_pct 0.2
###############################################################
#  Design:            tpu
###############################################################
set_units -time ps -capacitance fF -resistance kOhm -voltage V -current mA -power pW
current_design tpu
set_clock_gating_check -rise -setup 0
set_clock_gating_check -fall -setup 0
#create_clock [get_ports {clk}] -name core_clock -period 1000.000000 -waveform {0.000000 500.000000}
create_clock [get_ports {clk}] -name core_clock -period $clk_period -waveform [list 0.0 [expr $clk_period/2.0]]


set_clock_uncertainty -setup 0 [all_clocks]
set_clock_uncertainty -hold 0 [all_clocks]
