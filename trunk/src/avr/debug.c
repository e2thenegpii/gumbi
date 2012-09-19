#include "debug.h"

/* Handler for NOP mode. Do nothing. */
void nop(void) { }

/* Handler for ID mode. Return the board ID string */
void id(void)
{
	fprintf(&gconfig.usb, "%s\n", BOARD_ID);
}

/* Handler for PING mode. Just responds with an ACK. */
void ping(void)
{
	ack();
}

/* Handler for SCANBUS mode. Checks the SPI bus for I/O expansion chips and responds with the number of available I/O pins. */
void scan_bus(void)
{
	mcp23s17_init();
	get_pin_count();
}

/* Explicitly sets the number of available I/O pins. Responds with the new pin count setting. */
void set_pin_count(void)
{
	read_data((uint8_t *) &gconfig.num_pins, sizeof(gconfig.num_pins));
	gconfig.num_io_devices = gconfig.num_pins / PINS_PER_DEVICE;
	get_pin_count();
}

/* Handler for PINCOUNT mode. Responds with the number of available I/O pins. */
void get_pin_count(void)
{
	fprintf(&gconfig.usb, "%c", gconfig.num_pins);
}

/* Handler for INFO mode. Prints out several lines of info, with the last line being an ACK. */
void info(void)
{
	uint8_t voltage = get_regulator();

	fprintf(&gconfig.usb, "Board ID: %s\n", BOARD_ID);
	fprintf(&gconfig.usb, "Firmware Version: %s\n", FIRMWARE_ID);
	fprintf(&gconfig.usb, "I/O Chip Count: %d\n", gconfig.num_io_devices);
	fprintf(&gconfig.usb, "I/O Pin Count: %d\n", gconfig.num_pins);
	fprintf(&gconfig.usb, "Voltage: %d.%dv\n", (voltage >> 4), (voltage & 0x0F));
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
		fprintf(&gconfig.usb, "%c", byte);
	}
}

/* Handler for XFER mode. Reads in XFER_TEST_SIZE bytes of data then sends it back out to the host. */
void xfer_test(void)
{
	uint32_t i = 0;
	uint8_t buf[XFER_TEST_SIZE] = { 0 };

	read_data((uint8_t *) &buf, sizeof(buf));

	for(i=0; i<sizeof(buf); i++)
	{
		fprintf(&gconfig.usb, "%c", buf[i]);
	}
}
