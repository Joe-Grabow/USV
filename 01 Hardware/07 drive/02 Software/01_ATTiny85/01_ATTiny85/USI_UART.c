#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>

#include "USI_UART_config.h"


//********** USI UART Defines **********//

#define CYCLES_PER_BIT				(F_CPU / BAUDRATE)							// CPU Cycles per Bit

#if (CYCLES_PER_BIT > 255)														// If CPU cycles for 1 Bit are greater than 255 then divide by 8 to fit in timer.													
	#define TIMER_PRESCALER			8											// Define the prescaler value
	#define CLOCKSELECT				2											// Define the prescaler setting for TCCR0B
#else
	#define TIMER_PRESCALER			1											// Define the prescaler value
	#define CLOCKSELECT				1											// Define the prescaler setting for TCCR0B
#endif

#define FULL_BIT_TICKS				(CYCLES_PER_BIT / TIMER_PRESCALER)			// Timer Cycles for 1 UART Bit: f_CPU=8MHz; (Baudrate=9600 * Prescaler=8) = 104.167

#define OCR0A_FULL					(FULL_BIT_TICKS - 1)						// Output Compare Match Value for One Bit-Width sampling; for Baudrate=9600: 103

#define HALF_BIT_TICKS				(FULL_BIT_TICKS /2 - 1)						// OCRA-Value for 1/2 Bit width sampling; for Baudrate=9600: 51


#define PIN_CHANGE_START_DELAY		99											// Number of CPU cycles from pin change to starting USI Counter

#define TIMER_START_DELAY			(PIN_CHANGE_START_DELAY / TIMER_PRESCALER)	// Number of Timer Cycles from pin change to starting USI Counter; here: 99/8 = 12

#define COMPA_INTERRUPT_DELAY		42											// Number of CPU cycles from Starting Timer0 until first COMPA Match can generate interrupt

#define TIMER_MIN					(COMPA_INTERRUPT_DELAY / TIMER_PRESCALER)	// min. value for OCR0A; here: 42/8 = 5

#if ((HALF_BIT_TICKS - TIMER_START_DELAY)>0)									// Check, if OCR0A-Value for 1/2 Bit minus Timer start delay is positive
	#define OCR0A_FIRST				(HALF_BIT_TICKS - TIMER_START_DELAY)		// OCR0A-Value for first Bit sampling until Output Compare Match Interrupt; here: 51 - 12 = 39
	
	#if (OCR0A_FIRST < TIMER_MIN)												// Check, if OCR0A-Value for first Bit sampling is greater than min. value for OCR0A
		#warning OCR0A_FIRST too low, USI bit sample will after center of bit
#endif
#else
	#error "OCR0A_FIRST invalid, choose different values for F_CPU, BAUDRATE and PIN_CHANGE_START_DELAY"
	#define OCR0A_FIRST				1
#endif

// Define of Bit sizes
#define DATA_BITS					8
#define HIGH_BIT					1
#define START_BIT					1
#define STOP_BIT					1

// Define of Frame sizes
#define FIRST_FRAME_RX				(DATA_BITS - HIGH_BIT - START_BIT)			// 6
#define SECOND_FRAME_RX				(DATA_BITS - FIRST_FRAME_RX + STOP_BIT)		// 3

#define FIRST_FRAME_TX				7											// (HIGH_BIT + START_BIT + 5 LSB of data)
#define SECOND_FRAME_TX				(DATA_BITS - (FIRST_FRAME_TX - HIGH_BIT - START_BIT) + STOP_BIT)
																				// 4 (=8-(7-1-1)+1)

// Define of USI Counter values
#define USI_COUNTER_MAX_COUNT		16
#define USI_COUNTER_SEED_RX_FIRST	(USI_COUNTER_MAX_COUNT - FIRST_FRAME_RX)	// 10; Start value for USI Counter for RX first
#define USI_COUNTER_SEED_RX_SECOND	(USI_COUNTER_MAX_COUNT - SECOND_FRAME_RX)	// 13; Start value for USI Counter for RX second
#define USI_COUNTER_SEED_TX_FIRST	(USI_COUNTER_MAX_COUNT - FIRST_FRAME_TX)	//  9; Start value for USI Counter for TX first
#define USI_COUNTER_SEED_TX_SECOND	(USI_COUNTER_MAX_COUNT - SECOND_FRAME_TX)	// 12; Start value for USI Counter for TX second
#define USI_COUNTER_SEED_RX_TO_TX	(USI_COUNTER_MAX_COUNT - 2)					// 14; Start value for USI Counter between RX until TX again

