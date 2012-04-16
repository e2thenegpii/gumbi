#include "i2c.h"

void i2c_eeprom(void)
{
	uint8_t ok = TRUE;

	read_data((uint8_t *) &hconfig, sizeof(hconfig));

	ok &= is_valid_pin(hconfig.sda);
	ok &= is_valid_pin(hconfig.clk);
	ok &= are_valid_pins(hconfig.vcc_pins, hconfig.num_vcc_pins);
	ok &= are_valid_pins(hconfig.gnd_pins, hconfig.num_gnd_pins);

	if(ok)
	{
		ack();

		mcp23s17_enable();

		configure_pin_as_output(hconfig.clk);
		configure_pin_as_output(hconfig.sda);
		configure_pins_as_outputs(hconfig.vcc_pins, hconfig.num_vcc_pins);
		configure_pins_as_outputs(hconfig.gnd_pins, hconfig.num_gnd_pins);
		commit_ddr_settings();

		set_pin_high(hconfig.clk);
		set_pin_high(hconfig.sda);
		commit_io_settings();

		set_pins_high(hconfig.vcc_pins, hconfig.num_vcc_pins);
		set_pins_low(hconfig.gnd_pins, hconfig.num_gnd_pins);
		commit_io_settings();

		switch(hconfig.action)
		{
			case READ:
				ack();
				read_i2c_eeprom();
				break;
			case WRITE:
			default:
				nack();
				write_string("The specified I2C EEPROM action is not supported.");
		}
	}
	else
	{
		nack();
		write_string("Invalid pin configureation.");
	}

	mcp23s17_disable();
}

void soft_i2c_start(void)
{
	set_pin_immediate(hconfig.clk, 1);
	set_pin_immediate(hconfig.sda, 1);
	set_pin_immediate(hconfig.sda, 0);
}

void soft_i2c_stop(void)
{
	set_pin_immediate(hconfig.clk, 1);
	set_pin_immediate(hconfig.sda, 0);
	set_pin_immediate(hconfig.sda, 1);
}

void soft_i2c_write(uint8_t byte)
{
	uint8_t i = 0;

	configure_pin_immediate(hconfig.sda, 'w');

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(hconfig.clk, 0);
		set_pin_immediate(hconfig.sda, ((byte & (1 << i)) >> i));
		set_pin_immediate(hconfig.clk, 1);
		set_pin_immediate(hconfig.clk, 0);
	}

	/* A read is always preceeded by at least one write. Make sure the SDA pin is configured as an input after every write. */	
	configure_pin_immediate(hconfig.sda, 'r');
}

uint8_t soft_i2c_read(void)
{
	uint8_t i = 0, byte = 0;

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(hconfig.clk, 0);
		set_pin_immediate(hconfig.clk, 1);
		if(get_pin(hconfig.sda))
		{
			byte |= (1 << i);
		}
	}
	
	return byte;
}

void read_i2c_eeprom(void)
{
	uint32_t i = 0;

	for(i=0; i<hconfig.count; i++)
	{
		/* TODO: Do the actual read. Also need to implement N/ACK support. */
	}
}
