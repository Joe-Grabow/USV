/*
 * main.c
 *
 * Created: 1/8/2025 1:54:32 PM
 *  Author: s2chhaen
 */ 

#include <xc.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <stdbool.h>

#include "USI_UART_config.h"

/************************************************************************/
/* Defines                                                              */
/************************************************************************/
// Define for PWM
#define PWM_STOP 90					// middle of [69, 111]: duty cycle of 35% (=1,765V). Motor is not running.

// Define for 100 ms for Timer 1
#define OVF_MATCHES_100MS 11100UL	// Tried value with stop watch. Calculated for 100ms was: 25000 (= TARGET_TIME_MS * 0.001 * F_PLL / (OCR1C_VAL+1))

// Defines for counters that can be increment after 100 ms
#define MAX_FAILED_NEW_DATA 10		// Max. for failed incoming data to go in safe stat
#define MAX_MOTOR_FAILURE 5			// Max. for motor failure to send the state motor_not_ok
#define MAX_MOTOR_OK_AFTER_FAIL 3	// Max. for get OK after failure to recovery the motor state.

#define LED_TOGGLE_UART_LOST 10		// Max. for LED toggle.

// Define for motor state
typedef enum {
	MOTOR_OK = 0xAA,				// Motor OK.
	MOTOR_NOT_OK = 0xBB,			// Motor sent no start signal.
	MOTOR_NOT_MORE_OK = 0xCC		// Motor failure on running.
} motor_state_t;

// Define for UART state
typedef enum {
	UART_WAIT_FOR_SYNC = 0,			// Wait for start byte. (especially for BT-Module, that no invalid data can be set at start to the motor)
	UART_CONNECTED = 1,				// UART connected. Data can be received.
	UART_CONNECTION_LOST = 2		// Lost UART connection after timeout.
} uart_state_t;

/************************************************************************/
/* Global variables                                                     */
/************************************************************************/
// Motor variables
static motor_state_t motor_state = MOTOR_NOT_OK;		// Motor has sent no start signal
static uint8_t cnt_motor_failure = 0;					// Counter for failure from motor
static uint8_t cnt_motor_ok_after_fail = 0;				// Counter for recovery from failure of motor
	
// UART variables
static uart_state_t uart_state = UART_WAIT_FOR_SYNC;	// UART-state on start
static bool valid_data_received = false;				// Flag, if valid data was received
static uint8_t cnt_failed_new_data = 0;					// Counter for failed incoming data
	
// LED variable
uint8_t cnt_led_toggle = 0;								// Counter for LED_toggle.

/************************************************************************/
/* Extern                                                               */
/************************************************************************/
// Function for writing OSCCAL to EEPROM
extern void flashNewOSCCALtoEEPROM(uint8_t tOSCCAL);

/************************************************************************/
/* Intern Functions                                                     */
/************************************************************************/
/**
 * Initialization of Timer/Counter1 for PWM Mode to generate the resulting voltage for the motor control. 
 * At the beginning the motor have to be in the stop position for which a voltage between 1,35 and 2,18 (PWM value from 69 until 111) is needed.
 * The middle of this range is 1,765V. (=PWM value: 90).
 * The Timer/Counter1 is used in asynchronous mode, which uses the fast peripheral clock (PCK) with a frequency of 64 MHz as the clock time base.
 * The frequency of the PWM results in a value of 250 kHz with a prescaler of N=1, calculated by the following equitation:
 * f_PWM = f_PLL / (N * (OCR1C value + 1)) = 64 MHz / (1 * (255 + 1)) = 250 kHz.
 * The OCR1C value is maximum value for the Timer/Counter1 from up counting from 0. The Timer/Counter will be reset to 0 on compare match.
 * 
 * @param void
 * @return void
 */
