#include <avr/io.h>

#include "common.h"
#include "parallel.h"
#include "io.h"
#include "command.h"

void ping(void)
{
	ack();
}

void debug(void)
{
	printf("Address: 0x%lx\r\n", gconfig->addr);
	printf("Count: %ld\r\n", gconfig->count);
	printf("Number of address pins: %d\r\n", gconfig->num_addr_pins);
	printf("Number of data pins: %d\r\n", gconfig->num_data_pins);
	printf("Number of Vcc pins: %d\r\n", gconfig->num_vcc_pins);
	printf("Number of ground pins: %d\r\n", gconfig->num_gnd_pins);
	printf("Configuration valid: %d\r\n", validate_gconfig());
	ack();
}

void speed_test(void)
{
	uint32_t i = 0;

	for(i=0; i<gconfig->count; i++)
	{
		putchar('A');
	}
	printf("\r\n");
	ack();
}

void command_handler(struct command *cmd)
{
	/* Point the global gconfig to the configuration data passed from the PC */
	gconfig = &cmd->configuration;

	switch(cmd->mode)
	{
		case PING:
			ping();
			break;
		case DEBUG:
			debug();
			break;
		case SPEED:
			speed_test();
			break;
		case PFLASH:
			parallel_flash();
			break;
		case IO:
			io();
			break;
		case SPIFLASH:
		case SPIEEPROM:
		case I2CEEPROM:
		default:
			printf("Command not implemented!\r\n");
			nack();
			break;
	}
	
	gconfig = NULL;
	return;
}
