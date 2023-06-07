#include <avr/io.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "dataprep.h"

/*bytes_to_values**********************************************************
*Input:
*uint8_t received[] : �bergabe des Arrays, welches die gefilterten Daten enth�lt
*
*Output:
*uint8_t* : gibt Zeiger auf Array zur�ck
*gefilterte Daten bestehen aus 722 Byte in der Form (LSB, MSB) pro Datenpunkt
*Werte werden zu Distanzen verrechnet, resultierendes Array enth�lt 361 Daten (0,5� je Messpunkt, 180� gesamt)
*************************************************************/
uint8_t* bytes_to_values(uint8_t received[]) {
	uint8_t data[361] = NULL;
	int i = 0;
	
	for (i=0; i<=722; i+=2) {
		data[i/2] = received[i] + 256*received[i+1];
	}
	
	return data;
}

/*round_values**********************************************************
*Input:
*uint8_t data[] : �bergabe des Arrays, welches die 361 Messpunkte enth�lt
*
*Output:
*uint8_t* : gibt Zeiger auf Array zur�ck
*gem�� Forderung werden die Messwerte (liegen in cm vor) auf 50cm genau gerundet
*aus Sicherheitsgr�nden: immer abrunden
*************************************************************/
uint8_t* round_values(uint8_t data[]) {
	uint8_t rounded_data[361] = NULL;
	int i = 0;
	
	for (i=0; i<=361; i++) {
		rounded_data[i] = (data[i]/500)*500; /*immer auf 0,5m genau abrunden aus Sicherheitsgr�nden: 3412cm --> 3000cm, 2976cm --> 2500cm, 891cm --> 500cm*/
	}
	
	return rounded_data;
}

/*cm_to_m**********************************************************
*Input:
*uint8_t data[] : �bergabe des Arrays, welches die gerundeten Messwerte (in cm) enth�lt
*
*Output:
*uint8_t* : gibt Zeiger auf Array zur�ck
*Funktion konvertiert die Messwerte (liegen in cm vor) in m
*gem�� Forderung werden die Daten mit 2 multipliziert, um ganzzahlige Werte an Slave senden zu k�nnen
*************************************************************/
uint8_t* cm_to_m (uint8_t data[]) {
	uint8_t converted_data[361] = NULL;
	int i = 0;
	
	for (i=0; i<=361; i++) {
		converted_data[i] = data[i]*2/100;
	}
	
	return converted_data;
}