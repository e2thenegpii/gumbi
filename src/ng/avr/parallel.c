#include "parallel.h"

/* Handles parallel NOR flash commands */
void parallel_flash(void)
{
	uint8_t ok = TRUE;

	/* Read in parallel flash configuration data */
	read_data((uint8_t *) &hconfig, sizeof(hconfig));

	/* Validate data pins. Control pins are validated on the fly, as some may or may not be specified, depending on the target chip. */
	ok &= are_valid_pins(hconfig.addr_pins, hconfig.num_addr_pins);
	ok &= are_valid_pins(hconfig.data_pins, hconfig.num_data_pins);
	ok &= are_valid_pins(hconfig.vcc_pins, hconfig.num_vcc_pins);
	ok &= are_valid_pins(hconfig.gnd_pins, hconfig.num_gnd_pins);

	/* Validate that the number of write commands is sane */
	if(hconfig.num_write_commands > MAX_WRITE_COMMANDS)
	{
		ok = FALSE;
	}

	if(ok)
	{
		/* Acknowledge successful receipt of configuration data */
		ack();

		/* Initialize SPI and the MCP23S17 chips */
		mcp23s17_enable();

		/* Configure all address, Vcc and GND pins as outputs */
		configure_pins_as_outputs(hconfig.addr_pins, hconfig.num_addr_pins);
		configure_pins_as_outputs(hconfig.vcc_pins, hconfig.num_vcc_pins);
		configure_pins_as_outputs(hconfig.gnd_pins, hconfig.num_gnd_pins);

		/* Set control pins as outputs */
		configure_pin_as_output(hconfig.oe.pin);
		configure_pin_as_output(hconfig.we.pin);
		configure_pin_as_output(hconfig.ce.pin);
		configure_pin_as_output(hconfig.be.pin);
		configure_pin_as_output(hconfig.rst.pin);

		/* Set the busy/ready pin as an input */
		configure_pin_as_input(hconfig.by.pin);

		/* If we have more than 8 data pins, enable word-size data access */
		if(hconfig.num_data_pins > 8)
		{
			byte_enable(FALSE);
		}
		else
		{
			byte_enable(TRUE);
		}
	
		/* Enable the target chip while disabling output and writing */
		reset_enable(FALSE);
		write_enable(FALSE);
		output_enable(FALSE);
		chip_enable(TRUE);
	
		/* Supply power to the target chip */
		set_pins_high(hconfig.vcc_pins, hconfig.num_vcc_pins);
		set_pins_low(hconfig.gnd_pins, hconfig.num_gnd_pins);
	
		/* Commit settings */
		commit_ddr_settings();
		commit_io_settings();
	
		switch(hconfig.action)
		{
			case READ:
				/* When reading, data pins are inputs to us */
				configure_pins_as_inputs(hconfig.data_pins, hconfig.num_data_pins);
				commit_ddr_settings();
				ack();
				parallel_read();
				break;
			case WRITE:
				/* When writing, data pins are outputs from us */
				configure_pins_as_outputs(hconfig.data_pins, hconfig.num_data_pins);
				commit_ddr_settings();
				ack();
				parallel_write();
				break;
			default:
				nack();
				write_string("The specified action is not supported");
				break;
		}

		mcp23s17_disable();

		/* Final ACK indicates the parallel flash operation is complete */
		ack();
	}
	else
	{
		nack();
		write_string("Invalid pin configuration");
	}

	return;
}

/* Sets the specified control pin to active (tf = TRUE) or inactive (tf = FALSE) state */
void set_control_pin(struct ctrlpin p, uint8_t tf)
{
	if(is_valid_pin(p.pin))
	{
		if(tf)
		{
			set_pin_immediate(p.pin, p.active);
		}
		else
		{
			set_pin_immediate(p.pin, ~p.active);
		}
	}
}

/* Set the output enable pin */
void output_enable(uint8_t tf)
{
	set_control_pin(hconfig.oe, tf);
}

/* Set the write enable pin */
void write_enable(uint8_t tf)
{
	set_control_pin(hconfig.we, tf);
}

/* Set the chip enable pin */
void chip_enable(uint8_t tf)
{
	set_control_pin(hconfig.ce, tf);
}

/* Set the reset enable pin */
void reset_enable(uint8_t tf)
{
	set_control_pin(hconfig.rst, tf);
}

/* Set the byte enable pin (disable BE pin to enable word-based operations) */
void byte_enable(uint8_t tf)
{
	set_control_pin(hconfig.be, tf);
}

/* Check if the chip is busy or not */
uint8_t is_busy(void)
{
	uint8_t busy = FALSE;

	if(is_valid_pin(hconfig.by.pin))
	{
		if((read_register(gconfig.pins[hconfig.by.pin].addr, gconfig.pins[hconfig.by.pin].reg) & (1 << gconfig.pins[hconfig.by.pin].bit)) == gconfig.pins[hconfig.by.pin].active)
		{
			busy = TRUE;
		}
	}

	return busy;
}

/* Only commit settings to those devices/registers that correspond with the provided list of pins */
void commit_targeted_settings(uint8_t pins[], uint32_t count)
{
	uint8_t i = 0;
	struct device updates[MAX_DEVICES];

	memset((void *) &updates, 0, sizeof(updates));

	/* Mark all I/O chips and registers that need to be updated */
	for(i=0; i<count; i++)
	{
		updates[gconfig.pins[pins[i]].addr].port[gconfig.pins[pins[i]].reg] = 1;		
	}
	updates[gconfig.pins[hconfig.oe.pin].addr].port[gconfig.pins[hconfig.oe.pin].reg] = 1;

	/* Update only the registers on the I/O chips that have address pins assigned to them */
	for(i=0; i<gconfig.num_io_devices; i++)
	{
		if(updates[i].port[GPIOA] == 1)
		{
			commit_settings(i, GPIOA);
		}
		else if(updates[i].port[GPIOB] == 1)
		{
			commit_settings(i, GPIOB);
		}
	}
}

