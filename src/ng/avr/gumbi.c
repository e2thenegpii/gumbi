#include <avr/io.h>
#include <util/delay.h>
#include <avr/power.h>
#include "gumbi.h"
#include "debug.h"
#include "mcp23s17.h"
#include "parallel.h"
#include "spi.h"

int main(void)
{
	uint8_t mode = 0;

	/* Disable watchdog if enabled by bootloader/fuses */
	MCUSR &= ~(1 << WDRF);
	wdt_disable();

	/* Full speed clock */
	clock_prescale_set(clock_div_1);

	/* Set LED pin as output */
	DDRD |= (1 << PD5);

	while(1)
	{
		PORTD |= (1 << PD5);
		_delay_ms(1000);
		PORTD &= ~(1 << PD5);
		_delay_ms(1000);
	}

	/* Make sure the entire gconfig structure is zeroed out */
	memset(&gconfig, 0, sizeof(gconfig));

	/* Initialize the MCP23S17 chips */	
	mcp23s17_init();

	/* Initialize USB */
	usb_init();
	while(!usb_configured()) { }
	_delay_ms(1000);

	/* Turn on the LED to show that we're alive */
	PORTD &= ~(1 << PD5);

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
#ifdef DEBUG
		case PING:
			handler = &ping;
			break;
		case INFO:
			handler = &info;
			break;
		case SPEEDTEST:
			handler = &speed_test;
			break;
		case XFER:
			handler = &xfer_test;
			break;
		case GID:
			handler = &id;
			break;
#endif
		case PFLASH:
			handler = &parallel_flash;
			break;
		case SPIFLASH:
			handler = &spi_flash;
			break;
		case GPIO:
			handler = &gpio;
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
		/* If the specified mode is unknown/unsupported, send a NACK */
		nack();
	}

	return;
}
