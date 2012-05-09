#ifndef __MCP23S17_H__
#define __MCP23S17_H__

#include "common.h"
#include <avrlib/spi.h>

#define REG_READ 1
#define REG_WRITE 0
#define OPCODE 0x40
#define IOCON_DEFAULT_VALUE 0x38
#define IODIR_DEFAULT_VALUE 0xFF
#define REG_DEFAULT_VALUE 0x00

void mcp23s17_init(void);
void mcp23s17_enable(void);
void mcp23s17_disable(void);
void mcp23s17_io_init(void);
uint8_t mcp23s17_chip_count(void);
void init_pins(void);
uint8_t read_register(uint8_t addr, uint8_t reg);
void write_register(uint8_t addr, uint8_t reg, uint8_t val);
uint8_t pin_ddr_port(uint8_t p);
uint8_t is_high(uint8_t p);
uint8_t is_output(uint8_t p);
uint8_t get_pin(uint8_t p);
uint8_t set_pin_high(uint8_t p);
uint8_t set_pin_low(uint8_t p);
void set_pins_high(uint8_t pins[], uint8_t n);
void set_pins_low(uint8_t pins[], uint8_t n);
void commit_settings(uint8_t device, uint8_t reg);
void commit_io_settings(void);
void commit_ddr_settings(void);
void set_pin_immediate(uint8_t p, uint8_t hl);
uint8_t configure_pin(uint8_t p, uint8_t rw);
void configure_pin_immediate(uint8_t pin, uint8_t rw);
void configure_pin_as_output(uint8_t p);
void configure_pins_as_outputs(uint8_t pins[], uint8_t pin_count);
void configure_pin_as_input(uint8_t p);
void configure_pins_as_inputs(uint8_t pins[], uint8_t pin_count);

#endif
