#include "parallel.h"

/* Handles parallel interface commands */
void parallel(void)
{
	uint8_t ok = TRUE, loop = TRUE, configured = FALSE;

	/* Initialize the I/O expansion chips */
	mcp23s17_enable();

	while(loop)
	{
		/* Read in parallel configuration data */
		read_data((uint8_t *) &hconfig, sizeof(hconfig));

		/* If given the exit command, don't do anything else, just acknowledge and exit */
		if(hconfig.action == EXIT)
		{
			ack();
			break;
		}

		/* Validate that the number of operational commands is sane */
		if(hconfig.num_commands > MAX_COMMANDS)
		{
			ok = FALSE;
		}
		else
		{
			ok = TRUE;
		}

		/* Validate I/O pins. Control pins are validated on the fly, as some may or may not be specified, depending on the target chip. */
		ok &= are_valid_pins(hconfig.addr_pins, hconfig.num_addr_pins);
		ok &= are_valid_pins(hconfig.data_pins, hconfig.num_data_pins);
		ok &= are_valid_pins(hconfig.vcc_pins, hconfig.num_vcc_pins);
		ok &= are_valid_pins(hconfig.gnd_pins, hconfig.num_gnd_pins);

		if(ok)
		{
			/* Acknowledge successful receipt of valid configuration data */
			ack();

			if(configured == FALSE || hconfig.reconfigure)
			{
				/* Configure all address, data, Vcc and GND pins as outputs */
				configure_pins_as_outputs(hconfig.addr_pins, hconfig.num_addr_pins);
				configure_pins_as_outputs(hconfig.data_pins, hconfig.num_data_pins);
				configure_pins_as_outputs(hconfig.vcc_pins, hconfig.num_vcc_pins);
				configure_pins_as_outputs(hconfig.gnd_pins, hconfig.num_gnd_pins);

				/* Set control pins as outputs */
				configure_pin_as_output(hconfig.oe.pin);
				configure_pin_as_output(hconfig.we.pin);
				configure_pin_as_output(hconfig.re.pin);
				configure_pin_as_output(hconfig.ce.pin);
				configure_pin_as_output(hconfig.be.pin);
				configure_pin_as_output(hconfig.rst.pin);

				/* Set the busy/ready pin as an input */
				configure_pin_as_input(hconfig.by.pin);
	
				/* If we have more than 8 data pins, enable word-size data access */
				if(data_size() == 1)
				{
					byte_enable(TRUE);
				}
				else
				{
					byte_enable(FALSE);
				}
	
				/* Disable all control pins */
				reset_enable(FALSE);
				write_enable(FALSE);
				read_enable(FALSE);
				output_enable(FALSE);
				write_protect(FALSE);
				chip_enable(FALSE);
					
				/* Supply power to the target chip */
				set_pins_high(hconfig.vcc_pins, hconfig.num_vcc_pins);
				set_pins_low(hconfig.gnd_pins, hconfig.num_gnd_pins);
	
				/* Commit settings */
				commit_ddr_settings();
				commit_io_settings();

				/* Enable the target chip */
				_delay_us(hconfig.toe);
				chip_enable(TRUE);
				_delay_us(hconfig.toe);
	
				/* Set the configured flag */
				configured = TRUE;
			}
	
			switch(hconfig.action)
			{
				case READ:
					ack();
					parallel_read();
					break;
				case WRITE:
					ack();
					parallel_write();
					break;
				case COMMAND:
					ack();
					execute_commands();
					ack();
					break;
//				case EXIT:
//					ack();
//					loop = FALSE;
//					break;
				default:
					/* Bad action specified, respond with NACK and a reason string */
					nack();
					fprintf(&gconfig.usb, "The specified action is not supported [0x%X]\n", hconfig.action);
					break;
			}
		}
		else
		{
			/* Band configuration specified, send a NACK and a reason */
			nack();
			fprintf(&gconfig.usb, "Invalid configuration");
			break;
		}
	}
	
	/* Disable the I/O expansion chips */	
	mcp23s17_disable();

	return;
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

/* Set the write protect pin */
void write_protect(uint8_t tf)
{
	set_control_pin(hconfig.wp, tf);
}

/* Set the read enable pin */
void read_enable(uint8_t tf)
{
	set_control_pin(hconfig.re, tf);
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
		if(get_pin(hconfig.by.pin) == hconfig.by.active)
		{	
			busy = TRUE;
		}
	}

	return busy;
}

/* Only commit settings to those devices/registers that correspond with the provided list of pins */
void commit_targeted_settings(uint8_t pins[], uint32_t count)
{
	struct device updates[MAX_DEVICES];
	uint8_t i = 0, device = 0, port = 0;

	memset((void *) &updates, 0, sizeof(updates));

	/* Update only the I/O chips and registers that need to be updated */
	for(i=0; i<count; i++)
	{
		device = gconfig.pins[pins[i]].addr;
		port = gconfig.pins[pins[i]].reg;

		if(updates[device].port[port] == 0)
		{
			commit_settings(device, port);
			updates[device].port[port] = 1;
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
			/* We can now process all data pins assigned to this I/O chip without any additional reads */
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
					if((reg & (1 << gconfig.pins[hconfig.data_pins[j]].bit)) > 0)
					{
						data |= (1 << j);
					}
				}
			}
		}
	}

	return data;
}

