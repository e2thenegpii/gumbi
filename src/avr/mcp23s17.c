#include <avr/io.h>

#include "avrlib/spi.h"
#include "common.h"
#include "mcp23s17.h"

void mcp23s17_init(void)
{
	RESET_DDR |= (1 << RESET_PIN);
	mcp23s17_chip_reset(TRUE);
}

void mcp23s17_chip_reset(uint8_t rst)
{
	if(rst == TRUE)
	{
		RESET_PORT &= ~(1 << RESET_PIN);
	}
	else
	{
		RESET_PORT |= (1 << RESET_PIN);
	}
}

void mcp23s17_enable(void)
{
	/* Bring the I/O chips out of their reset state */
	mcp23s17_chip_reset(FALSE);

	/* Initialize SPI */
	spi_init(SPI_MODE_0, SPI_MSB, SPI_NO_INTERRUPT, SPI_MSTR_CLK4, SPI_SS_IDLE_HIGH);

	/* Initialize I/O expansion chips */
	io_init();
}

void mcp23s17_disable(void)
{
	io_init();
	//mcp23s17_chip_reset(TRUE);
	spi_disable();
}

void io_init(void)
{
	uint8_t i = 0, j = 0;

	/* Set IOCON value on all un-initialized slave devices */
	write_register(0, IOCON, IOCON_DEFAULT_VALUE);

	/* Initialize all registers */
	for(i=0; i<NUM_DEVICES; i++)
	{
		for(j=0; j<NUM_REGISTERS; j++)
		{
			switch(j)
			{
				case IOCON:
					chips[i].port[j] = IOCON_DEFAULT_VALUE;
					break;
				case IODIRA:
				case IODIRB:
					chips[i].port[j] = IODIR_DEFAULT_VALUE;
					break;
				default:
					chips[i].port[j] = REG_DEFAULT_VALUE;
			}

			write_register(i, j, chips[i].port[j]);
		}
	}
}

void write_register(uint8_t addr, uint8_t reg, uint8_t val)
{
	spi_select();
	spi_write_byte(OPCODE | (addr << 1) | REG_WRITE);
	spi_write_byte(reg);
	spi_write_byte(val);
	spi_release();
}

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
uint8_t get_pin(struct pin *p)
{
	return (read_register(p->addr, p->reg) & p->bit);
}

/* Set the specified pins high (hl = 1) or low (hl = 0) */
void set_pins(struct pin pins[], uint8_t n, uint8_t hl)
{
        uint8_t i = 0;

        for(i=0; i<n; i++)
        {
                if(hl)
                {
                        set_pin_high(&pins[i]);
                }
                else
                {
                        set_pin_low(&pins[i]);
                }
        }
}

/* Set the specified pin high */
void set_pin_high(struct pin *p)
{
        if(p->inuse)
        {
                chips[p->addr].port[p->reg] |= (1 << p->bit);
        }
}

/* Set the specified pin low */
void set_pin_low(struct pin *p)
{
        if(p->inuse)
        {
                chips[p->addr].port[p->reg] &= (1 << p->bit);
        }
}

/* Set a list of pins low */
void set_pins_low(struct pin pins[], uint8_t n)
{
        set_pins(pins, n, 0);
}

/* Set a list of pins high */
void set_pins_high(struct pin pins[], uint8_t n)
{
        set_pins(pins, n, 1);
}

/* Set a pin high (hl = 1) or low (hl = 0) immediately */
void set_pin_immediate(struct pin *p, uint8_t hl)
{
        if(hl)
        {
                set_pin_high(p);
        }
        else
        {
                set_pin_low(p);
        }

        write_register(p->addr, p->reg, chips[p->addr].port[p->reg]);
}

/* Configure a pin as an input (rw = 'r') or an output (rw = 'w') */
void configure_pin(struct pin *p, uint8_t rw)
{
        uint8_t ddr = 0;

        if(!p->inuse)
        {
                return;
        }

        if(p->reg == GPIOA)
        {
                ddr = IODIRA;
        }
        else if(p->reg == GPIOB)
        {
                ddr = IODIRB;
        }
        else
        {
                return;
        }

        if(rw == 'r')
        {
                chips[p->addr].port[ddr] |= (1 << p->bit);
        }
        else if(rw == 'w')
        {
                chips[p->addr].port[ddr] &= ~(1 << p->bit);
        }
}

/* Configure a list of pins as inputs (rw = 'r') or low (rw = 'w') */
void configure_pins(struct pin pins[], uint8_t n, uint8_t rw)
{
        uint8_t i = 0;

        for(i=0; i<n; i++)
        {
                if(rw == 'w')
                {
                        configure_pin_as_output(&pins[i]);
                }
                else if(rw == 'r')
                {
                        configure_pin_as_input(&pins[i]);
                }
        }
}

/* Configure the specified pin as an output pin */
void configure_pin_as_output(struct pin *p)
{
        configure_pin(p, 'w');
}

/* Configure a list of pins as output pins */
void configure_pins_as_outputs(struct pin pins[], uint8_t n)
{
        configure_pins(pins, n, 'w');
}

/* Configure a pin as an input pin */
void configure_pin_as_input(struct pin *p)
{
        configure_pin(p, 'r');
}

/* Configure a list of pins as input pins */
void configure_pins_as_inputs(struct pin pins[], uint8_t n)
{
        configure_pins(pins, n, 'r');
}

/* Commit the current settings for the specified registers to all I/O chips */
void commit_settings(uint8_t device, uint8_t reg)
{
        write_register(device, reg, chips[device].port[reg]);
}

/* Commit GPIO settings */
void commit_io_settings(void)
{
        uint8_t i = 0;

        for(i=0; i<NUM_DEVICES; i++)
        {
                commit_settings(i, GPIOA);
                commit_settings(i, GPIOB);
        }
}

/* Commit IODIR settings */
void commit_ddr_settings(void)
{
        uint8_t i = 0;

        for(i=0; i<NUM_DEVICES; i++)
        {
                commit_settings(i, IODIRA);
                commit_settings(i, IODIRB);
        }
}

