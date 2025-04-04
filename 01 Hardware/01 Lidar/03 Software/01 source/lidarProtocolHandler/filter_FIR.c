/**
 * filter_FIR.c
 * Description: Quellcode-Datei f�r filter_FIR.h-Datei
 * Author: Thach
 * Created: 10/08/2023
 * Version: 1.0
 * Revision: 1.0
 */

#include "filter_FIR.h"

static uint8_t init = 0;
static int32_t ffCofs[FIR_FILTER_ORDER+1]={0};
static ffOldBufferFIR_t old = {0};

static double ffCofsFloat[FIR_FILTER_ORDER+1]={0};
static ffOldBufferFIRFloat_t oldFLoat = {0};

static int32_t qFormatARM2TI(int64_t input, uint16_t bits){
    int32_t result = 0;
    static const uint16_t bitLenMax = 20;
    const int32_t cFactorARM = (1<<bits) -1 ;
    if(bits<bitLenMax){
        result = (int32_t)((int64_t)input<<bits)/((int64_t)cFactorARM);
    }
    return result;
}

/** \brief Initialisierung des Moduls
 *
 * \param inputFFCofs int16_t* Zeiger zum Filter-Koeffizienten-Array
 * \param ffLen uint16_t Array-L�nge
 * \return void
 *
 */
void fir_init(int16_t* inputFFCofs, uint16_t ffLen){
    uint8_t checkFf = ffLen==(FIR_FILTER_ORDER+1);

    if(!checkFf){
        printf("Die Ordnung von Filterpolynom nicht gleich der vom Filter");
    } else{
        for(int i = 0; i< ffLen; i++){
            ffCofs[i] = qFormatARM2TI(inputFFCofs[i],FIXED_POINT_BITS);
            ffCofsFloat[i] = inputFFCofs[i]*1.0000/CONVERT_FACTOR_INT;
        }
        init = 1;
        oldFLoat.beginIdx = 0;
        oldFLoat.endIdx = FIR_FILTER_ORDER-1;
    }
}

/** \brief Ausf�hrung der Filterung
 *
 * \param data int32_t* Eingabe-Daten-Array
 * \param output int64_t* Ausgabe-Array
 * \param len uint16_t L�nge des Ausgabe/Eingabe-Arrays (Annahme: beide gleicheinander)
 * \return void
 *
 */
void fir_runFiP(int32_t* data, int64_t* output, uint16_t len){
    uint8_t idxPtr = 0;
    uint8_t phaseShift_sample = 0;
    int64_t tempBuff[OUTPUT_MAX_LEN] = {0};
    int64_t tempOut[OUTPUT_MAX_LEN] = {0};
    int32_t temp = 0;
    const uint8_t bufferLen = FIR_OLD_VALUES_BUFFER_LEN;
    for(int i = 0; i<len; i++)
    {
        tempBuff[i] = (int64_t)data[i];
    }
    phaseShift_sample = FIR_FILTER_ORDER/2 + 1;
    //kann nur Array mit max. (512 - shifted samples) Mitglieder bearbeiten
    len = ((OUTPUT_MAX_LEN-phaseShift_sample)>len)?len:(OUTPUT_MAX_LEN-phaseShift_sample);
    temp = tempBuff[len-1];
    for(int i = 0; i < phaseShift_sample; i++)
    {
        tempBuff[len+i] = temp;
    }
    len += phaseShift_sample;
    for(int i = 0; i < len; i++)
    {
        tempOut[i] = ((int64_t)ffCofs[0])*((int64_t)tempBuff[i])>>FIXED_POINT_BITS;
        old.beginIdx = old.endIdx;
        for(int j = 1; j <= FIR_FILTER_ORDER; j++)
        {
            tempOut[i] += ((int64_t)ffCofs[j])*((int64_t)old.data[old.beginIdx])>>FIXED_POINT_BITS;
            old.beginIdx--;
        }
        //Aktualisieren der alten Werte
        old.endIdx++;
        old.data[old.endIdx] = tempBuff[i];
    }

    for(int i = phaseShift_sample; i<len; i++)
    {
        output[i-phaseShift_sample] = tempOut[i];
    }
}
