#ifndef __UART_H__
#define __UART_H__

/*
 * Simple UART library for non-interrupt driven access to UART0 on AVR microcontrollers. 
 *
 * Set the baudrate by defining BAUD (defaults to 9600).
 *
 * By default, most serial terminals require \r\n instead of \n for new lines. 
 * Define CRFL_COMPAT to automatically add a \r in front of any \n's for compatability with functions like puts().
 */

#include <stdio.h>
#include <stdlib.h>
#include <avr/io.h>

/* If not already defined, try to identify the UART ports for the target AVR chip */
#ifndef UART0_CONTROL
	#if defined(UCSR0B)
		#define UART0_STATUS UCSR0A
		#define UART0_CONTROL UCSR0B
		#define UART0_FRAME UCSR0C
		#define UART0_UBRRH UBRR0H
		#define UART0_UBRRL UBRR0L
		#define UART0_DATA UDR0
		#define UART0_RX_ENABLE RXEN0
		#define UART0_TX_ENABLE TXEN0
		#define UART0_DATA_BIT1 UCSZ00
		#define UART0_DATA_BIT2 UCSZ01
		#define UART0_RX_READY RXC0
		#define UART0_TX_READY UDRE0
	#elif defined(UCSRB)
		#define UART0_STATUS UCSRA
		#define UART0_CONTROL UCSRB
		#define UART0_FRAME UCSRC
		#define UART0_UBRRH UBRRH
		#define UART0_UBRRL UBRRL
		#define UART0_DATA UDR
		#define UART0_RX_ENABLE RXEN
		#define UART0_TX_ENABLE TXEN
		#define UART0_DATA_BIT1 UCSZ0
		#define UART0_DATA_BIT2 UCSZ1
		#define UART0_RX_READY RXC
		#define UART0_TX_READY UDRE
	#else
		#error : Unknown UART ports! Please define in uart.h.
	#endif // defined(UCSR0B) 
#endif // UCSR_PORTB

/* 
 * Initializes UART0 at 8 bits, no stop bits, 1 parity bit, in non-interrupt mode.
 *
 */
void uart_init(void);

/*
 * Reads and returns one byte from UART0. This is a blocking operation.
 */
uint8_t uart_read_byte(void);

/* 
 * Writes one byte to UART0. This is a blocking operation.
 */
void uart_write_byte(uint8_t byte);

/*
 * Handles stdout/stderr redirection to UART0. For internal use only; see dup2uart.
 */
int uart_putchar(char c, FILE *stream);

/* 
 * Handles stdin redirection from UART0. For internal use only; see dup2uart.
 */
int uart_getchar(FILE *stream);

/*
 * Redirects stdin, stdout, and stderr to UART0.
 * This allows you to use printf, scanf, etc to read and write to UART0.
 */
void dup2uart(void);

#endif
