#include "common.h"
#include "gumbi.h"
#include "debug.h"
#include "mcp23s17.h"
#include "parallel.h"
#include "spi.h"
#include "i2c.h"

int main(void)
{
	uint8_t mode = 0;

	/* By default, the DIV8 fuse is set. Change it to use the full clock speed. */
	clock_prescale_set(clock_div_1);

	/* Initialize LED pin(s) */
	led_init();

	/* Make sure the entire gconfig structure is zeroed out */
	memset(&gconfig, 0, sizeof(gconfig));

	/* Initialize the MCP23S17 chips */	
	mcp23s17_init();

	/* Initialize USB */
	usb_init();
	while(!usb_configured()) { }
	_delay_ms(1000);

	/* Show that we're alive and ready */
	led_on();

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
		case PARALLEL:
			handler = &parallel;
			break;
		case SPIFLASH:
			handler = &spi_flash;
			break;
		case SPIEEPROM:
			handler = &spi_eeprom;
			break;
		case I2CEEPROM:
			handler = &i2c_eeprom;
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
		case XFER:
			handler = &xfer_test;
			break;
		case PINCOUNT:
			handler = &pin_count;
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
