#include <avr/io.h>

#include "common.h"
#include "mcp23s17.h"
#include "io.h"

void io(void)
{
	uint8_t loop = TRUE;
	struct io *cmd = NULL;
	uint16_t data_size = sizeof(struct io);

	mcp23s17_enable();

	while(loop)
	{
		cmd = (struct io *) read_data(data_size);
		if(cmd)
		{
			switch(cmd->action)
			{
				case WRITE:
					set_pin_immediate(cmd->pin, gconfig.pins[cmd->pin].active);
					break;
				case READ:
					putchar(get_pin(cmd->pin));
					break;
				case EXIT:
					loop = FALSE;
					break;
				default:
					break;
			}

			free(cmd);
		}
	}
	
	mcp23s17_disable();

	return;
}
