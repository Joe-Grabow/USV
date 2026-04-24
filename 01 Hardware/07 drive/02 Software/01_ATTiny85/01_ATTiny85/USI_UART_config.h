//********** USI UART Defines **********//

#ifndef USI_UART_CONFIG_H_
	#define USI_UART_CONFIG_H_

#ifndef F_CPU
	#define F_CPU	8000000UL
#endif

#define BAUDRATE	9600			/* 9600 OR 19200 */

#define UART_RX_BUFFER_SIZE	16		/* 2,4,8,16,32 or 64 bytes */
#define UART_TX_BUFFER_SIZE 16


//********** USI_UART Prototypes **********//

void	USI_UART_Flush_Buffers(void);
void	USI_UART_Initialise_Receiver(void);
uint8_t USI_UART_Receive_Byte(void);
uint8_t USI_UART_Data_In_Receive_Buffer(void);
void	USI_UART_Transmit_Byte(uint8_t);

#endif /* USI_UART_CONFIG_H_ */