// Check, if Buffer size is a power of 2
#define UART_RX_BUFFER_MASK			(UART_RX_BUFFER_SIZE - 1)
#if (UART_RX_BUFFER_SIZE & UART_RX_BUFFER_MASK)
    #error "RX buffer size is not a power of 2"
#endif

#define UART_TX_BUFFER_MASK			(UART_TX_BUFFER_SIZE - 1)
#if (UART_TX_BUFFER_SIZE & UART_TX_BUFFER_MASK)
    #error "TX buffer size is not a power of 2"
#endif				

// Define of USI_UART_state.RX_Buffer_Overflow and USI_UART_state.TX_aborted
#define FALSE						0
#define TRUE						1


//********** USI UART Typedefs **********//

// USI UART RX and TX states
typedef enum {
	WAIT_ON_RX_OR_TX = 0,			// Wait for reception or transmission. Line is free.
	RX_GET_STARTBIT	= 1,			// Reception has started after pin change, but is waiting for
									// synchronization until first timer overflow.
	RX_FIRST = 2,					// Reception of first part is ongoing.
	RX_SECOND = 3,					// Reception of second part is ongoing. Wait for RX-Stop-Bit.
	AFTER_RX_TO_START_TX = 4,		// Wait after Reception for start of Transmission again, if TX was aborted.
	TX_FIRST = 5,					// Transmit of first part.
	TX_SECOND = 6					// Transmit of second part.
} RX_TX_state_t;

// State Byte
typedef struct			
{
	RX_TX_state_t RX_TX_state:	3;
	uint8_t TX_aborted:			1;	// uint8_t better than bool for byte field
	uint8_t RX_Buffer_Overflow:	1;	// uint8_t better than bool for byte field
} USI_UART_state_t;

// UART TX Ring buffer.
typedef struct
{
	uint8_t	Tx1;
	uint8_t	Tx2;
} UART_TXBuf_t;

// UART RX Ring buffer.
typedef struct
{
	uint8_t	Rx1;
	uint8_t	Rx2;
} UART_RXBuf_t;


//********** Static Variables **********//

static volatile USI_UART_state_t USI_UART_state = {0};					// State Byte
	
static volatile UART_TXBuf_t UART_TXBuf[UART_TX_BUFFER_SIZE] = {0};		// TX ring buffer. Size is to define in the header file.
static volatile uint8_t	UART_TxHead;									// Head of TX-Ring-Buffer
static volatile uint8_t	UART_TxTail;									// Tail of TX-Ring-Buffer
static volatile uint8_t UART_TxBuf_Count;								// Counter value for stored data in TX-Ring-Buffer

static volatile UART_RXBuf_t UART_RXBuf[UART_RX_BUFFER_SIZE] = {0};		// RX ring buffer. Size is to define in the header file.
static volatile uint8_t	UART_RxHead;									// Head of RX-Ring-Buffer
static volatile uint8_t	UART_RxTail;									// Tail of RX-Ring-Buffer
static volatile uint8_t UART_RxBuf_Count;								// Counter value for stored data in RX-Ring-Buffer


// ********** Intern Functions ********** //

/**
 * Reverses the order of bits in a byte.
 * I.e. MSB is swapped with LSB, etc. 
 * 
 * @param x original byte
 * @return x reversed byte
 */
uint8_t Bit_Reverse(uint8_t x)
{
	x = ((x >> 1) & 0x55) | ((x << 1) & 0xaa);
	x = ((x >> 2) & 0x33) | ((x << 2) & 0xcc);
	x = ((x >> 4) & 0x0f) | ((x << 4) & 0xf0);
	return x;
}

//********** USI_UART functions **********//

/**
 * Flush the USI UART buffers.
 * 
 * @param void
 * @return void
 */
