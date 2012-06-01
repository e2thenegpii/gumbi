#ifndef __REGULATOR_H__
#define __REGULATOR_H__

#include "common.h"

#define REGULATOR_DDR DDRC
#define REGULATOR_PORT PORTC
#define V18_PIN PC5
#define V30_PIN PC4
#define V47_PIN PC3

void voltage(void);
void regulator_init(void);
void set_regulator(uint8_t voltage);
uint8_t get_regulator(void);

#endif
