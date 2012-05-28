#ifndef __COMMAND_H__
#define __COMMAND_H__

#include <util/delay.h>
#include <avr/power.h>
#include <avr/wdt.h>
#include "common.h"

void ping(void);
void info(void);
void speed_test(void);
void command_handler(uint8_t mode);

#endif
