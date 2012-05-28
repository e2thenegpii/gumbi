#ifndef __DEBUG_H__
#define __DEBUG_H__

#include "common.h"
#include "mcp23s17.h"
#include "regulator.h"

void nop(void);
void id(void);
void ping(void);
void info(void);
void scan_bus(void);
void set_pin_count(void);
void get_pin_count(void);
void speed_test(void);
void xfer_test(void);

#endif
