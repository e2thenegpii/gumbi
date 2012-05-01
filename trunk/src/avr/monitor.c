#include "monitor.h"

/* Read from all pins and stream data back to the host n number of times */
void monitor(void)
{
	uint32_t i = 0, count = 0;
	uint8_t j = 0, gpioa = 0, gpiob = 0;

	mcp23s17_enable();

	while(TRUE)
	{
		read_data((uint8_t *) &count, 4);

		if(count == 0)
		{
			ack();
			break;
		}

		for(i=0; i<count; i++)
		{
			for(j=0; j<gconfig.num_io_devices; j++)
			{
				gpioa = read_register(j, GPIOA);
				gpiob = read_register(j, GPIOB);

				buffered_write((uint8_t *) &gpioa, 1);
				buffered_write((uint8_t *) &gpiob, 1);
			}
		}

		flush_buffer();
	}

	mcp23s17_disable();
}
