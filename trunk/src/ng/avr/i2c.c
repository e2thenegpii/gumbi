#include "i2c.h"

void soft_i2c_init(void)
{
	mcp23s17_enable();
	configure_pin_as_output(pconfig.clk);
	configure_pin_as_output(pconfig.sda);
	commit_ddr_settings();
}

void soft_i2c_close(void)
{
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
