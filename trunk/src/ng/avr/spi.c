#include "spi.h"

void spi_flash(void)
{
	soft_spi_init();

	switch(pconfig.action)
	{
		case READ:
			ack();
			read_spi_flash();
			break;
		case WRITE:
		default:
			nack();
			write_string("The specified SPI Flash action is not supported");
	}

	soft_spi_release();
}

void spi_eeprom(void)
{
	soft_spi_init();
	
	switch(pconfig.action)
	{
		case READ:
			ack();
			read_spi_eeprom();
			break;
		case WRITE:
		default:
			nack();
			write_string("The specified SPI EEPROM action is not supported");
	}

	soft_spi_release();
}

uint8_t validate_spi_config(void)
{
	uint8_t ok = TRUE;

	ok &= is_valid_pin(pconfig.clk);
	ok &= is_valid_pin(pconfig.ss);
	ok &= is_valid_pin(pconfig.mosi);
	ok &= is_valid_pin(pconfig.miso);
	ok &= are_valid_pins(pconfig.vcc_pins, pconfig.num_vcc_pins);
	ok &= are_valid_pins(pconfig.gnd_pins, pconfig.num_gnd_pins);

	return ok;
}

void soft_spi_init(void)
{
	read_data((uint8_t *) &pconfig, sizeof(pconfig));

	if(validate_spi_config())
	{
		ack();	
	
		mcp23s17_enable();

		configure_pin_as_input(pconfig.miso);
		configure_pin_as_output(pconfig.mosi);
		configure_pin_as_output(pconfig.ss);
		configure_pin_as_output(pconfig.clk);
		configure_pins_as_outputs(pconfig.vcc_pins, pconfig.num_vcc_pins);
		configure_pins_as_outputs(pconfig.gnd_pins, pconfig.num_gnd_pins);

		set_pins_high(pconfig.vcc_pins, pconfig.num_vcc_pins);
		set_pins_low(pconfig.gnd_pins, pconfig.num_gnd_pins);
		set_pin_high(pconfig.ss);
	
		commit_ddr_settings();
		commit_io_settings();
	}
	else
	{
		nack();
		write_string("Invalid pin configuration");
	}
}

void soft_spi_release(void)
{
	mcp23s17_disable();
}

void spi_dump(void)
{
	uint32_t i = 0;
	uint8_t byte = 0;

	for(i=0; i<pconfig.count; i++)
	{
		byte = soft_spi_read();
		buffered_write((uint8_t *) &byte, 1);
	}

	flush_buffer();
}

void read_spi_eeprom(void)
{
	set_pin_immediate(pconfig.ss, 0);

	soft_spi_write(SPI_READ_COMMAND);
	soft_spi_write((uint8_t) (pconfig.addr >> 8));
	soft_spi_write((uint8_t) (pconfig.addr));

	spi_dump();

	set_pin_immediate(pconfig.ss, 1);
}

void read_spi_flash(void)
{
	set_pin_immediate(pconfig.ss, 0);
	
	soft_spi_write(SPI_READ_COMMAND);
	soft_spi_write((uint8_t) (pconfig.addr >> 16));
	soft_spi_write((uint8_t) (pconfig.addr >> 8));
	soft_spi_write((uint8_t) (pconfig.addr));

	spi_dump();

	set_pin_immediate(pconfig.ss, 1);
}

void soft_spi_write(uint8_t byte)
{
	uint8_t i = 0;

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(pconfig.clk, 0);
		set_pin_immediate(pconfig.mosi, ((byte & (1 << i)) >> i));
		set_pin_immediate(pconfig.clk, 1);
	}

	set_pin_immediate(pconfig.clk, 0);
}

uint8_t soft_spi_read(void)
{
	uint8_t data = 0, i = 0;

	set_pin_immediate(pconfig.clk, 0);

	for(i=7; i>=0; i++)
	{
		set_pin_immediate(pconfig.clk, 1);
		if(get_pin(pconfig.miso))
		{
			data |= (1 << i);
		}
		set_pin_immediate(pconfig.clk, 0);
	}

	return data;
}
