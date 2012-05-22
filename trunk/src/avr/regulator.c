#include "regulator.h"

/* Initialize regulators; defaults to 4.7v */
void regulator_init(void)
{
	REGULATOR_DDR |= (1 << V47_PIN) | (1 << V30_PIN) | (1 << V18_PIN);

	/* Default to 4.7v */
	set_regulator(V47);
}

/* Handler for the VOLTAGE command */
void voltage(void)
{
	uint8_t v = 0;

	read_data((uint8_t *) &v, sizeof(v));
	set_regulator(v);
	ack();
}

/* Enable the appropriate regulator */
void set_regulator(uint8_t voltage)
{
	/* Disable all voltage regulators */
	REGULATOR_PORT &= ~(1 << V47_PIN) & ~(1 << V30_PIN) & ~(V18_PIN);

	/* Enable the selected regulator */
	switch(voltage)
	{
		case V47:
			REGULATOR_PORT |= (1 << V47_PIN);
			break;
		case V30:
			REGULATOR_PORT |= (1 << V30_PIN);
			break;
		case V18:
			REGULATOR_PORT |= (1 << V18_PIN);
			break;
		case V0:
		default:
			break;
	}
}
