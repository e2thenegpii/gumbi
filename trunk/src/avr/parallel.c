#include <avr/io.h>

#include "common.h"
#include "mcp23s17.h"
#include "parallel.h"

/* Handles parallel flash commands */
void parallel_flash(void)
{
	/* Initialize SPI and the MCP23S17 chips */
	mcp23s17_init();

	/* Configure all address, Vcc and GND pins as outputs */
	configure_pins_as_outputs(gconfig->addr_pins, gconfig->num_addr_pins);
	configure_pins_as_outputs(gconfig->vcc_pins, gconfig->num_vcc_pins);
	configure_pins_as_outputs(gconfig->gnd_pins, gconfig->num_gnd_pins);

	/* Set control pins as outputs */
	configure_pin_as_output(&gconfig->oe_pin);
	configure_pin_as_output(&gconfig->we_pin);
	configure_pin_as_output(&gconfig->ce_pin);
	configure_pin_as_output(&gconfig->be_pin);
	configure_pin_as_output(&gconfig->rst_pin);

	/* Set the busy/ready pin as an input */
	configure_pin_as_input(&gconfig->by_pin);

	/* If we have more than 8 data pins, enable word-size data access */
	if(gconfig->num_data_pins > 8)
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
	set_pins_high(gconfig->vcc_pins, gconfig->num_vcc_pins);
	set_pins_low(gconfig->gnd_pins, gconfig->num_gnd_pins);

	/* Commit settings */
	commit_ddr_settings();
	commit_io_settings();

	switch(gconfig->action)
	{
		case READ:
			configure_pins_as_inputs(gconfig->data_pins, gconfig->num_data_pins);
			commit_ddr_settings();
			parallel_read();
			break;
		case WRITE:
			configure_pins_as_outputs(gconfig->data_pins, gconfig->num_data_pins);
			commit_ddr_settings();
			parallel_write();
			break;
		default:
			break;
	}

	mcp23s17_disable();
	return;
}

/* Sets the specified control pin to active (tf = TRUE) or inactive (tf = FALSE) state */
void set_control_pin(struct pin *p, uint8_t tf)
{
	if(p->inuse)
	{
		if(tf)
		{
			set_pin_immediate(p, p->active);
		}
		else
		{
			set_pin_immediate(p, ~p->active);
		}
	}
}

/* Set the output enable pin */
void output_enable(uint8_t tf)
{
	set_control_pin(&gconfig->oe_pin, tf);
}

/* Set the write enable pin */
void write_enable(uint8_t tf)
{
	set_control_pin(&gconfig->we_pin, tf);
}

/* Set the chip enable pin */
void chip_enable(uint8_t tf)
{
	set_control_pin(&gconfig->ce_pin, tf);
}

/* Set the reset enable pin */
void reset_enable(uint8_t tf)
{
	set_control_pin(&gconfig->rst_pin, tf);
}

/* Set the byte enable pin (disable BE pin to enable word-based operations) */
void byte_enable(uint8_t tf)
{
	set_control_pin(&gconfig->be_pin, tf);
}

/* Check if the chip is busy or not */
uint8_t is_busy(void)
{
	uint8_t busy = FALSE;

	if(gconfig->by_pin.inuse)
	{
		if((read_register(gconfig->by_pin.addr, gconfig->by_pin.reg) & (1 << gconfig->by_pin.bit)) == gconfig->by_pin.active)
		{
			busy = TRUE;
		}
	}

	return busy;
}

/* Update all registers on all I/O chips that have address pins assigned to them */
void commit_address_settings(void)
{
	uint8_t i = 0, j = 0;
	struct device updates[NUM_DEVICES];

	/* Initialize ports in updates */
	for(i=0; i<NUM_DEVICES; i++)
	{
		for(j=0; j<NUM_REGISTERS; j++)
		{
			updates[i].port[j] = 0;
		}
	}

	/* Mark all I/O chips and registers that need to be updated */
	for(i=0; i<gconfig->num_addr_pins; i++)
	{
		updates[gconfig->addr_pins[i].addr].port[gconfig->addr_pins[i].reg] = 1;		
	}

	/* Update only the registers on the I/O chips that have address pins assigned to them */
	for(i=0; i<NUM_DEVICES; i++)
	{
		for(j=0; j<NUM_REGISTERS; i++)
		{
			if(updates[i].port[j] == 1)
			{
				commit_settings(i, j);
			}
		}
	}
}

/* Update all registers on all I/O chips that have data pins assigned to them */
void commit_data_settings(void)
{
	uint8_t i = 0, j = 0;
	struct device updates[NUM_DEVICES];

	/* Initialize ports in updates */
        for(i=0; i<NUM_DEVICES; i++)
        {
                for(j=0; j<NUM_REGISTERS; j++)
                {
                        updates[i].port[j] = 0;
                }
        }

	for(i=0; i<gconfig->num_data_pins; i++)
	{
		updates[gconfig->data_pins[i].addr].port[gconfig->data_pins[i].reg] = 1;
	}
	
	for(i=0; i<NUM_DEVICES; i++)
	{
		for(j=0; j<NUM_REGISTERS; i++)
		{
			if(updates[i].port[j] == 1)
			{
				commit_settings(i, j);
			}
		}
	}
}

/* Read in one (or two) bytes of data from the data lines */
uint16_t read_data(void)
{
	uint8_t i = 0, j = 0, reg = 0, rega = 0, regb = 0;
	uint16_t data = 0;
	
	/* Loop through all the I/O expansion chips */
	for(i=0; i<NUM_DEVICES; i++)
	{
		reg = rega = regb = 0;

		/* Only read from chips that have data pins assigned to them */
		for(j=0; j<gconfig->num_data_pins; j++)
		{
			if(gconfig->data_pins[j].addr == i)
			{
				rega = read_register(i, GPIOA);
				regb = read_register(i, GPIOB);
				break;
			}
		}

		if(rega || regb)
		{
			for(j=0; j<gconfig->num_data_pins; j++)
			{
				/* Does this data pin reside on this chip? */
				if(gconfig->data_pins[j].addr == i)
				{
					/* Which port was the pin assigned to? */
					if(gconfig->data_pins[j].reg == GPIOA)
					{
						reg = rega;
					}
					else
					{
						reg = regb;
					}

					/* If this pin is set, set the appropriate bit in data */
					if((reg | (1 << gconfig->data_pins[j].bit)) == reg)
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

	for(i=0; i<gconfig->num_addr_pins; i++)
	{
		if((address | (1 << i)) == address)
		{
			set_pin_high(&gconfig->addr_pins[i]);
		}
		else
		{
			set_pin_low(&gconfig->addr_pins[i]);
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
	read_size = gconfig->num_data_pins;

	for(i=0; i<gconfig->count; i+=read_size)
	{
		/* TODO: Do we need sleeps in here to ensure the data is latched before reading? I don't think so... */
		set_address(gconfig->addr+i);
		output_enable(TRUE);
		data = read_data();
		output_enable(FALSE);

		putchar((uint8_t) (data & 0xFF));
		if(read_size > 8)
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

