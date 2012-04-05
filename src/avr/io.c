#include <avr/io.h>

#include "common.h"
#include "mcp23s17.h"
#include "io.h"

void io(void)
{
	uint8_t loop = TRUE;
	struct io *cmd = NULL;
	uint16_t i = 0, data_size = sizeof(struct io);
	uint8_t data[sizeof(struct io)] = { 0 };

	if(!validate_gconfig())
	{
		printf("Invalid configuration data\r\n");
		nack();
	}
	else
	{
		mcp23s17_enable();

		configure_pins_as_inputs(gconfig->addr_pins, gconfig->num_addr_pins);
		configure_pins_as_outputs(gconfig->data_pins, gconfig->num_data_pins);
		configure_pins_as_outputs(gconfig->vcc_pins, gconfig->num_vcc_pins);
		configure_pins_as_outputs(gconfig->gnd_pins, gconfig->num_gnd_pins);
		commit_ddr_settings();

		set_pins_high(gconfig->vcc_pins, gconfig->num_vcc_pins);
		set_pins_low(gconfig->gnd_pins, gconfig->num_gnd_pins);
		commit_io_settings();

		ack();

		while(loop)
		{
			for(i=0; i<data_size; i++)
			{
				data[i] = getchar();
			}

			cmd = (struct io *) &data;

			switch(cmd->action)
			{
				case WRITE:
					set_pin_immediate(&cmd->p, cmd->p.active);
					break;
				case READ:
					putchar(get_pin(&cmd->p));
					break;
				case EXIT:
					loop = FALSE;
					break;
				default:
					break;
			}
		}
	
		mcp23s17_disable();
	}

	return;
}
