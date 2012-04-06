#include "mcp23s17.h"

/* 
 * Configures the MCP23S17 reset pin as an output.
 * Identifies how many MCP23S17 chips are on the SPI bus.
 * Calculates the number of available I/O pins.
 * Puts the MCP32S17 chips into a reset (standby) state.
 * Initializes the gconfig.pins data structures.
 *
 * This should be called before any other functions in mcp23s17.c.
 */
void mcp23s17_init(void)
{
	RESET_DDR |= (1 << RESET_PIN);

	mcp23s17_enable();
	gconfig.num_io_devices = mcp23s17_chip_count();
	gconfig.num_pins = (gconfig.num_io_devices * PINS_PER_DEVICE);
	mcp23s17_disable();

	init_pins();
}

/* 
 * Puts the MCP23S17 chips into a reset state, or takes the out of a reset state.
 * If rst == TRUE, the chips are put into a reset state.
 * If rst == FALSE, the chips are taken out of a reset state.
 */
void mcp23s17_chip_reset(uint8_t rst)
{
	if(rst == TRUE)
	{
		/* The reset pin is active low. */
		RESET_PORT &= ~(1 << RESET_PIN);
	}
	else
	{
		RESET_PORT |= (1 << RESET_PIN);
	}
}

/* Enables and configures all the MCP23S17 chips on the SPI bus. */
void mcp23s17_enable(void)
{
	/* Bring the I/O chips out of their reset state */
	mcp23s17_chip_reset(FALSE);

	/* Initialize SPI */
	spi_init(SPI_MODE_0, SPI_MSB, SPI_NO_INTERRUPT, SPI_MSTR_CLK4, SPI_SS_IDLE_HIGH);

	/* Initialize I/O expansion chips */
	mcp23s17_io_init();
}

/* Puts the MCP23S17 chips into a reset state and disables SPI on the AVR. */
void mcp23s17_disable(void)
{
	mcp23s17_chip_reset(TRUE);
	spi_disable();
}

/* Loads all MCP23S17 chips with their initial configurations. */
void mcp23s17_io_init(void)
{
	uint8_t i = 0, j = 0;

	/* Set IOCON value on all un-initialized slave devices */
	write_register(0, IOCON, IOCON_DEFAULT_VALUE);

	/* Initialize all registers  on all slave devices */
	for(i=0; i<MAX_DEVICES; i++)
	{
		for(j=0; j<NUM_REGISTERS; j++)
		{
			switch(j)
			{
				case IOCON:
					gconfig.chips[i].port[j] = IOCON_DEFAULT_VALUE;
					break;
				case IODIRA:
				case IODIRB:
					gconfig.chips[i].port[j] = IODIR_DEFAULT_VALUE;
					break;
				default:
					gconfig.chips[i].port[j] = REG_DEFAULT_VALUE;
			}

			write_register(i, j, gconfig.chips[i].port[j]);
		}
	}
}

/* Detects the number of active slaves devices */
uint8_t mcp23s17_chip_count(void)
{
	uint8_t i = 0;

	for(i=0; i<MAX_DEVICES; i++)
	{
		if(read_register(i, IOCON) != IOCON_DEFAULT_VALUE)
		{
			break;
		}
	}

	return i;
}

/* Initializes all available pins in the gconfig.pins data structure array */
void init_pins(void)
{
        uint8_t i = 0;

        for(i=0; i<gconfig.num_pins; i++)
        {
                gconfig.pins[i].inuse = 1;
                gconfig.pins[i].active = 1;
                gconfig.pins[i].addr = (i / PINS_PER_DEVICE);
                gconfig.pins[i].bit = (i - (gconfig.pins[i].addr * PINS_PER_DEVICE));

                if(gconfig.pins[i].bit >= PINS_PER_REGISTER)
                {
                        gconfig.pins[i].bit -= PINS_PER_REGISTER;
                        gconfig.pins[i].reg = GPIOB;
                }
                else
                {
                        gconfig.pins[i].reg = GPIOA;
                }
        }
}

/* Writes val to the reg register on the MCP23S17 chip configured with the addr hardware address */
void write_register(uint8_t addr, uint8_t reg, uint8_t val)
{
	spi_select();
	spi_write_byte(OPCODE | (addr << 1) | REG_WRITE);
	spi_write_byte(reg);
	spi_write_byte(val);
	spi_release();
}

/* Reads the current value of the reg register from teh MCP23S17 chip configured with teh addr hardware address */
uint8_t read_register(uint8_t addr, uint8_t reg)
{
	uint8_t value = 0;

	spi_select();
	spi_write_byte(OPCODE | (addr << 1) | REG_READ);
	spi_write_byte(reg);
	value = spi_read_byte();
	spi_release();

	return value;
}

/* Get the status of a specific pin. Returns 1 for high, 0 for low. */
uint8_t get_pin(uint8_t p)
{
	return (read_register(gconfig.pins[p].addr, gconfig.pins[p].reg) & gconfig.pins[p].bit);
}