void Timer_and_PWM_Init(void)
{	
	PLLCSR |= (1 << PLLE);								// Enable the PLL.
	while(!(PLLCSR & (1 << PLOCK)));					// Wait until PPL is locked in steady state (100 us) is needed before asynchronous mode can be enabled.
	PLLCSR |= (1 << PCKE);								// Enable PLL as Timer/Counter clock source for enabling the asynchronous mode. (f_PLL = 64 MHz).  	
	
	GTCCR |= (1 << PWM1B)|(1 << COM1B1);				// Enable PWM for OCR1B in non-inverting mode.
	
	OCR1C = 255; 										// Set the maximum count value for the PWM. (255 = maximum resolution of 8.0)
	OCR1B = PWM_STOP; 									// Set the duty cycle at the beginning to 35% (=1,765V).
	
	DDRB |= (1 << PB4);									// Set PB4 as output for the PWM.
	
	TCCR1 |= (1 << CS10);								// Start the Timer/Counter1 with prescaler N = 1.
}

/**
 * Check the incoming 3 pulsed signal of the Haswing Protuar motor. 
 * 
 * @param void
 * @return true or false
 */
bool check_OK_on_Start(void)
{	
	DDRB &= ~(1 << PB3);								// Error Beep In
	PORTB |= (1 << PB3);								// Internal Pull-Up
	
	_delay_ms(990);										// Time for middle of first Low-Signal of Motor-OK (=898 + 185/2)
		
	for (uint8_t i=1; i<=6; i++)					
	{	// odd and Pin is not Low or even and Pin is not High
		if (((i%2 == 1) && (PINB & (1 << PB3))) || ((i%2 == 0) && !(PINB & (1 << PB3))))
		{
			return false;
		}
		else if (i != 6)
		{
			_delay_ms(185);								// One Pulse of OK-Signal
		}
	}
	
	return true;
}

/**
 * Check for valid PWM value of Rx function
 * 
 * @param uint8_t value
 * @return bool: true if valid value, else: false
 */
bool check_for_valid_value(uint8_t value)
{
	return ((value >= 24 && value <= 68) || (value == PWM_STOP) || (value >= 112 && value <= 235));
}

/**
 * Timer function for 100 ms
 * 
 * @param Timer_interval in ms
 * @return true if Timer shot or false
 */
bool Timer_shot_100_ms(void)
{
	static uint32_t ovf_cnt = 0;						// Overflow Counter for Timer1
	
	if (TIFR & (1 << TOV1))								// Timer1 Overflow Flag is set?
	{
		TIFR |= (1 << TOV1);							// Reset Timer1 Overflow Flag
			
		ovf_cnt++;										// Count Overflows
			
		if (ovf_cnt >= (OVF_MATCHES_100MS))				// Check if Timer_Overflows reached the overflows for time
		{
			ovf_cnt = 0;								// Reset the overflow counter
			return true;
		}
	}
	
	return false;
}

/**
* Function for check of the UART state
* 
* @param void
* @return void
*/
void check_and_set_UART_state(void)
{
	switch(uart_state)
	{
		case UART_WAIT_FOR_SYNC:						// UART is not connected on start
		{
			break;										// Do nothing
		}
					
		case UART_CONNECTED:							// UART is connected
		{
			if (valid_data_received)					// Valid data received
			{
				cnt_failed_new_data = 0;				// Reset the counter
				valid_data_received = false;			// Reset valid data state.
			}
			else										// No valid data received.
			{
				PORTB &= ~(1 << PB2);					// LED off
				cnt_failed_new_data++;					// Increment the failed data counter.
							
				if (cnt_failed_new_data >= MAX_FAILED_NEW_DATA)	// Timeout for Rx-data!
				{
					OCR1B = PWM_STOP;					// Set stop. Fail safe!
					uart_state = UART_CONNECTION_LOST;	// Set state for lost connection
				}
			}
						
			break;
		}
					
		case UART_CONNECTION_LOST:						// UART lost connection.
		{
			cnt_led_toggle++;							// Increment the LED counter.
						
			if (cnt_led_toggle >= LED_TOGGLE_UART_LOST)
			{
				PORTB ^= (1 << PB2);					// LED toggle slowly.
				cnt_led_toggle = 0;						// Reset the counter for slowly LED toggle.
			}
						
			break;
		}
					
		default:										// Other unexpected states.
		{
			break;
		}
	}
}
	
