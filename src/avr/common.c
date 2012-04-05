#include "common.h"

void ack(void)
{
	printf("%s\r\n", ACK);
}

void nack(void)
{
	printf("%s\r\n", NACK);
}

uint8_t is_valid_pin(struct pin *p)
{
        uint8_t ok = FALSE;

        if(p->inuse)
        {
                if(p->addr < NUM_DEVICES)
                {
                        if(p->reg < NUM_REGISTERS)
                        {
                                if(p->bit < PINS_PER_REGISTER)
                                {
                                        ok = TRUE;
                                }
                        }
                }
        }
        else
        {
                ok = TRUE;
        }

        return ok;
}

uint8_t are_valid_pins(struct pin pins[])
{
        uint8_t i = 0, ok = TRUE;

        for(i=0; i<MAX_PINS; i++)
        {
                if(!is_valid_pin(&pins[i]))
                {
                        ok = FALSE;
                        break;
                }
        }

        return ok;
}

uint8_t validate_gconfig(void)
{
        uint8_t ok = FALSE;

	if(gconfig != NULL)
	{
		ok = TRUE;

        	ok &= are_valid_pins(gconfig->addr_pins);
        	ok &= are_valid_pins(gconfig->data_pins);
        	ok &= are_valid_pins(gconfig->vcc_pins);
        	ok &= are_valid_pins(gconfig->gnd_pins);

        	ok &= is_valid_pin(&gconfig->ce_pin);
        	ok &= is_valid_pin(&gconfig->we_pin);
        	ok &= is_valid_pin(&gconfig->oe_pin);
        	ok &= is_valid_pin(&gconfig->be_pin);
        	ok &= is_valid_pin(&gconfig->by_pin);
        	ok &= is_valid_pin(&gconfig->wp_pin);
        	ok &= is_valid_pin(&gconfig->rst_pin);
	}
        
	return ok;
}

