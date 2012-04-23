#ifndef __SOFT_SPI_H__
#define __SOFT_SPI_H__

#include "common.h"
#include "mcp23s17.h"

void spi(void);
uint8_t validate_spi_config(void);
void soft_spi_write_byte(uint8_t byte);
uint8_t soft_spi_read_byte(void);
void soft_spi_read(void);
void soft_spi_write(void);
void ss_active(uint8_t tf);
void clk_active(uint8_t tf);
void mosi_active(uint8_t tf);
void miso_active(uint8_t tf);

#endif