void USI_UART_Flush_Buffers(void)
{
	UART_RxTail = 0;
	UART_RxHead = 0;
	UART_RxBuf_Count = 0;
	UART_TxTail = 0;
	UART_TxHead = 0;
	UART_TxBuf_Count = 0;
}

/**
 * Initialize USI for UART reception.
 * Note that this function only enables pin change interrupt on the USI Data Input pin.
 * The USI is configured to read data within the pin change interrupt.
 * 
 * @param void
 * @return void
 */
void USI_UART_Initialise_Receiver(void)
{
	while (USI_UART_state.RX_TX_state != WAIT_ON_RX_OR_TX);				// Wait until TX has finished, if TX was started before
	
	cli();																// Interrupts disabled
	
	PORTB |=  (1<<PB1)|(1<<PB0);										// Enable pull up on USI DO and DI pin.
	DDRB  &= ~(1<<PB1)|(1<<PB0);										// Set USI DO and DI pin as input; DO to not disturb RX
	
	USICR = 0;															// Disable USI.

	GIFR =	(1<<PCIF);													// Clear pin change interrupt flag.
	GIMSK |= (1<<PCIE);													// Enable pin change interrupt.
	PCMSK |= (1<<PCINT0);												// Enable pin change on pin PB0
	
	USI_UART_state.RX_TX_state = WAIT_ON_RX_OR_TX;						// Set Status to Wait on RX or TX. Line is free.
	USI_UART_state.TX_aborted = FALSE;									// Set state to TX is not aborted
	USI_UART_state.RX_Buffer_Overflow = FALSE;							// Reset state RX Buffer Overflow
	
	sei();																// Enable global interrupts.
}

/**
 * Check if there is data in the receive buffer.
 * 
 * @param void
 * @return TRUE if data is in the buffer or FALSE if not
 */
uint8_t USI_UART_Data_In_Receive_Buffer(void)
{
	return (UART_RxBuf_Count > 0);										// Return 0 (FALSE) if the receive buffer is empty.
}

/**
 * Get one received byte from the buffer with reversed bits.
 * Wait if buffer is empty.
 * 
 * @param void
 * @return temp_rx_byte as the received byte.
 */
uint8_t USI_UART_Receive_Byte(void)
{
	uint8_t temp_rx_byte;
	
	while (UART_RxBuf_Count == 0);										// Wait for incoming data.
	
	temp_rx_byte = 	(UART_RXBuf[UART_RxTail].Rx1 << 2) | 				// Combine the incoming parts of data.
					((0x0F & UART_RXBuf[UART_RxTail].Rx2) >> 1);
													 
    temp_rx_byte = Bit_Reverse(temp_rx_byte);							// Reverse the order of the bits in the data byte.
	
	UART_RxTail = (UART_RxTail + 1) & UART_RX_BUFFER_MASK;				// Store new index.
	UART_RxBuf_Count--;													// Decrement the stored data.
	
	USI_UART_state.RX_Buffer_Overflow = FALSE;							// Reset the Buffer Overflow flag, if it is set.
	return temp_rx_byte;												// Returns data from the buffer.
}

/**
 * Puts data in the transmission buffer, after reversing the bits in the byte.
 * Initiates the transmission routines if not already started.
 * 
 * @param data as the data which has to be transmitted
 * @return void
 */
