#include "spi.h"

void spi_flash(void)
{
	read_data((uint8_t *) &sconfig, sizeof(sconfig));
	
	mcp23s17_enable();

	configure_pin_as_input(sconfig.miso);
	configure_pin_as_output(sconfig.mosi);
	configure_pin_as_output(sconfig.ss);
	configure_pin_as_output(sconfig.clk);
	configure_pins_as_outputs(sconfig.vcc_pins, sconfig.num_vcc_pins);
	configure_pins_as_outputs(sconfig.gnd_pins, sconfig.num_gnd_pins);

	set_pins_high(sconfig.vcc_pins, sconfig.num_vcc_pins);
	set_pins_low(sconfig.gnd_pins, sconfig.num_gnd_pins);
	set_pin_high(sconfig.ss);
	
	commit_ddr_settings();
	commit_io_settings();

	switch(sconfig.action)
	{
		case READ:
			ack();
			read_spi_flash();
			break;
		case WRITE:
		default:
			nack();
			write_string("The specified action is not supported!");
	}

	mcp23s17_disable();
}

void read_spi_flash(void)
{
	uint32_t i = 0;
	uint8_t byte = 0;

	set_pin_immediate(sconfig.ss, 0);
	
	soft_spi_write(SPI_READ_COMMAND);
	soft_spi_write((uint8_t) (sconfig.addr >> 16));
	soft_spi_write((uint8_t) (sconfig.addr >> 8));
	soft_spi_write((uint8_t) (sconfig.addr));

	for(i=0; i<sconfig.count; i++)
	{	
		byte = soft_spi_read();
		buffered_write((uint8_t *) &byte, 1);
	}

	flush_buffer();

	set_pin_immediate(sconfig.ss, 1);
}

void soft_spi_write(uint8_t byte)
{
	uint8_t i = 0;

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(sconfig.clk, 0);
		set_pin_immediate(sconfig.mosi, (byte & (1 << i)));
		set_pin_immediate(sconfig.clk, 1);
	}

	set_pin_immediate(sconfig.clk, 0);
}

uint8_t soft_spi_read(void)
{
	uint8_t data = 0, i = 0;

	set_pin_immediate(sconfig.clk, 0);

	for(i=7; i>=0; i++)
	{
		set_pin_immediate(sconfig.clk, 1);
		if(get_pin(sconfig.miso))
		{
			data |= (1 << i);
		}
		set_pin_immediate(sconfig.clk, 0);
	}

	return data;
}
