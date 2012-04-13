#include "i2c.h"

void i2c_eeprom(void)
{
	uint8_t ok = TRUE;

	read_data((uint8_t *) &pconfig, sizeof(pconfig));

	ok &= is_valid_pin(pconfig.sda);
	ok &= is_valid_pin(pconfig.clk);
	ok &= are_valid_pins(pconfig.vcc_pins, pconfig.num_vcc_pins);
	ok &= are_valid_pins(pconfig.gnd_pins, pconfig.num_gnd_pins);

	if(ok)
	{
		ack();

		mcp23s17_enable();

		configure_pin_as_output(pconfig.clk);
		configure_pin_as_output(pconfig.sda);
		configure_pins_as_outputs(pconfig.vcc_pins, pconfig.num_vcc_pins);
		configure_pins_as_outputs(pconfig.gnd_pins, pconfig.num_gnd_pins);
		commit_ddr_settings();

		set_pin_high(pconfig.clk);
		set_pin_high(pconfig.sda);
		commit_io_settings();

		set_pins_high(pconfig.vcc_pins, pconfig.num_vcc_pins);
		set_pins_low(pconfig.gnd_pins, pconfig.num_gnd_pins);
		commit_io_settings();

		switch(pconfig.action)
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
	set_pin_immediate(pconfig.clk, 1);
	set_pin_immediate(pconfig.sda, 1);
	set_pin_immediate(pconfig.sda, 0);
}

void soft_i2c_stop(void)
{
	set_pin_immediate(pconfig.clk, 1);
	set_pin_immediate(pconfig.sda, 0);
	set_pin_immediate(pconfig.sda, 1);
}

void soft_i2c_write(uint8_t byte)
{
	uint8_t i = 0;

	configure_pin_immediate(pconfig.sda, 'w');

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(pconfig.clk, 0);
		set_pin_immediate(pconfig.sda, ((byte & (1 << i)) >> i));
		set_pin_immediate(pconfig.clk, 1);
		set_pin_immediate(pconfig.clk, 0);
	}

	/* A read is always preceeded by at least one write. Make sure the SDA pin is configured as an input after every write. */	
	configure_pin_immediate(pconfig.sda, 'r');
}

uint8_t soft_i2c_read(void)
{
	uint8_t i = 0, byte = 0;

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(pconfig.clk, 0);
		set_pin_immediate(pconfig.clk, 1);
		if(get_pin(pconfig.sda))
		{
			byte |= (1 << i);
		}
	}
	
	return byte;
}

void read_i2c_eeprom(void)
{
	uint32_t i = 0;

	for(i=0; i<pconfig.count; i++)
	{
		/* TODO: Do the actual read. Also need to implement N/ACK support. */
	}
}
