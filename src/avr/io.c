#include <avr/io.h>

#include "common.h"
#include "mcp23s17.h"
#include "io.h"

void io(void)
{
	uint8_t loop = TRUE;
	struct io cmd = { 0 };

	mcp23s17_enable();

	while(loop)
	{
		read_data((uint8_t *) &cmd, sizeof(struct io));
		
		switch(cmd.action)
		{
			case HIGH:
				configure_pin_immediate(cmd.pin, 'w');
				set_pin_immediate(cmd.pin, 1);
				ack();
				break;
			case LOW:
				configure_pin_immediate(cmd.pin, 'w');
				set_pin_immediate(cmd.pin, 0);
				ack();
				break;
			case READ:
				configure_pin_immediate(cmd.pin, 'r');
				ack();
				putchar(get_pin(cmd.pin));
				break;
			case EXIT:
				loop = FALSE;
				ack();
				break;
			default:
				nack();
				printf("IO action %d is not supported\r\n", cmd.action);
				break;
		}
	}
	
	mcp23s17_disable();

	return;
}