/**
* Function for check of motor signal, if motor start signal was received.
* 
* @param void
* @return void
*/
void check_motor_and_set_status(void)
{	
	if (!(PINB & (1 << PB3)) && motor_state == MOTOR_OK) // Low for failure if motor was OK. 
	{
		cnt_motor_ok_after_fail = 0;					// Reset the counter for OK.
		cnt_motor_failure++;							// Increment the counter for failure.
				
		if (cnt_motor_failure >= MAX_MOTOR_FAILURE)
		{
			OCR1B = PWM_STOP;							// Set the stop after max. times of Motor failure.
			motor_state = MOTOR_NOT_MORE_OK;			// Set Failure, if MAX_MOTOR_FAILURE is reached.
		}
	}
	else if ((PINB & (1 << PB3)) && motor_state == MOTOR_NOT_MORE_OK) // Again High after Failure.
	{
		cnt_motor_failure = 0;							// Reset the counter for failure.
		cnt_motor_ok_after_fail++;						// Increment the counter for OK.
				
		if (cnt_motor_ok_after_fail >= MAX_MOTOR_OK_AFTER_FAIL)
		{
			motor_state = MOTOR_OK;						// Reset the motor state to OK.
		}
	}
}

/************************************************************************/
/* Main Function                                                        */
/************************************************************************/
/**
 * Main function
 * 
 * @param void
 * @return void
 */
int main(void)
{			
	// example for OSCCAL EEPROM write
	//if (OSCCAL != 0x4E)
	//{
		//flashNewOSCCALtoEEPROM(0x4E);
	//}
	
	asm("nop"); // For debug!
	
	// Start at first the PWM to set the neutral PWM-signal to motor
	Timer_and_PWM_Init();								// Initialization of Timer and PWM.
	
	if (check_OK_on_Start())
	{
		motor_state = MOTOR_OK;
	}


	DDRB |= (1 << PB2);									// LED Output
	PORTB |= (1 << PB2);								// LED on to show that is one and wait for connection.
	
	USI_UART_Flush_Buffers();							// Clear all USI UART Buffers.	
	USI_UART_Initialise_Receiver();						// Initialization for USI_UART Receiver.
	
	asm("nop"); // For debug!
	
	// Main-Loop
    while(1)
    {			
		if (USI_UART_Data_In_Receive_Buffer())			// Check for incoming data.	
		{
			uint8_t Rx_Temp = USI_UART_Receive_Byte();	// Store the data.
			
			if (uart_state == UART_WAIT_FOR_SYNC)		// UART is not ready. Wait on startsignal.
			{
				if (Rx_Temp == PWM_STOP)				// PWM_STOP is also the startsignal from Raspberry Pi Pico
				{
					uart_state = UART_CONNECTED;		// Set UART connected.
					USI_UART_Transmit_Byte(motor_state);// Send the motor_state after first Rx to say "Hello".
				}
			}
			else										// UART is ready
			{
				if (check_for_valid_value(Rx_Temp))		// Check, if data is valid in the range
				{
					OCR1B = Rx_Temp;					// Set the PWM value.
					PORTB ^= (1 << PB2);				// LED toggle
					
					valid_data_received = true;			// Set flag for valid data.
					uart_state = UART_CONNECTED;		// Set UART connected, if connection was lost.
					USI_UART_Transmit_Byte(motor_state);// Send the motor_state after Rx to say "I am connected" (not in cycle to avoid a collision!).
				}
			}														
		}
		
		if (Timer_shot_100_ms())						// Check every 100ms:				
		{
			check_and_set_UART_state();					// 1.) UART state, to shut the motor off, after failure or reset.
			check_motor_and_set_status();				// 2.) motor state
		}
	}
}