#include "parallel.h"

/* Handles parallel flash commands */
void parallel_flash(void)
{
	/* Read in parallel flash configuration data */
	read_data((uint8_t *) &pconfig, sizeof(pconfig));

	if(validate_pconfig())
	{
		/* Acknowledge successful receipt of configuration data */
		ack();

		/* Initialize SPI and the MCP23S17 chips */
		mcp23s17_enable();

		/* Configure all address, Vcc and GND pins as outputs */
		configure_pins_as_outputs(pconfig.addr_pins, pconfig.num_addr_pins);
		configure_pins_as_outputs(pconfig.vcc_pins, pconfig.num_vcc_pins);
		configure_pins_as_outputs(pconfig.gnd_pins, pconfig.num_gnd_pins);

		/* Set control pins as outputs */
		configure_pin_as_output(pconfig.oe.pin);
		configure_pin_as_output(pconfig.we.pin);
		configure_pin_as_output(pconfig.ce.pin);
		configure_pin_as_output(pconfig.be.pin);
		configure_pin_as_output(pconfig.rst.pin);

		/* Set the busy/ready pin as an input */
		configure_pin_as_input(pconfig.by.pin);

		/* If we have more than 8 data pins, enable word-size data access */
		if(pconfig.num_data_pins > 8)
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
		set_pins_high(pconfig.vcc_pins, pconfig.num_vcc_pins);
		set_pins_low(pconfig.gnd_pins, pconfig.num_gnd_pins);
	
		/* Commit settings */
		commit_ddr_settings();
		commit_io_settings();
	
		switch(pconfig.action)
		{
			case READ:
				ack();
				/* When reading, data pins are inputs to us */
				configure_pins_as_inputs(pconfig.data_pins, pconfig.num_data_pins);
				commit_ddr_settings();
				parallel_read();
				break;
			case WRITE:
				ack();
				/* When writing, data pins are outputs from us */
				configure_pins_as_outputs(pconfig.data_pins, pconfig.num_data_pins);
				commit_ddr_settings();
				parallel_write();
				break;
			default:
				nack();
				printf("The specified action (0x%.2X) is not supported\r\n", pconfig.action);
				break;
		}

		mcp23s17_disable();

		/* Final ACK indicates the parallel flash operation is complete */
		ack();
	}
	else
	{
		nack();
		printf("Invalid pin configuration\r\n");
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
	set_control_pin(pconfig.oe, tf);
}

/* Set the write enable pin */
void write_enable(uint8_t tf)
{
	set_control_pin(pconfig.we, tf);
}

/* Set the chip enable pin */
void chip_enable(uint8_t tf)
{
	set_control_pin(pconfig.ce, tf);
}

/* Set the reset enable pin */
void reset_enable(uint8_t tf)
{
	set_control_pin(pconfig.rst, tf);
}

/* Set the byte enable pin (disable BE pin to enable word-based operations) */
void byte_enable(uint8_t tf)
{
	set_control_pin(pconfig.be, tf);
}

/* Check if the chip is busy or not */
uint8_t is_busy(void)
{
	uint8_t busy = FALSE;

	if(is_valid_pin(pconfig.by.pin))
	{
		if((read_register(gconfig.pins[pconfig.by.pin].addr, gconfig.pins[pconfig.by.pin].reg) & (1 << gconfig.pins[pconfig.by.pin].bit)) == gconfig.pins[pconfig.by.pin].active)
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
	commit_targeted_settings(pconfig.addr_pins, pconfig.num_addr_pins);
}

/* Update all registers on all I/O chips that have data pins assigned to them */
void commit_data_settings(void)
{
	commit_targeted_settings(pconfig.data_pins, pconfig.num_data_pins);
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
		for(j=0; j<pconfig.num_data_pins; j++)
		{
			if(gconfig.pins[pconfig.data_pins[j]].addr == i)
			{
				rega = read_register(i, GPIOA);
				regb = read_register(i, GPIOB);
				break;
			}
		}

		if(rega || regb)
		{
			for(j=0; j<pconfig.num_data_pins; j++)
			{
				/* Does this data pin reside on this chip? */
				if(gconfig.pins[pconfig.data_pins[j]].addr == i)
				{
					/* Which port was the pin assigned to? */
					if(gconfig.pins[pconfig.data_pins[j]].reg == GPIOA)
					{
						reg = rega;
					}
					else
					{
						reg = regb;
					}

					/* If this pin is set, set the appropriate bit in data */
					if((reg | (1 << gconfig.pins[pconfig.data_pins[j]].bit)) == reg)
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

	for(i=0; i<pconfig.num_addr_pins; i++)
	{
		if((address | (1 << i)) == address)
		{
			set_pin_high(pconfig.addr_pins[i]);
		}
		else
		{
			set_pin_low(pconfig.addr_pins[i]);
		}
	}
	
	commit_address_settings();
}

/* Read in the specified number of bytes from the chip and write them to the UART */
void parallel_read(void)
{
	uint16_t data = 0;
	uint8_t read_size = 0;
	uint32_t i = 0;

	/* This should be either 8 or 16. We're trusting the data structure passed from the PC to adhere to this limitation. */
	read_size = (pconfig.num_data_pins / 8);

	for(i=0; i<pconfig.count; i+=read_size)
	{
		/* 
		 * TODO: Try to improve the speed of this code block. Ideas:
		 *
		 * 	o Remove the is_valid_pin checks in set_pin_high/set_pin_low.
		 *	o Remove first loop in commit_targeted_settings.
		 * 	o Each output_enable call results in an additional SPI transaction.
		 * 	o Can the read_data_pins function be minimized?
		 *	o Call uart_write_byte directly, instead of putchar.
 		 */
		set_address(pconfig.addr+i);
		_delay_us(pconfig.toe);
		output_enable(TRUE);
		_delay_us(pconfig.toe);
		data = read_data_pins();
		_delay_us(pconfig.toe);
		output_enable(FALSE);

		putchar((uint8_t) (data & 0xFF));
		if(read_size > 1)
		{
			putchar((uint8_t) (data >> 8));
		}
	}
}

/* Read bytes from the UART and write them to the target chip */
void parallel_write(void)
{
	/* TODO: Not implemented yet */
	return;
}

