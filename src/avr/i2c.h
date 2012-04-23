#ifndef __SOFT_I2C_H__
#define __SOFT_I2C_H__

#include "common.h"
#include "mcp23s17.h"

void i2c(void);
void soft_i2c_start(void);
void soft_i2c_stop(void);
uint8_t soft_i2c_read_byte(void);
void soft_i2c_write_byte(uint8_t byte);
void soft_i2c_write(void);
void soft_i2c_read(void);

#endif
