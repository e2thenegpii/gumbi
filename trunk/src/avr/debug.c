#include "debug.h"
#include "mcp23s17.h"

void nop(void) { }

void id(void)
{
	printf("%s\r\n\r\n", BOARD_ID);
}

/* Handler for PING mode. Just responds with an ACK. */
void ping(void)
{
	ack();
}

/* Handler for INFO mode. Prints out several lines of info, with the last line being an ACK. */
void info(void)
{
	printf("Board ID: %s\r\n", BOARD_ID);
	printf("Number of I/O chips: %d\r\n", gconfig.num_io_devices);
	printf("Available I/O pins: %d\r\n", gconfig.num_pins);
	ack();
	printf("\r\n");
}

/* Handler for SPEED mode. Reads in a 4 byte size field, then prints out that many bytes of data. */
void speed_test(void)
{
	uint32_t i = 0, count = 0;

	read_data((uint8_t *) &count, sizeof(count));
		
	ack();

	for(i=0; i<count; i++)
	{
		putchar('A');
	}
}

/* Handler for IO test mode. */
void io(void)
{
	uint8_t loop = TRUE;
	struct io cmd = { 0 };

	mcp23s17_enable();

	while(loop)
	{
		read_data((uint8_t *) &cmd, sizeof(struct io));
		
		switch(cmd.action)
		{
			case HIGH:
				configure_pin_immediate(cmd.pin, 'w');
				set_pin_immediate(cmd.pin, 1);
				ack();
				break;
			case LOW:
				configure_pin_immediate(cmd.pin, 'w');
				set_pin_immediate(cmd.pin, 0);
				ack();
				break;
			case READ:
				configure_pin_immediate(cmd.pin, 'r');
				ack();
				putchar(get_pin(cmd.pin));
				break;
			case EXIT:
				loop = FALSE;
				ack();
				break;
			default:
				nack();
				printf("IO action %d is not supported\r\n", cmd.action);
				break;
		}
	}
	
	mcp23s17_disable();

	return;
}