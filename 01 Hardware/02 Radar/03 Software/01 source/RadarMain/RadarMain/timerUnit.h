/*
 * timerUnit.h
 * Description: Header-Datei f�r Timer-Einheit
 * Created: 6/29/2023 1:41:01 PM
 * Author: Thach
 * Version: 1.1
 * Revision: 1.2
 */ 


#ifndef TIMERUNIT_H_
#define TIMERUNIT_H_

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include "./ATMegaXX09/ATMegaXX09Clock.h"
#include "ATMegaXX09/USART/USART.h"
#include "Math/MinMax.h"
#include "errorList.h"

/*Abk�rzungen: Res/REZ = resolution
*/

#define CONVERT_FACTOR_S_2_MS 1000UL
#define CONVERT_FACTOR_S_2_US 1000000UL
#define TIMER_MAX_REZ_MS 3276
#define TIMER_MAX_REZ_S 3
#define TIMER_MIN_REZ_US 1000UL

enum timerResolution{
	REZ_US,
	REZ_MS,
	REZ_S
};

typedef struct{
	uint8_t init:1;
}timerStatus_t;

extern uint8_t timer_init(uint8_t rezConfig, uint16_t resUSV, uint16_t resRadar);
//Funktion zum Steuern des Timers f�r USVData
extern void usvTimer_setState(uint8_t state);
extern void usvTimer_setCounter(uint32_t value);
extern const int16_t usvTimer_getCounter();
//Funktion zum Steuern des Timers f�r Radar
extern void radarTimer_setState(uint8_t state);
extern void radarTimer_setCounter(uint32_t value);
extern const int16_t radarTimer_getCounter();

#endif /* TIMERUNIT_H_ */