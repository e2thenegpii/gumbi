#include "common.h"

void ack(void)
{
	printf("%s\r\n", ACK);
}

void nack(void)
{
	printf("%s\r\n", NACK);
}

uint8_t *read_data(uint32_t size)
{
	uint32_t i = 0;
	uint8_t *data = NULL;

	data = malloc(size);
	if(data)
	{
		memset(data, 0, size);
		
		for(i=0; i<size; i++)
		{
			data[i] = getchar();
		}
	}
	
	return data;
}

uint8_t is_valid_pin(uint8_t p)
{
        uint8_t ok = FALSE;

        if(gconfig.pins[p].inuse)
        {
		ok = TRUE;
        }

        return ok;
}

uint8_t are_valid_pins(uint8_t pins[])
{
        uint8_t i = 0, ok = TRUE;

        for(i=0; i<MAX_PINS; i++)
        {
                if(!is_valid_pin(pins[i]))
                {
                        ok = FALSE;
                        break;
                }
        }

        return ok;
}
