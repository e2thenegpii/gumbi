#include <avr/io.h>
#include <string.h>

#include "common.h"
#include "gumbi.h"
#include "mcp23s17.h"
#include "parallel.h"
#include "io.h"

int main(void)
{
	uint8_t mode = 0;

	/* Make sure the entire gconfig structure is zeroed out */
	memset(&gconfig, 0, sizeof(gconfig));

	/* Initialize the MCP23S17 chips */	
	mcp23s17_init();

	/* Initialize UART comms with the PC */
	uart_init();
	dup2uart();

	printf("%s\r\n", BOARD_ID);

	while(TRUE)
	{
		mode = getchar();
		command_handler(mode);
	}

	return 0;
}

void ping(void)
{
	ack();
}

void info(void)
{
	printf("Number of I/O chips: %d\r\n", gconfig.num_io_devices);
	printf("Available I/O pins: %d\r\n", gconfig.num_pins);
	ack();
}

void speed_test(void)
{
	uint8_t *data = NULL;
	uint32_t i = 0, count = 0, data_size = sizeof(uint32_t);

	data = read_data(data_size);
	if(data)
	{
		count = (uint32_t) *data;

		for(i=0; i<count; i++)
		{
			putchar('A');
		}
		printf("\r\n");
		
		free(data);
	}
}

void command_handler(uint8_t mode)
{
	void (*handler)(void);

	handler = NULL;

	switch(mode)
	{
		case PING:
			handler = &ping;
			break;
		case INFO:
			handler = &info;
			break;
		case SPEED:
			handler = &speed_test;
			break;
		case PFLASH:
			handler = &parallel_flash;
			break;
		case IO:
			handler = &io;
			break;
		case SPIFLASH:
		case SPIEEPROM:
		case I2CEEPROM:
		default:
			break;
	}

	if(handler)
	{
		ack();
		handler();
	}
	else
	{
		printf("Mode not implemented!\r\n");
		nack();
	}

	return;
}