void USI_UART_Transmit_Byte(uint8_t data)          
{	
	data = Bit_Reverse(data);											// Reverse the order of the bits.
		
	while (UART_TxBuf_Count == UART_TX_BUFFER_SIZE);					// Wait for free space in buffer.
		
	UART_TXBuf[UART_TxHead].Tx1 = 0x80 | (data >> 2);					// Load (initial high state,) start-bit and 5 LSB of original data (5 MSB of bit of bit reversed data)
	UART_TXBuf[UART_TxHead].Tx2 = (data << 5) | 0x1F;					// Load and shift data for second TX from Buffer and fill with Stop bits
			
	UART_TxHead = (UART_TxHead + 1) & UART_TX_BUFFER_MASK;				// Calculate and Store new index.
	UART_TxBuf_Count++;													// Increment the number of stored Bytes	

	// Start first transmission if line is free
	if	(USI_UART_state.RX_TX_state == WAIT_ON_RX_OR_TX)
	{
		cli();															// Interrupts disabled
		
		// Start Timer0
		TCCR0A = (1<<WGM01);											// Choose Timer0 in CTC mode
		TCCR0B = CLOCKSELECT;											// Start Counter and set prescaler to clk or clk /8; here: Baudrate:9600: 8
		TCNT0 = 0;														// Count up from 0
		OCR0A = OCR0A_FULL;												// Set Output Compare Match Value for full Bit width, here: Baud rate:9600: 51
		
		// Enable USI
		USICR = (0<<USISIE)|(1<<USIOIE)|								// Enable USI Counter OVF interrupt.
				(0<<USIWM1)|(1<<USIWM0)|								// Select Three Wire mode.
				(0<<USICS1)|(1<<USICS0)|(0<<USICLK)|					// Select Timer0 Compare Match as USI Clock source.
				(0<<USITC);
		USIDR = UART_TXBuf[UART_TxTail].Tx1;							// Copy (initial high state,) start-bit and 5 LSB of original data (5 MSB
																		// of bit of bit reversed data)										
		USISR = (1<<USISIF)|(1<<USIOIF)|(1<<USIPF)|						// Clear all USI interrupt flags.
				(USI_COUNTER_SEED_TX_FIRST);							// Preload the USI counter to generate interrupt.
				
		DDRB |= (1<<PB1);												// Configure USI_DO as output
		
		USI_UART_state.RX_TX_state = TX_FIRST;							// Set state to TX First
		sei();															// Interrupts enabled
	}
}

// ********** Interrupt Handlers ********** //

/**
 * The pin change interrupt is used to detect USI_UART reception.
 * The USI is here configured to sample the UART signal.
 */                                  
ISR(PCINT0_vect)                              
{                                                                   
    if (!(PINB & (1<<PB0)))												// Trigger only if DI is Low, which generates the Pin Change Interrupt
    {			
		// Check, if TX was running
		if	(USI_UART_state.RX_TX_state == AFTER_RX_TO_START_TX ||		// If Status Wait after Reception for start of Transmission again
			(USI_UART_state.RX_TX_state == TX_FIRST &&					// If TX has started but has send only the High-Bit
			((USISR & 0x0F) == USI_COUNTER_SEED_TX_FIRST)))				
		{
			DDRB  &= ~(1<<PB1);											// Set USI DO pin as input, to not disturb Rx
		} 
		else if (USI_UART_state.RX_TX_state == TX_SECOND &&				// If TX has sent the last Bit but USI Counter has not reached the overflow
				((USISR & 0x0F) == 15))									// TX will be seen as finished and the index of stored data will be increased
		{																
			UART_TxTail = (UART_TxTail + 1) & UART_TX_BUFFER_MASK;		// Store new index of Tail for next transmission
			UART_TxBuf_Count--;											// Decrement the stored data

			DDRB  &= ~(1<<PB1);											// Set USI DO pin as input, to not disturb Rx
		}
		else if (USI_UART_state.RX_TX_state == TX_FIRST ||				// If TX was running somewhere
				(USI_UART_state.RX_TX_state == TX_SECOND))
		{
			USIDR &= ~0xFE;												// Set Output to Low for DO Low, except the DI-Bit
			USI_UART_state.TX_aborted = TRUE;							// Set TX aborted state to first Byte was aborted
		}		

		//Start Reception																	
		if ((TCCR0B & ((1<<CS02)|(1<<CS01)|(1<<CS00))) == 0)			// If Timer0 is not already running
		{
			TCCR0A = (1<<WGM01);										// CTC mode
			TCCR0B = CLOCKSELECT;										// Start Counter and set prescaler to clk or clk /8; here: Baudrate: 9600: 8
		}

		TCNT0 = 0;														// Count up from 0
		OCR0A = OCR0A_FIRST;											// Set Output Compare Match Value minus Interrupt-Delay for sampling the middle of the Start Bit 
																		// here: Baud rate: 9600: 51 - 12 = 39											
		
		TIFR |= (1<<OCF0A);												// Clear output compare interrupt flag
		TIMSK |= (1<<OCIE0A);											// Enable output compare interrupt
		
		GIMSK &= ~(1<<PCIE);											// Disable pin change interrupt.

		USI_UART_state.RX_TX_state = RX_GET_STARTBIT;					// Set state to Reception Wait until Timer Overflow
    }	
}

