#ifndef __COMMON_H__
#define __COMMON_H__

#include <avrlib/uart.h>

#define BOARD_ID "GUMBI v1"

#define TRUE 1
#define FALSE 0

#define ACK "ACK"
#define NACK "NACK"

#define SPEED_TEST_SIZE 65535

#define MAX_PINS 64
#define NUM_DEVICES 4
#define PINS_PER_DEVICE 16
#define PINS_PER_REGISTER 8
#define NUM_REGISTERS 0x16

enum registers
{ 
        IODIRA   = 0x00,
        IODIRB   = 0x01,
	IPOLA    = 0x02,
	IPOLB    = 0x03,
	GPINTENA = 0x04,
	GPINTENB = 0x05,
	DEFVALA  = 0x06,
	DEFVALB  = 0x07,
	INTCONA  = 0x08,
	INTCONB  = 0x09,
        IOCONA   = 0x0A,
	IOCONB   = 0x0B,
        GPPUA    = 0x0C,
        GPPUB    = 0x0D,
	INTFA    = 0x0E,
	INTFB    = 0x0F,
	INTCAPA  = 0x10,
	INTCAPB  = 0x11,
        GPIOA    = 0x12,
        GPIOB    = 0x13,
	OLATA    = 0x14,
	OLATB    = 0x15
};
#define IOCON IOCONA

enum modes
{
	NOP = 0,
	PFLASH = 1,
	SPIFLASH = 2,
	SPIEEPROM = 3,
	I2CEEPROM = 4,
	PING = 5,
	DEBUG = 6,
	SPEED = 7,
	IO = 8
};

enum actions
{
	READ = 1,
	WRITE = 2,
	ERASE = 3
};

struct pin
{
        uint8_t addr;				/* Address of the I/O expansion chip this pin is located on */
        uint8_t reg;				/* The GPIO register this pin is located on (GPIOA/GPIOB) */
        uint8_t bit;				/* The bit (0-7) in the GPIO register that represents this pin */
	uint8_t inuse;				/* Set to 1 if the pin is in use, 0 if not */
	uint8_t active;				/* The active state (1, 0) of the pin, mostly used for control pins */
};

struct device
{
        uint8_t port[NUM_REGISTERS];
};

struct config
{
        enum actions action;			/* Are we reading? Writing? Erasing? */
        uint32_t addr;				/* What is the start address? */
        uint32_t count;				/* How many bytes? */
	uint16_t num_addr_pins;
        uint16_t num_data_pins;
        uint16_t num_vcc_pins;
        uint16_t num_gnd_pins;
        struct pin addr_pins[MAX_PINS];
        struct pin data_pins[MAX_PINS];
        struct pin vcc_pins[MAX_PINS];
        struct pin gnd_pins[MAX_PINS];
        struct pin ce_pin;			/* Chip Enable */
        struct pin we_pin;			/* Write Enable */
        struct pin oe_pin;			/* Output Enable */
	struct pin be_pin;			/* Byte Enable */
	struct pin by_pin;			/* Ready / Busy */
	struct pin wp_pin;			/* Write Protect */
	struct pin rst_pin;			/* Reset */
};

struct command
{
        enum modes mode;
        struct config configuration;
};

struct config *gconfig;
struct device chips[NUM_DEVICES];


void ack(void);
void nack(void);
uint8_t is_valid_pin(struct pin *p);
uint8_t are_valid_pins(struct pin pins[]);
uint8_t validate_gconfig(void);

#endif
