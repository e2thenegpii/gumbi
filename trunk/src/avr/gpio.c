#include "gpio.h"
#include "mcp23s17.h"

/* Handler for GPIO mode. */
void gpio(void)
{
	struct io cmd = { 0 };
	uint8_t loop = TRUE;

	mcp23s17_enable();

	while(loop)
	{
		read_data((uint8_t *) &cmd, sizeof(cmd));
		
		switch(cmd.action)
		{
			case HIGH:
				configure_pin_immediate(cmd.pin, 'w');
				set_pin_immediate(cmd.pin, 1);
				break;
			case LOW:
				configure_pin_immediate(cmd.pin, 'w');
				set_pin_immediate(cmd.pin, 0);
				break;
			case READ:
				configure_pin_immediate(cmd.pin, 'r');
				fputc(get_pin(cmd.pin), &gconfig.usb);
				break;
			case EXIT:
				loop = FALSE;
				break;
			default:
				nack();
				fprintf(&gconfig.usb, "The specified GPIO action is not supported [0x%X]\n", cmd.action);
				break;
		}

		/* Acknowledge that the command was processed */
		ack();
	}
	
	mcp23s17_disable();

	return;
}
