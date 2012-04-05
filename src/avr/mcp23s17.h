#ifndef __MCP23S17_H__
#define __MCP23S17_H__

#include "common.h"

#define REG_READ 1
#define REG_WRITE 0
#define OPCODE 0x40
#define IOCON_DEFAULT_VALUE 0x38
#define IODIR_DEFAULT_VALUE 0xFF
#define REG_DEFAULT_VALUE 0x00

void mcp23s17_init(void);
void mcp23s17_disable(void);
void io_init(void);
uint8_t read_register(uint8_t addr, uint8_t reg);
void write_register(uint8_t addr, uint8_t reg, uint8_t val);
void set_pin_high(struct pin *p);
void set_pin_low(struct pin *p);
void set_pins_high(struct pin pins[], uint8_t n);
void set_pins_low(struct pin pins[], uint8_t n);
void commit_settings(uint8_t device, uint8_t reg);
void commit_io_settings(void);
void commit_ddr_settings(void);
void set_pin_immediate(struct pin *p, uint8_t hl);
void configure_pin(struct pin*p, uint8_t rw);
void configure_pin_as_output(struct pin *p);
void configure_pins_as_outputs(struct pin pins[], uint8_t pin_count);
void configure_pin_as_input(struct pin *p);
void configure_pins_as_inputs(struct pin pins[], uint8_t pin_count);

#endif
