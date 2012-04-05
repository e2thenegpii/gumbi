#ifndef __PARALLEL_H__
#define __PARALLEL_H__

#include "common.h"

void parallel_flash(void);
void set_control_pin(struct ctrlpin p, uint8_t tf);
void output_enable(uint8_t tf);
void write_enable(uint8_t tf);
void chip_enable(uint8_t tf);
void reset_enable(uint8_t tf);
void byte_enable(uint8_t tf);
void commit_address_settings(void);
void commit_data_settings(void);
uint16_t read_data_word(void);
void set_address(uint32_t address);
void parallel_read(void);
void parallel_write(void);

#endif
