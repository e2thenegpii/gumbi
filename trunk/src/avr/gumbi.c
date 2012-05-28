#include "common.h"
#include "gumbi.h"
#include "serial.h"
#include "mcp23s17.h"
#include "debug.h"
#include "parallel.h"
#include "gpio.h"
#include "monitor.h"
#include "regulator.h"

int main(void)
{
	uint8_t mode = 0;

	/* Ensure watchdog is disabled */
	MCUSR &= ~(1 << WDRF);
	wdt_disable();

	/* By default, the DIV8 fuse is set. Change it to use the full clock speed. */
	clock_prescale_set(clock_div_1);

	/* Initialize LED pin(s) */
	led_init();

	/* Initialize voltage regulators */
	regulator_init();

	/* Make sure the entire gconfig structure is zeroed out */
	memset(&gconfig, 0, sizeof(gconfig));

	/* Initialize virtual serial port */
	serial_init();

	/* Initialize the MCP23S17 chips */	
	mcp23s17_init();

	/* If we were unable to identify the minimum number of I/O chips, blink the status LED and keep trying */
	while(gconfig.num_io_devices < MIN_DEVICES)
	{
		led_on();
		_delay_ms(500);
		led_off();
		_delay_ms(500);
		
		mcp23s17_init();
	}

	/* Show that we're alive and ready */
	led_on();

	while(TRUE)
	{
		read_data((uint8_t *) &mode, sizeof(mode));
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
		case GETPINCOUNT:
			handler = &get_pin_count;
			break;
		case SETPINCOUNT:
			handler = &set_pin_count;
			break;
		case SCANBUS:
			handler = &scan_bus;
			break;
		case MONITOR:
			handler = &monitor;
			break;
		case VOLTAGE:
			handler = &voltage;
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