/* Set the specified pins high (hl = 1) or low (hl = 0) */
void set_pins(uint8_t pins[], uint8_t n, uint8_t hl)
{
        uint8_t i = 0;

        for(i=0; i<n; i++)
        {
                if(hl)
                {
                        set_pin_high(pins[i]);
                }
                else
                {
                        set_pin_low(pins[i]);
                }
        }
}

/* Set the specified pin high */
void set_pin_high(uint8_t p)
{
        if(gconfig.pins[p].inuse)
        {
                gconfig.chips[gconfig.pins[p].addr].port[gconfig.pins[p].reg] |= (1 << gconfig.pins[p].bit);
        }
}

/* Set the specified pin low */
void set_pin_low(uint8_t p)
{
        if(gconfig.pins[p].inuse)
        {
                gconfig.chips[gconfig.pins[p].addr].port[gconfig.pins[p].reg] &= ~(1 << gconfig.pins[p].bit);
        }
}

/* Set a list of pins low */
void set_pins_low(uint8_t pins[], uint8_t n)
{
        set_pins(pins, n, 0);
}

/* Set a list of pins high */
void set_pins_high(uint8_t pins[], uint8_t n)
{
        set_pins(pins, n, 1);
}

/* Set a pin high (hl = 1) or low (hl = 0) immediately */
void set_pin_immediate(uint8_t p, uint8_t hl)
{
        if(hl)
        {
                set_pin_high(p);
        }
        else
        {
                set_pin_low(p);
        }

        write_register(gconfig.pins[p].addr, gconfig.pins[p].reg, gconfig.chips[gconfig.pins[p].addr].port[gconfig.pins[p].reg]);
}

/* Configure a pin as an input (rw = 'r') or an output (rw = 'w') */
void configure_pin(uint8_t p, uint8_t rw)
{
        uint8_t ddr = 0;

        if(!gconfig.pins[p].inuse)
        {
                return;
        }

        if(gconfig.pins[p].reg == GPIOA)
        {
                ddr = IODIRA;
        }
        else if(gconfig.pins[p].reg == GPIOB)
        {
                ddr = IODIRB;
        }
        else
        {
                return;
        }

        if(rw == 'r')
        {
                gconfig.chips[gconfig.pins[p].addr].port[ddr] |= (1 << gconfig.pins[p].bit);
        }
        else if(rw == 'w')
        {
                gconfig.chips[gconfig.pins[p].addr].port[ddr] &= ~(1 << gconfig.pins[p].bit);
        }
}

/* Configure a pin as an output immediately, without needing to call commit_ddr_settings(). */
void configure_pin_immediate(uint8_t pin, uint8_t rw)
{
	uint8_t ddr = 0;

	configure_pin(pin, rw);

	if(gconfig.pins[pin].reg == GPIOA)
	{
		ddr = IODIRA;
	}
	else
	{
		ddr = IODIRB;
	}

	write_register(gconfig.pins[pin].addr, ddr, gconfig.chips[gconfig.pins[pin].addr].port[ddr]);
}

/* Configure a list of pins as inputs (rw = 'r') or low (rw = 'w') */
void configure_pins(uint8_t pins[], uint8_t n, uint8_t rw)
{
        uint8_t i = 0;

        for(i=0; i<n; i++)
        {
                if(rw == 'w')
                {
                        configure_pin_as_output(pins[i]);
                }
                else if(rw == 'r')
                {
                        configure_pin_as_input(pins[i]);
                }
        }
}

/* Configure the specified pin as an output pin */
void configure_pin_as_output(uint8_t p)
{
        configure_pin(p, 'w');
}

/* Configure a list of pins as output pins */
void configure_pins_as_outputs(uint8_t pins[], uint8_t n)
{
        configure_pins(pins, n, 'w');
}

/* Configure a pin as an input pin */
void configure_pin_as_input(uint8_t p)
{
        configure_pin(p, 'r');
}

/* Configure a list of pins as input pins */
void configure_pins_as_inputs(uint8_t pins[], uint8_t n)
{
        configure_pins(pins, n, 'r');
}

/* Commit the current settings for the specified registers to all I/O chips */
void commit_settings(uint8_t device, uint8_t reg)
{
        write_register(device, reg, gconfig.chips[device].port[reg]);
}

/* Commit GPIO settings */
void commit_io_settings(void)
{
        uint8_t i = 0;

        for(i=0; i<gconfig.num_io_devices; i++)
        {
                commit_settings(i, GPIOA);
                commit_settings(i, GPIOB);
        }
}

/* Commit IODIR settings */
void commit_ddr_settings(void)
{
        uint8_t i = 0;

        for(i=0; i<gconfig.num_io_devices; i++)
        {
                commit_settings(i, IODIRA);
                commit_settings(i, IODIRB);
        }
}

