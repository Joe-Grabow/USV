/*
 * InitOSCCAL.c
 *
 * Created: 09.07.2025 18:34:03
 *  Author: s2chhaen
 */ 

#include <avr/eeprom.h>
#include <stdbool.h>

uint16_t cpuID = 0x0000;
bool setOSCCAL = false;

void OSCCALInit(void) __attribute__((constructor));
void flashNewOSCCALtoEEPROM(uint8_t tOSCCAL);

void OSCCALInit(void)
{
	uint8_t tOSCCAL;
	uint8_t tmp;
	uint8_t CHSr;
	
	uint8_t CHSc = 0;
	
	tmp = eeprom_read_byte((const uint8_t*)0x00);
	CHSc += tmp;
	cpuID |= (uint16_t)tmp;
	tmp = eeprom_read_byte((const uint8_t*)0x01);
	CHSc += tmp;
	cpuID |=  ((uint16_t)tmp)<<8;
	tOSCCAL = eeprom_read_byte((const uint8_t*)0x02);
	CHSc += tOSCCAL;
	CHSc = (~CHSc) +1;
	CHSr = eeprom_read_byte((const uint8_t*)0x03);
	if(CHSc==CHSr)
	{
		OSCCAL = tOSCCAL;
		setOSCCAL = true;
	}
}

void flashNewOSCCALtoEEPROM(uint8_t tOSCCAL)
{
	uint8_t tmp;
	
	uint8_t CHSc = 0;
	
	tmp = eeprom_read_byte((const uint8_t*)0x00);
	CHSc += tmp;
	tmp = eeprom_read_byte((const uint8_t*)0x01);
	CHSc += tmp;
	CHSc += tOSCCAL;
	CHSc = (~CHSc) +1;
	eeprom_busy_wait();
	eeprom_write_byte((uint8_t*)0x02,tOSCCAL);
	eeprom_busy_wait();
	eeprom_write_byte((uint8_t*)0x03,CHSc);
}
