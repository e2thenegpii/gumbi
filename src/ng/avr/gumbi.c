#include "common.h"
#include "gumbi.h"
#include "debug.h"
#include "mcp23s17.h"
#include "parallel.h"
#include "spi.h"

int main(void)
{
	uint8_t mode = 0;

	/* Make sure the entire gconfig structure is zeroed out */
	memset(&gconfig, 0, sizeof(gconfig));

	/* Initialize the MCP23S17 chips */	
	mcp23s17_init();

	/* Full speed clock */
	clock_prescale_set(0);

	/* Initialize USB */
	usb_init();
	while(!usb_configured()) { }
	_delay_ms(1000);

	/* Show that we're alive and ready */
	//id();

	while(TRUE)
	{
		read_data((uint8_t *) &mode, 1);
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
		case SPEEDTEST:
			handler = &speed_test;
			break;
		case PFLASH:
			handler = &parallel_flash;
			break;
		case SPIFLASH:
			handler = &spi_flash;
			break;
		case GPIO:
			handler = &gpio;
			break;
		case GID:
			handler = &id;
			break;
		case NOP:
			handler = &nop;
			break;
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
		write_string("Specified mode not implemented!");
	}

	return;
}
