#include "debug.h"
#include "mcp23s17.h"

void nop(void) { }

void id(void)
{
	write_string(BOARD_ID);
}

/* Handler for PING mode. Just responds with an ACK. */
void ping(void)
{
	ack();
}

/* Handler for INFO mode. Prints out several lines of info, with the last line being an ACK. */
void info(void)
{
	uint8_t info[BLOCK_SIZE] = { 0 };

	write_string(BOARD_ID);
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
	uint8_t buf[BLOCK_SIZE] = { TEST_BYTE };

	read_data((uint8_t *) &count, sizeof(count));
		
	ack();

	for(i=0; i<count; i+=sizeof(buf))
	{
		write_data((uint8_t *) &buf, sizeof(buf));
	}
}

/* Handler for GPIO test mode. */
void gpio(void)
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
				write_string("The specified GPIO action is not supported");
				break;
		}
	}
	
	mcp23s17_disable();

	return;
}
