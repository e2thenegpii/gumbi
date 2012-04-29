#include "gpio.h"
#include "mcp23s17.h"

/* Handler for GPIO mode. */
void gpio(void)
{
	uint8_t rx[BLOCK_SIZE] = { 0 };
	uint8_t loop = TRUE, do_stream = FALSE, i = 0, index = 0;

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
				case STREAM:
					do_stream = TRUE;
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

		/* If the STREAM action was specified, call read_stream. We won't be returning from this. */
		if(do_stream)
		{
			read_stream();
		}
	}
	
	mcp23s17_disable();

	return;
}

/* Read from all pins and stream data back to the host indefinitely */
void read_stream(void)
{
	uint8_t i = 0, gpioa = 0, gpiob = 0;

	while(TRUE)
	{
		for(i=0; i<gconfig.num_io_devices; i++)
		{
			gpioa = read_register(i, GPIOA);
			gpiob = read_register(i, GPIOB);
			
			buffered_write((uint8_t *) &gpioa, 1);
			buffered_write((uint8_t *) &gpiob, 1);
		}
	}	
}
