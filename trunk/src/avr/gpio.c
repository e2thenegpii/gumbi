#include "gpio.h"
#include "mcp23s17.h"

/* Handler for GPIO mode. */
void gpio(void)
{
	uint8_t loop = TRUE, i = 0, index = 0;
	uint8_t rx[BLOCK_SIZE] = { 0 };

	mcp23s17_enable();

	while(loop)
	{
		read_data((uint8_t *) &hgpio, sizeof(hgpio));
		
		for(i=0; i<hgpio.num_cmd && i<MAX_GPIO_COMMANDS && loop; i++)
		{
			switch(hgpio.cmd[i].action)
			{
				case HIGH:
					configure_pin_immediate(hgpio.cmd[i].pin, 'w');
					set_pin_immediate(hgpio.cmd[i].pin, 1);
					break;
				case LOW:
					configure_pin_immediate(hgpio.cmd[i].pin, 'w');
					set_pin_immediate(hgpio.cmd[i].pin, 0);
					break;
				case READ:
					configure_pin_immediate(hgpio.cmd[i].pin, 'r');
					rx[index++] = get_pin(hgpio.cmd[i].pin);
					break;
				case EXIT:
					loop = FALSE;
					break;
				default:
					nack();
					write_string("The specified GPIO action is not supported");
					break;
			}
		}

		/* Acknowledge that the data block has been processed */
		ack();

		/* If any data was read in, send it back to the host */
		if(index > 0)
		{
			write_data((uint8_t *) &rx, index);
			index = 0;
		}
	}
	
	mcp23s17_disable();

	return;
}
