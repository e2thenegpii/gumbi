#include "debug.h"

/* Handler for NOP mode. Do nothing. */
void nop(void) { }

/* Handler for ID mode. Return the board ID string */
void id(void)
{
	write_string(BOARD_ID);
}

/* Handler for PING mode. Just responds with an ACK. */
void ping(void)
{
	ack();
}

/* Handler for PINCOUNT mode. Responds with the number of available I/O pins. */
void pin_count(void)
{
	write_data((void *) &gconfig.num_pins, sizeof(gconfig.num_pins));
}

/* Handler for INFO mode. Prints out several lines of info, with the last line being an ACK. */
void info(void)
{
	uint8_t info[BLOCK_SIZE] = { 0 };

	snprintf((void *) &info, BLOCK_SIZE, "Board ID: %s", BOARD_ID);
	write_string((char *) &info);
	snprintf((void *) &info, BLOCK_SIZE, "I/O Chip Count: %d", gconfig.num_io_devices);
	write_string((char *) &info);
	snprintf((void *) &info, BLOCK_SIZE, "I/O Pin Count: %d", gconfig.num_pins);
	write_string((char *) &info);
	ack();
}

/* Handler for SPEED mode. Reads in a 4 byte size field, then prints out that many bytes of data. */
void speed_test(void)
{
	uint32_t i = 0, count = 0;
	uint8_t byte = DUMMY_BYTE;

	read_data((uint8_t *) &count, sizeof(count));

	for(i=0; i<count; i++)
	{
		buffered_write((uint8_t *) &byte, 1);
	}
	
	flush_buffer();
}

/* Handler for XFER mode. Reads in a 4 byte size field, reads in size data while sending it back out to the host. */
void xfer_test(void)
{
	uint8_t buf[XFER_TEST_SIZE] = { 0 };

	read_data((uint8_t *) &buf, sizeof(buf));
	buffered_write((uint8_t *) &buf, sizeof(buf));
	flush_buffer();
}
