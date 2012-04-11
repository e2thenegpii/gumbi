#include "common.h"

/* Send an ACK. */
void ack(void)
{
	write_string(ACK);
}

/* Send a NACK. */
void nack(void)
{
	write_string(NACK);
}

/* Read size bytes of data into buffer from USB HID endpoint */
void read_data(uint8_t *buffer, uint32_t size)
{
	uint32_t i = 0;
	uint8_t r = 0, n = 0;
	uint8_t rx_buf[BLOCK_SIZE] = { 0 };

	for(i=0,r=0; i<size; i+=n)
	{
		r = usb_rawhid_recv((uint8_t *) &rx_buf, 0);
		if(r > 0)
		{
			if((i+r) > size)
			{
				n = size - i;
			}
			else
			{
				n = r;
			}

			memcpy(buffer+i, (void *) &rx_buf, n);
		}
		else
		{
			r = 0;
		}
	}
}

/* Send size bytes of data from buffer to USB HID endpoint */
void write_data(uint8_t *buffer, uint32_t size)
{
	uint32_t i = 0, n = 0;
	uint8_t tx_buf[BLOCK_SIZE] = { 0 };

	for(i=0; i<size; i+=n)
	{
		memset((void *) &tx_buf, 0, sizeof(tx_buf));
		
		if((size-i) >= BLOCK_SIZE)
		{
			n = BLOCK_SIZE;
		}
		else
		{
			n = size - i;
		}
		
		memcpy((void *) &tx_buf, buffer+i, n);
		usb_rawhid_send((uint8_t *) &tx_buf, 50);
	}
}

/* Flushes the contents of the global buffer used by buffered_write() */
void flush_buffer(void)
{
	if(gconfig.buffer_size > 0)
	{
		write_data((uint8_t *) &gconfig.buffer, gconfig.buffer_size);
	}

	memset((void *) &gconfig.buffer, 0, BLOCK_SIZE);
	gconfig.buffer_size = 0;
}

/* Buffers transmitted data into BLOCK_SIZE data chunks */
void buffered_write(uint8_t *buffer, uint32_t size)
{
	uint32_t i = 0;

	for(i=0; i<size; i++)
	{
		gconfig.buffer[gconfig.buffer_size++] = buffer[i];

		if(gconfig.buffer_size == BLOCK_SIZE)
		{
			flush_buffer();
		}
	}
}

/* Wrapper function for writing strings. Strings must be <= BLOCK_SIZE bytes. */
void write_string(char *string)
{
	uint8_t size = 0;

	if(string != NULL)
	{
		size = strlen(string);
		if(size > BLOCK_SIZE)
		{
			size = BLOCK_SIZE;
		}
		write_data((uint8_t *) string, size);
	}
}

/* Check if the specified pin number is a valid pin. Returns TRUE if valid, FALSE if invalid. */
uint8_t is_valid_pin(uint8_t p)
{
	uint8_t ok = FALSE;

	if(p > 0 && p < gconfig.num_pins && gconfig.pins[p].inuse)
	{
		ok = TRUE;
	}

	return ok;
}

/* Check if an array of pin numbers are all valid. Returns FALSE if one or more pins in the array are not valid. */
uint8_t are_valid_pins(uint8_t pins[], uint8_t count)
{
	uint8_t i = 0, ok = TRUE;

	for(i=0; i<count; i++)
	{
		if(!is_valid_pin(pins[i]))
		{
			ok = FALSE;
			break;
		}
	}

	return ok;
}

/* Validate pin arrays in pconfig. Control pins are not validated here. */
uint8_t validate_pconfig(void)
{
	uint8_t ok = TRUE;

	ok &= are_valid_pins(pconfig.addr_pins, pconfig.num_addr_pins);
	ok &= are_valid_pins(pconfig.data_pins, pconfig.num_data_pins);
	ok &= are_valid_pins(pconfig.vcc_pins, pconfig.num_vcc_pins);
	ok &= are_valid_pins(pconfig.gnd_pins, pconfig.num_gnd_pins);

	return ok;
}