/* Update all registers on all I/O chips that have address pins assigned to them */
void commit_address_settings(void)
{
	commit_targeted_settings(hconfig.addr_pins, hconfig.num_addr_pins);
}

/* Update all registers on all I/O chips that have data pins assigned to them */
void commit_data_settings(void)
{
	commit_targeted_settings(hconfig.data_pins, hconfig.num_data_pins);
}

/* Read in one (or two) bytes of data from the data lines */
uint16_t read_data_pins(void)
{
	uint8_t i = 0, j = 0, reg = 0, rega = 0, regb = 0;
	uint16_t data = 0;
	
	/* Loop through all the I/O expansion chips */
	for(i=0; i<gconfig.num_io_devices; i++)
	{
		reg = rega = regb = 0;

		/* Only read from chips that have data pins assigned to them */
		for(j=0; j<hconfig.num_data_pins; j++)
		{
			if(gconfig.pins[hconfig.data_pins[j]].addr == i)
			{
				rega = read_register(i, GPIOA);
				regb = read_register(i, GPIOB);
				break;
			}
		}

		if(rega || regb)
		{
			for(j=0; j<hconfig.num_data_pins; j++)
			{
				/* Does this data pin reside on this chip? */
				if(gconfig.pins[hconfig.data_pins[j]].addr == i)
				{
					/* Which port was the pin assigned to? */
					if(gconfig.pins[hconfig.data_pins[j]].reg == GPIOA)
					{
						reg = rega;
					}
					else
					{
						reg = regb;
					}

					/* If this pin is set, set the appropriate bit in data */
					if((reg | (1 << gconfig.pins[hconfig.data_pins[j]].bit)) == reg)
					{
						data |= (1 << j);
					}
				}
			}
		}
	}

	return data;
}

/* Set the appropriate pins to represent the given address */
void set_address(uint32_t address)
{
	uint8_t i = 0;

	for(i=0; i<hconfig.num_addr_pins; i++)
	{
		if((address | (1 << i)) == address)
		{
			set_pin_high(hconfig.addr_pins[i]);
		}
		else
		{
			set_pin_low(hconfig.addr_pins[i]);
		}
	}
	
	commit_address_settings();
}

/* Set the appropriate pins to represent the given data byte/word */
void set_data(uint16_t data)
{
	uint8_t i = 0;

	for(i=0; i<hconfig.num_data_pins; i++)
	{
		if((data | (1 << i)) == data)
		{
			set_pin_high(hconfig.data_pins[i]);
		}
		else
		{
			set_pin_low(hconfig.data_pins[i]);
		}
	}

	commit_data_settings();
}

/* Read in the specified number of bytes from the chip and write them to the UART */
void parallel_read(void)
{
	uint32_t i = 0;
	uint16_t data = 0;
	uint8_t read_size = 0;

	/* num_data_pins should be either 8 or 16. We're trusting the data structure passed from the PC to adhere to this limitation. */
	read_size = (hconfig.num_data_pins / 8);

	for(i=0; i<hconfig.count; i+=read_size)
	{
		/* 
		 * TODO: Try to improve the speed of this code block.
 		 */
		set_address(hconfig.addr+i);
		output_enable(TRUE);
		_delay_us(hconfig.toe);
		data = read_data_pins();
		output_enable(FALSE);
		_delay_us(hconfig.toe);

		buffered_write((uint8_t *) &data, 1);
		if(read_size > 1)
		{
			data = (data >> 8);
			buffered_write((uint8_t *) &data, 1);
		}
	}

	flush_buffer();
}

/* Read bytes from the UART and write them to the target chip */
void parallel_write(void)
{
	uint16_t pbyte = 0;
	uint8_t write_size = 0;
	uint32_t i = 0, j = 0, k = 0;
	uint8_t data[BLOCK_SIZE] = { 0 };

	/* num_data_pins should be either 8 or 16. We're trusting the data structure passed from the PC to adhere to this limitation. */
	write_size = (hconfig.num_data_pins / 8);

	/* We use write_size in the memcpy, so make sure it's sane. */
	if(write_size <= sizeof(pbyte))
	{
		/* Loop until we've written hconfig.count bytes */
		for(i=0; i<hconfig.count; )
		{
			/* Read in the data to be written to the chip */
			read_data((uint8_t *) &data, sizeof(data));

			/* Loop through this block of data, writing it sequentially to the chip, starting at address hconfig.addr */	
			for(j=0; i<hconfig.count && j<sizeof(data); i+=write_size, j+=write_size)
			{
				/* Get the next byte/word to write */
				memcpy((void *) &pbyte, (void *) &(data[j]), write_size);

				/* Any write operation must be preceeded by a set of commands that prepare the chip for writing */
				for(k=0; k<hconfig.num_write_commands; k++)
				{
					while(is_busy()) { }
					set_address(hconfig.write_commands[k].addr);
					set_data(hconfig.write_commands[k].data);
					write_enable(TRUE);
					_delay_us(hconfig.toe);
					write_enable(FALSE);
					_delay_us(hconfig.tbp);
				}				

				while(is_busy()) { }

				set_address(hconfig.addr+i);
				set_data(pbyte);

				write_enable(TRUE);
				_delay_us(hconfig.toe);
				write_enable(FALSE);
				_delay_us(hconfig.tbp);
			}
			
			/* Acknowledge when we've finished processing a block of data so the host knows we're ready for more */	
			ack();
		}
	}

	return;
}