/**
 * Timer0 Compare Match A interrupt is used to trigger the sampling of signals
 * on the USI ports, if reception is ongoing.
 */         
ISR(TIMER0_COMPA_vect)
{	
	TCNT0 = 0;															// Count up from 0
	OCR0A = OCR0A_FULL;													// Shift every bit width, here 103 Timer Cycles

	if (USI_UART_state.TX_aborted)
	{
		USIDR &= ~0xFE;													// Set Output to Low for DO Low, except the DI-Bit
	}
	else
	{
		USICR = (0<<USISIE)|(1<<USIOIE)|								// Enable USI Counter OVF interrupt.
				(0<<USIWM1)|(1<<USIWM0)|								// Select Three Wire mode.
				(0<<USICS1)|(1<<USICS0)|(0<<USICLK)|					// Select Timer0 Compare Match as USI Clock source.
				(0<<USITC);
	}
		
	USISR = (1<<USISIF)|(1<<USIOIF)|(1<<USIPF)|							// Clear all USI interrupt flags.
			USI_COUNTER_SEED_RX_FIRST;									// Preload the USI counter to generate interrupt after the reception of the data bits
		
	TIMSK &= ~(1<<OCIE0A);												// Disable COMPA interrupt
		
	USI_UART_state.RX_TX_state = RX_FIRST;								// Set state to Reception is ongoing
}

/**
 * The USI Counter Overflow interrupt is used for moving data between memory and the USI data register.
 * The interrupt is used for both transmission and reception.
 */ 
