#include "spi.h"

/* TODO: Add action to select/deselect SPI slave */

/* SPI action handler */
void spi(void)
{
	uint8_t loop = TRUE;

	/* Initialize the I/O expansion chips */
	mcp23s17_init();

	while(loop)
	{
		/* Read in config data from the host */
		read_data((uint8_t *) &hconfig, sizeof(hconfig));

		/* Make sure the config data is sane */
		if(validate_spi_config())
		{
			/* Acknowledge the receipt of valid config data */
			ack();

			/* Configure SPI pins */
			configure_pin_as_input(hconfig.miso.pin);
			configure_pin_as_output(hconfig.mosi.pin);
			configure_pin_as_output(hconfig.ss.pin);
			configure_pin_as_output(hconfig.clk.pin);

			/* Put all SPI pins in their idle states  */
			ss_active(FALSE);
			clk_active(FALSE);
			mosi_active(FALSE);
			miso_active(FALSE);

			/* Configure Vcc and GND pins */
			configure_pins_as_outputs(hconfig.vcc_pins, hconfig.num_vcc_pins);
			configure_pins_as_outputs(hconfig.gnd_pins, hconfig.num_gnd_pins);

			/* Set Vcc pins high, GND pins low */
			set_pins_high(hconfig.vcc_pins, hconfig.num_vcc_pins);
			set_pins_low(hconfig.gnd_pins, hconfig.num_gnd_pins);

			/* Commit the above direction and output settings */
			commit_ddr_settings();
			commit_io_settings();

			switch(hconfig.action)
			{
				case READ:
					ack();
					spi_read();
					break;
				case WRITE:
					ack();
					spi_write();
					break;
				case EXIT:
					ack();
					loop = FALSE;
					break;
				default:
					nack();
					write_string("The specified SPI Flash action is not supported");
			}
		}
		else
		{
			nack();
			write_string("Invalid configuration data");
		}
	}
	
	mcp23s17_disable();
}

/* De/activates the SS pin */
void ss_active(uint8_t tf)
{
	set_control_pin(hconfig.ss, tf);
}

/* De/activates the CLK pin */
void clk_active(uint8_t tf)
{
	set_control_pin(hconfig.clk, tf);
}

/* De/activates the MOSI pin */
void mosi_active(uint8_t tf)
{
	set_control_pin(hconfig.mosi, tf);
}

/* De/activates the MISO pin */
void miso_active(uint8_t tf)
{
	set_control_pin(hconfig.miso, tf);
}

/* Validate the SPI-specific configuration settings */
uint8_t validate_spi_config(void)
{
	uint8_t ok = TRUE;

	ok &= is_valid_pin(hconfig.clk.pin);
	ok &= is_valid_pin(hconfig.ss.pin);
	ok &= is_valid_pin(hconfig.mosi.pin);
	ok &= is_valid_pin(hconfig.miso.pin);
	ok &= are_valid_pins(hconfig.vcc_pins, hconfig.num_vcc_pins);
	ok &= are_valid_pins(hconfig.gnd_pins, hconfig.num_gnd_pins);

	return ok;
}

/* Write one byte, MSB first */
void soft_spi_write_byte(uint8_t byte)
{
	uint8_t i = 0;

	for(i=7; i>=0; i--)
	{
		set_pin_immediate(hconfig.mosi.pin, ((byte & (1 << i)) >> i));
		clk_active(TRUE);
		clk_active(FALSE);
	}
}

/* Read one byte, MSB first */
uint8_t soft_spi_read_byte(void)
{
	uint8_t data = 0, i = 0;

	for(i=7; i>=0; i++)
	{
		if(get_pin(hconfig.miso.pin))
		{
			data |= (1 << i);
		}
	}

	return data;
}

/* Read bytes from the target SPI chip */
void spi_read(void)
{
	uint32_t i = 0;
	uint8_t byte = 0;

	ss_active(TRUE);
	
	for(i=0; i<hconfig.count; i++)
	{
		byte = soft_spi_read_byte();
		buffered_write((uint8_t *) &byte, sizeof(byte));
	}

	flush_buffer();

	ss_active(TRUE);
}

/* Write bytes to the target SPI chip */
void spi_write(void)
{
	uint8_t j = 0;
	uint32_t i = 0;
	uint8_t buf[BLOCK_SIZE] = { 0 };

	ss_active(TRUE);

	for(i=0; i<hconfig.count; )
	{
		/* Read data from host */
		read_data((uint8_t *) &buf, sizeof(buf));

		/* Write data to SPI chip */
		for(j=0; j<sizeof(buf) && i<hconfig.count; j++, i++)
		{
			soft_spi_write_byte(buf[j]);
		}

		/* Acknowledge that we're done processing this block of data so the host knows to send more */
		ack();
	}
	
	ss_active(TRUE);
}
