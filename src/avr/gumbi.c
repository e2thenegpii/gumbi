#include "gumbi.h"
#include "debug.h"
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

	/* Show that we're alive and ready */
	printf("%s\r\n", BOARD_ID);

	while(TRUE)
	{
		mode = getchar();
		command_handler(mode);
	}

	return 0;
}

/* Checks the specified mode and calls the appropriate handler function. */
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
		/* Always ACK if the specified mode was identified. */
		ack();
		handler();
	}
	else
	{
		/* If the specified mode is unknown/unsupported, send a NACK followed by a reason */
		nack();
		printf("Specified mode not implemented!\r\n");
	}

	return;
}
