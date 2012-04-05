#include "common.h"

/* Send an ACK. */
void ack(void)
{
	printf("%s\r\n", ACK);
}

/* Send a NACK. */
void nack(void)
{
	printf("%s\r\n", NACK);
}

/* Read size bytes of data from the PC and return a pointer to the data. Return value must be freed by the caller. */
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

/* Check if the specified pin number is a valid pin. Returns TRUE if valid, FALSE if invalid. */
uint8_t is_valid_pin(uint8_t p)
{
        uint8_t ok = FALSE;

	if(p > 0 && p < gconfig.num_pins)
	{
        	if(gconfig.pins[p].inuse)
        	{
			ok = TRUE;
		}
        }

        return ok;
}

/* Check if an array of pin numbers are all valid. Returns FALSE if one or more pins in the array are not valid. */
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
