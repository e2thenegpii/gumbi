#ifndef __COMMON_H__
#define __COMMON_H__

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <avr/io.h>
#include <util/delay.h>

#define BOARD_ID "GUMBI v1.1"
#define FIRMWARE_ID "0.9"

#define TRUE 1
#define FALSE 0

#define ACK "A"
#define NACK "N"

#define BLOCK_SIZE 64
#define DUMMY_BYTE 0xFF
#define XFER_TEST_SIZE 128
#define LED_TOGGLE_INTERVAL 128

#define LED_DDR DDRB
#define LED_PORT PORTB
#define LED_PIN PB4
#define LED_XOR PINB

#define MAX_PINS 128
#define MIN_DEVICES 4
#define MAX_DEVICES 8
#define MAX_COMMANDS 32
#define MAX_GPIO_COMMANDS 31

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
	PARALLEL = 1,
	PING = 2,
	INFO = 3,
	SPEEDTEST = 4,
	GPIO = 5,
	GID = 6,
	XFER = 7,
	GETPINCOUNT = 8,
	SETPINCOUNT = 9,
	SCANBUS = 10,
	MONITOR = 11,
	VOLTAGE = 12
};

enum actions
{
	EXIT = 0,
	READ = 1,
	WRITE = 2,
	HIGH = 3,
	LOW = 4,
	COMMAND = 5
};

enum voltages
{
	V0  = 0x00,
	V18 = 0x18,
	V30 = 0x30,
	V47 = 0x47
};

struct pin
{
	uint8_t addr;				/* Address of the I/O expansion chip this pin is located on */
	uint8_t reg;				/* The GPIO register this pin is located on (GPIOA/GPIOB) */
	uint8_t bit;				/* The bit (0-7) in the GPIO register that represents this pin */
	uint8_t inuse;				/* Set to 1 if the pin is in use, 0 if not */
	uint8_t active;				/* The active state (1, 0) of the pin, mostly used for control pins */
};

struct io
{
	enum actions action;
	uint8_t pin;
};

struct device
{
	uint8_t port[NUM_REGISTERS];
};

struct ctrlpin
{
	uint8_t pin;
	uint8_t active;
};

struct confdata
{
	enum actions action;			/* Are we reading? Writing? Erasing? */
	uint32_t addr;				/* What is the start address? */
	uint32_t count;				/* How many bytes? */
	uint8_t toe;				/* How long to sleep when latching pins (uS) */
	uint8_t tbp;				/* Byte program time (uS) */
	uint8_t cmd_delay;			/* Period to delay (in seconds) after writing commands listed in hconfig.commands */
	uint8_t reconfigure;			/* Re-configure I/O pins (TRUE/FALSE) */
	uint16_t num_addr_pins;
	uint16_t num_data_pins;
	uint16_t num_vcc_pins;
	uint16_t num_gnd_pins;
	uint8_t num_commands;
	uint8_t addr_pins[MAX_PINS];
	uint8_t data_pins[MAX_PINS];
	uint8_t vcc_pins[MAX_PINS];
	uint8_t gnd_pins[MAX_PINS];
	uint32_t commands[MAX_COMMANDS];	/* Data/address commands to send when writing to parallel chips */
	struct ctrlpin ce;			/* Chip Enable */
	struct ctrlpin we;			/* Write Enable */
	struct ctrlpin re;			/* Read Enable */
	struct ctrlpin oe;			/* Output Enable */
	struct ctrlpin be;			/* Byte Enable */
	struct ctrlpin by;			/* Ready / Busy */
	struct ctrlpin wp;			/* Write Protect */
	struct ctrlpin wi;			/* Write Indicator */
	struct ctrlpin ri;			/* Read Indicator */
	struct ctrlpin rst;			/* Reset */
} hconfig;

struct config
{
	uint8_t num_pins;
	uint8_t num_io_devices;
	struct pin pins[MAX_PINS];
	struct device chips[MAX_DEVICES];
	uint8_t buffer[BLOCK_SIZE];
	uint8_t buffer_size;
	uint8_t regulator;
	FILE usb;
} gconfig;

void led_init(void);
void led_on(void);
void led_off(void);
void toggle_led(void);
void ack(void);
void nack(void);
void usleep(uint8_t useconds);
void sleep(uint8_t seconds);
uint8_t is_valid_pin(uint8_t p);
void set_control_pin(struct ctrlpin p, uint8_t tf);
void read_data(uint8_t *buffer, uint32_t count);
uint8_t are_valid_pins(uint8_t pins[], uint8_t count);

#endif
