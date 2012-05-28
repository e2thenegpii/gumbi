#include "common.h"
#include "mcp23s17.h"

void led_init(void)
{
	LED_DDR |= (1 << LED_PIN);
	led_off();
}

void led_on(void)
{
	LED_PORT |= (1 << LED_PIN);
}

void led_off(void)
{
	LED_PORT &= ~(1 << LED_PIN);
}

void toggle_led(void)
{
	LED_PORT ^= (1 << LED_PIN);
}

/* Send an ACK. */
void ack(void)
{
	fprintf(&gconfig.usb, "%s\n", ACK);
}

/* Send a NACK. */
void nack(void)
{
	fprintf(&gconfig.usb, "%s\n", NACK);
}

/* Delay for x number of seconds */
void sleep(uint8_t seconds)
{
	uint8_t i = 0, j = 0;

	for(i=0; i<seconds; i++)
	{
		for(j=0; j<10; j++)
		{
			_delay_ms(100);
		}
	}
}

/* Read size bytes of data into buffer from USB HID endpoint */
void read_data(uint8_t *buffer, uint32_t size)
{
	uint32_t i = 0;

	for(i=0; i<size; i++)
	{
		buffer[i] = fgetc(&gconfig.usb);
	}
}

/* Check if the specified pin number is a valid pin. Returns TRUE if valid, FALSE if invalid. */
uint8_t is_valid_pin(uint8_t p)
{
	uint8_t ok = FALSE;

	if(p >= 0 && p < gconfig.num_pins && gconfig.pins[p].inuse)
	{
		ok = TRUE;
	}

	return ok;
}

/* Check if an array of pin numbers are all valid. Returns FALSE if one or more pins in the array are not valid. */
uint8_t are_valid_pins(uint8_t pins[], uint8_t count)
{
	uint8_t i = 0, ok = TRUE;

	for(i=0; i<count; i++)
	{
		if(!is_valid_pin(pins[i]))
		{
			ok = FALSE;
			break;
		}
	}

	return ok;
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
