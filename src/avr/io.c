#include <avr/io.h>

#include "common.h"
#include "mcp23s17.h"
#include "io.h"

void io(void)
{
	if(!validate_gconfig())
	{
		printf("Invalid configuration data\r\n");
		nack();
	}
	else
	{
		mcp23s17_init();

		configure_pins_as_inputs(gconfig->addr_pins, gconfig->num_addr_pins);
		configure_pins_as_outputs(gconfig->data_pins, gconfig->num_data_pins);
		configure_pins_as_outputs(gconfig->vcc_pins, gconfig->num_vcc_pins);
		configure_pins_as_outputs(gconfig->gnd_pins, gconfig->num_gnd_pins);

		set_pins_high(gconfig->vcc_pins, gconfig->num_vcc_pins);
		set_pins_low(gconfig->gnd_pins, gconfig->num_gnd_pins);

		commit_ddr_settings();
		commit_io_settings();

		ack();
	
	//	mcp23s17_disable();
	}

	return;
}
