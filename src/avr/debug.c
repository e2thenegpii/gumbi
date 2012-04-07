#include "debug.h"

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