ISR(USI_OVF_vect)
{	
	USISR = (1<<USISIF)|(1<<USIOIF)|(1<<USIPF);							// Clear all USI interrupt flags.

	switch (USI_UART_state.RX_TX_state)
	{
		case WAIT_ON_RX_OR_TX:											// Not possible in ISR
		{
			break;
		}
		
		case RX_GET_STARTBIT:											// Not possible in ISR
		{
			break;
		}
		
		case RX_FIRST:													// After state Reception ongoing
		{			
			USI_UART_state.RX_TX_state = RX_SECOND;						// Set state to Waiting on Rx-Stop bit
			
			if (UART_RxBuf_Count < UART_RX_BUFFER_SIZE)					// If there is space in the buffer then store the data.
			{
				UART_RXBuf[UART_RxHead].Rx1 = USIBR;					// Store first 7 Bits of received data in buffer.
				USISR |= USI_COUNTER_SEED_RX_SECOND;					// Preload the USI counter to get the last bits until next interrupt.
			}
			else														// If buffer is full trash data and set buffer full flag.
			{
				USI_UART_state.RX_Buffer_Overflow = TRUE;				// Store state to take actions elsewhere in the application code
				PORTB ^= (1 << PB2);									// LED toggeln
			}
			
			if (USI_UART_state.TX_aborted)								// Check if Tx was aborted somewhere at first byte.
			{
				USIDR &= ~0xFE;											// Set Output to Low for DO Low, except the DI-Bit.
			}
			
			break;
		}
		
		case RX_SECOND:													// After state Waiting for RX-Stop bit
		{
			if ((USIBR & 0x01) && !USI_UART_state.RX_Buffer_Overflow)	// Check for Stop bit. If Stop bit was send successful, increment UART_RXHead and the Buffer counter 
																		// else store the next incoming data at the same place to overwrite the corrupted byte.
			{
				UART_RXBuf[UART_RxHead].Rx2 = USIBR;					// Store last Bit of received data in buffer.
				UART_RxHead = (UART_RxHead + 1) & UART_RX_BUFFER_MASK;	// Calculate and Store new index.
				UART_RxBuf_Count++;										// Increment the number of stored Bytes	
			}
			
			if (USI_UART_state.TX_aborted)								// Check if Tx was aborted somewhere at first byte.
			{
				USI_UART_state.RX_TX_state = AFTER_RX_TO_START_TX;		// Set state Status wait after RX on TX
									
				USISR |= USI_COUNTER_SEED_RX_TO_TX;						// Preload the USI counter to generate interrupt. (14)
				USIDR |= 0x7F;											// Set USIDR Output 1 Bit Low and 1 Bit High
				
				USI_UART_state.TX_aborted = FALSE;
			}
			else														// TX_aborted==FALSE 
			{				
				if (UART_TxBuf_Count > 0)								// Check for data in Tx Buffer.
				{
					USI_UART_state.RX_TX_state = TX_FIRST;				// Set state to TX First again.
										
					USIDR = UART_TXBuf[UART_TxTail].Tx1;				// Copy (initial high state,) start-bit and 5 LSB of original data (5 MSB) of aborted Tail
					USISR |= USI_COUNTER_SEED_TX_FIRST;					// Preload the USI counter to generate interrupt.
					
					DDRB |= (1<<PB1);									// Configure USI_DO as output
				}
				else													// Else initialize for Rx again.
				{
					USI_UART_state.RX_TX_state = WAIT_ON_RX_OR_TX;		// Set Status to Wait on RX or TX. Line is free.

					TCCR0B = (0<<CS02)|(0<<CS01)|(0<<CS00);				// Stop Timer0.
					USICR = 0;											// Disable USI.
					PORTB |= (1<<PB1);									// Enable pull up on USI DO pin.
					DDRB  &= ~(1<<PB1);									// Set USI DO pin as input, to not disturb Rx
				}
			}
																		// Initialize for Receive again.
			GIFR =	(1<<PCIF);											// Clear pin change interrupt flag.
			GIMSK |= (1<<PCIE);											// Enable pin change interrupt.
			PCMSK |= (1<<PCINT0);										// Enable pin change on pin PB0.				
			
			break;	
		}
		
		case AFTER_RX_TO_START_TX:										// After Status wait after RX to start TX
		{	
			USI_UART_state.RX_TX_state = TX_FIRST;			 			// Set state to TX First again
			
			USIDR = UART_TXBuf[UART_TxTail].Tx1;						// Copy (initial high state,) start-bit and 5 LSB of original data (5 MSB)
			USISR |= (USI_COUNTER_SEED_TX_FIRST);						// Preload the USI counter to generate interrupt.
			
			break;
		}
	
		case TX_FIRST:													// After state TX First
		{
			USI_UART_state.RX_TX_state = TX_SECOND;						// Set state to TX Second
														
			USIDR =  UART_TXBuf[UART_TxTail].Tx2;						// Reload the USIDR with the rest of the data and stop-bits.
			USISR |= (USI_COUNTER_SEED_TX_SECOND);						// Preload the USI counter with second seed to generate interrupt.
			
			break;
		}
	
		case TX_SECOND:													// After state TX Second
		{	
			UART_TxTail = (UART_TxTail + 1) & UART_TX_BUFFER_MASK;		// Store new index of Tail for next transmission
			UART_TxBuf_Count--;											// Decrement the stored data
								
			
			if (UART_TxBuf_Count > 0)									// Check for further data in Buffer
			{
				USI_UART_state.RX_TX_state = TX_FIRST;					// Set state to TX First again
				
				USIDR = UART_TXBuf[UART_TxTail].Tx1;					// Copy (initial high state,) start-bit and 5 LSB of original data (5 MSB
				USISR |= (USI_COUNTER_SEED_TX_FIRST);					// Preload the USI counter to generate interrupt.
			}
			else														// Else leave transmit mode.
			{
				USI_UART_state.RX_TX_state = WAIT_ON_RX_OR_TX;			// Set Status to Wait on RX or TX. Line is free.

				TCCR0B  = (0<<CS02)|(0<<CS01)|(0<<CS00);				// Stop Timer0.
				PORTB |=  (1<<PB1);										// Enable pull up on USI DO pin.
				DDRB  &= ~(1<<PB1);										// Set USI DO pin as input, to not disturb RX
				USICR = 0;												// Disable USI.
			}
			
			break;
		}
		
		default:
		{
			break;
		}
	}
}