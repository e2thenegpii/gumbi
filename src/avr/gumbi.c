#include <avr/io.h>
#include <string.h>

#include "common.h"
#include "command.h"
#include "mcp23s17.h"

int main(void)
{
	uint8_t data[sizeof(struct command)] = { 0 };
	uint16_t i = 0, data_size = sizeof(struct command);

	/* Initialize the MCP23S17 chips */	
	mcp23s17_init();

	/* Initialize UART comms with the PC */
	uart_init();
	dup2uart();

	printf("%s\r\n", BOARD_ID);
//	printf("Waiting for %d bytes of command data...\r\n", data_size);

	while(TRUE)
	{
		memset(&data, 0, data_size);

		for(i=0; i<data_size; i++)
		{
//			printf("%d/%d\r\n", i, data_size);
			data[i] = getchar();
		}

		/* Pass command data off to command_handler */
		command_handler((struct command *) &data);
	}

	return 0;
}
