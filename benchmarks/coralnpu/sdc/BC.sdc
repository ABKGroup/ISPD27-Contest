# coralnpu MCMM scenario constraint. Units: ps (ASAP7 liberty time_unit).
# Generated from the delivered SDC: every clock is scaled from clk_period so
# the delivered period ratios survive compression.
set clk_period 1358
set clk_io_pct 0.2
set_units -time ps -capacitance fF -resistance kOhm -voltage V -current mA -power pW
current_design CoralNPUChiselSubsystem
set_clock_gating_check -rise -setup 0
set_clock_gating_check -fall -setup 0
create_clock [get_ports {io_clk_i}] -name core_clock -period $clk_period -waveform [list 0.0 [expr $clk_period/2.0]]

# ISPD27: the SPI clock the delivered SDC leaves out. io_external_ports_5 is io_spi_clk of Spi2TLUL,
# which reaches the core only through async queues.
create_clock [get_ports {io_external_ports_5}] -name spi_clk -period [expr $clk_period*10] -waveform [list 0.0 [expr $clk_period*10/2.0]]
set_clock_groups -name ispd27_async -asynchronous -group [get_clocks {core_clock}] -group [get_clocks {spi_clk}]


# The delivered SDC constrains no IO. Add the virtual IO clock so the
# boundary paths are timed, matching the reference benchmark template.
set clk_io_name vclk_io
create_clock -name $clk_io_name -period $clk_period
set non_clock_inputs [all_inputs -no_clocks]
set_input_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name $non_clock_inputs
set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_io_name [all_outputs]
# ISPD27: vclk_io times the IO of core_clock only. The SPI clock stays asynchronous.
set_clock_groups -name ispd27_vclk_io -asynchronous -group [get_clocks {core_clock vclk_io}] -group [get_clocks {spi_clk}]

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
