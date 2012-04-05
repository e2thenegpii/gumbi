#include "uart.h"

#ifndef BAUD
#warning : BAUD not defined in uart.c; defaulting to 9600 baud.
#define BAUD 9600
#endif

#include <util/setbaud.h>

/* FILE stream used to redirect stdout, stderr and stdin. */
FILE uart_stream = FDEV_SETUP_STREAM(uart_putchar, uart_getchar, _FDEV_SETUP_RW);
FILE *uart = &uart_stream;

void uart_init(void)
{
	/* Enable receive and transmit operations on UART0 */
	UART0_CONTROL = ((1 << UART0_RX_ENABLE) | (1 << UART0_TX_ENABLE));
	/* Set frame properties to 8N1 */
        UART0_FRAME = ((1 << UART0_DATA_BIT1) | (1 << UART0_DATA_BIT2));

	/* Define the baudrate prescaling */
        UART0_UBRRH = UBRRH_VALUE;
        UART0_UBRRL = UBRRL_VALUE;
}

uint8_t uart_read_byte(void)
{
	/* Wait until there's a byte ready to read, then return it */
	while((UART0_STATUS & (1 << UART0_RX_READY)) == 0) { }
	return UART0_DATA;
}

void uart_write_byte(uint8_t byte)
{
	/* Wait until the uC is ready to transmit a byte, then send it */
	while((UART0_STATUS & (1 << UART0_TX_READY)) == 0) { }
	UART0_DATA = byte;
}

int uart_putchar(char c, FILE *stream)
{
#ifdef CRLF_COMPAT
	if(c == '\n') uart_putchar('\r', stream);
#endif
	uart_write_byte(c);
	return 0;
}

int uart_getchar(FILE *stream)
{
	return uart_read_byte();
}

void dup2uart(void)
{
	/* Redirect stdin, stdout and stderr to uart */
	stdout = uart;
	stderr = uart;
	stdin = uart;
}