/* Set the appropriate pins to represent the given data */
void data2pins(uint32_t data, uint8_t pins[], uint8_t num_pins)
{
	uint8_t i = 0;

	if(num_pins > 0)
	{
		for(i=0; i<num_pins; i++)
		{
			if(((data >> i) & 1) == 1)
			{
				set_pin_high(pins[i]);
			}
			else
			{
				set_pin_low(pins[i]);
			}
		}
	}
}

/* Set the address pins to represent the given address */
void set_address(uint32_t address)
{
	data2pins(address, hconfig.addr_pins, hconfig.num_addr_pins);
	commit_address_settings();
}

/* Set the data pins to represent the given data byte/word */
void set_data(uint16_t data)
{
	data2pins((uint32_t) data, hconfig.data_pins, hconfig.num_data_pins);
	commit_data_settings();
}

/* Returns the data size, in bytes, based on the number of data pins specified in hconfig */
uint8_t data_size(void)
{
	uint8_t size = 0;

	if(hconfig.num_data_pins > 0)
	{
		if(hconfig.num_data_pins <= 8)
		{
			size = 1;
		}
		else
		{
			size = 2;
		}
	}

	return size;
}

/* Writes the given data to the specified address on the target chip */
void write_data_to_addr(uint32_t address, uint16_t data)
{
	/* Wait until the target chip is ready to receive commands */
	while(is_busy()) { }

	/* Disable all output from the target chip */
	output_enable(FALSE);

	/* Setup the address and data lines  */
	set_address(address);
	set_data(data);
	_delay_us(hconfig.toe);

	/* Toggle the write enable pin */
	write_enable(TRUE);
	_delay_us(hconfig.toe);
	
	write_enable(FALSE);
	_delay_us(hconfig.toe);
}

/* Execute the address/data commands listed in hconfig.commands */
void execute_commands(void)
{
	uint8_t i = 0;

	for(i=0; i<hconfig.num_commands; i+=2)
	{
		/* Commands are stored in the format: <addr>:<data>,<addr>:<data>... */
		write_data_to_addr(hconfig.commands[i], hconfig.commands[i+1]);
	}

	sleep(hconfig.cmd_delay);
}

/* Read in the specified number of bytes from the chip and send them back to the host */
void parallel_read(void)
{
	uint16_t data = 0;
	uint8_t read_size = 0;
	uint32_t i = 0, j = 0, c = 0;
	
	/* Get the size of the data bus, in bytes (1 or 2) */
	read_size = data_size();
	
	/* Read operations may need to be preceeded by a set of commands that prepare the chip for reading */
	execute_commands();
	
	/* Make sure data pins are set as inputs */
	configure_pins_as_inputs(hconfig.data_pins, hconfig.num_data_pins);
	commit_ddr_settings();

	for(i=0, j=0, c=0; i<hconfig.count; i+=read_size, j++, c++)
	{
		/* Wait until the target chip is not busy */
		while(is_busy()) { }

		/* Set the appropriate address pins and assert the read/output enable line */
		set_address(hconfig.addr+j);
		output_enable(TRUE);
		read_enable(TRUE);

		/* Wait for the output to become active, then read data off the data pins */
		_delay_us(hconfig.toe);
		data = read_data_pins();

		/* Release the output/read enable line, and wait for the output be be deactivated */
		output_enable(FALSE);
		read_enable(FALSE);
		_delay_us(hconfig.toe);

		/* Send one (or two) bytes of read data back to the host */
		fputc((uint8_t) (data & 0xFF), &gconfig.usb);
		if(read_size > 1)
		{
			fputc((uint8_t) ((data >> 8) & 0xFF), &gconfig.usb);
		}

		/* Toggle the status LED */
		if(c == LED_TOGGLE_INTERVAL)
		{
			toggle_led();
			c = 0;
		}
	}

	/* Make sure the LED is on after the read loop */
	led_on();
	return;
}

/* Read bytes from the host and write them to the target chip */
void parallel_write(void)
{
	uint16_t data = 0;
	uint32_t i = 0, c = 0, j = 0;
	uint8_t data1 = 0, data2 = 0;
	uint8_t write_size = data_size();

	/* Make sure data pins are set as outputs */
	configure_pins_as_outputs(hconfig.data_pins, hconfig.num_data_pins);
	commit_ddr_settings();

	/* Make sure write_size is sane. */
	if(write_size <= sizeof(data))
	{
		/* Loop until we've written hconfig.count bytes */
		for(i=0, j=hconfig.addr, c=0; i<hconfig.count; c++, j++, i+=write_size)
		{
			/* Get a byte of data from the host */
			data1 = fgetc(&gconfig.usb);

			/* If we're working with a 16 bit data bus, get the next byte */
			if(write_size > 1)
			{
				/* Send an ack so the host will send the next byte */
				ack();
				data2 = fgetc(&gconfig.usb);
			}

			/* Combine the two bytes read into a single 16 bit value */
			data = data1 + (data2 << 8);

			/* Write operations may need to be preceeded by a set of commands that prepare the chip for writing */
			execute_commands();

			/* Write the specified byte/word to the next address, then wait for the write to complete */
			write_data_to_addr(j, data);
			_delay_us(hconfig.tbp);

			/* Toggle the status LED */
			if(c == LED_TOGGLE_INTERVAL)
			{
				toggle_led();
				c = 0;
			}

			/* Acknowledge when we've finished processing a block of data so the host knows we're ready for more */
			ack();
		}
	}

	led_on();
	return;
}

