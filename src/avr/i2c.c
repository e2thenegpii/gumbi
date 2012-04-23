#include "i2c.h"

void i2c(void)
{
	uint8_t ok = TRUE, loop = TRUE, configured = FALSE;

	mcp23s17_enable();

	while(loop)
	{
		read_data((uint8_t *) &hconfig, sizeof(hconfig));

		ok &= is_valid_pin(hconfig.sda.pin);
		ok &= is_valid_pin(hconfig.clk.pin);
		ok &= are_valid_pins(hconfig.vcc_pins, hconfig.num_vcc_pins);
		ok &= are_valid_pins(hconfig.gnd_pins, hconfig.num_gnd_pins);

		if(ok)
		{
			ack();
	
			if(!configured || hconfig.reconfigure)
			{
				configure_pin_as_output(hconfig.clk.pin);
				configure_pin_as_output(hconfig.sda.pin);
				configure_pins_as_outputs(hconfig.vcc_pins, hconfig.num_vcc_pins);
				configure_pins_as_outputs(hconfig.gnd_pins, hconfig.num_gnd_pins);
				commit_ddr_settings();
	
				set_pin_high(hconfig.clk.pin);
				set_pin_high(hconfig.sda.pin);
				commit_io_settings();
	
				set_pins_high(hconfig.vcc_pins, hconfig.num_vcc_pins);
				set_pins_low(hconfig.gnd_pins, hconfig.num_gnd_pins);
				commit_io_settings();

				configured = TRUE;
			}

			switch(hconfig.action)
			{
				case READ:
					ack();
					soft_i2c_read();
					break;
				case WRITE:
					ack();
					soft_i2c_write();
					break;
				case START:
					ack();
					soft_i2c_start();
					break;
				case STOP:
					ack();
					soft_i2c_stop();
					break;
				case EXIT:
					ack();
					loop = FALSE;
					break;
				default:
					nack();
					write_string("The specified I2C action is not supported.");
			}
		}
		else
		{
			nack();
			write_string("Invalid pin configureation.");
		}
	}

	mcp23s17_disable();
}

void soft_i2c_start(void)
{
	set_pin_immediate(hconfig.clk.pin, 1);
	set_pin_immediate(hconfig.sda.pin, 1);
	set_pin_immediate(hconfig.sda.pin, 0);
}

void soft_i2c_stop(void)
{
	set_pin_immediate(hconfig.clk.pin, 1);
	set_pin_immediate(hconfig.sda.pin, 0);
	set_pin_immediate(hconfig.sda.pin, 1);
}

void soft_i2c_write_byte(uint8_t byte)
{
	uint8_t i = 0;

	configure_pin_immediate(hconfig.sda.pin, 'w');

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(hconfig.clk.pin, 0);
		set_pin_immediate(hconfig.sda.pin, ((byte & (1 << i)) >> i));
		set_pin_immediate(hconfig.clk.pin, 1);
		set_pin_immediate(hconfig.clk.pin, 0);
	}
}

uint8_t soft_i2c_read_byte(void)
{
	uint8_t i = 0, byte = 0;

	configure_pin_immediate(hconfig.sda.pin, 'r');

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(hconfig.clk.pin, 0);
		set_pin_immediate(hconfig.clk.pin, 1);
		if(get_pin(hconfig.sda.pin))
		{
			byte |= (1 << i);
		}
	}
	
	return byte;
}

void soft_i2c_write(void)
{
	uint8_t i = 0, j = 0;
	uint8_t data[BLOCK_SIZE] = { 0 };

	for(i=0; i<hconfig.count; )
	{
		read_data((uint8_t *) &data, sizeof(data));

		for(j=0; j<sizeof(data) && i<hconfig.count; j++, i++)
		{
			soft_i2c_write_byte(data[j]);
		}

		ack();
	}
}

void soft_i2c_read(void)
{
	uint8_t i = 0, byte = 0;

	for(i=0; i<hconfig.count; i++)
	{
		byte = soft_i2c_read_byte();
		buffered_write((uint8_t *) &byte, 1);
	}

	flush_buffer();
}

