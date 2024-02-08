#ifndef FILTER_IIR_H_INCLUDED
#define FILTER_IIR_H_INCLUDED

#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdint.h>
#include <inttypes.h>
#include "filterConfig.h"

#define IIR_FILTER_ORDER 2U
#define IIR_OLD_VALUES_BUFFER_LEN_BITS ((IIR_FILTER_ORDER-1U)/2U + 1U)
#define IIR_OLD_VALUES_BUFFER_LEN (1<<IIR_OLD_VALUES_BUFFER_LEN_BITS)


typedef struct{
    int32_t data[IIR_OLD_VALUES_BUFFER_LEN];
    uint8_t beginIdx :IIR_OLD_VALUES_BUFFER_LEN_BITS;
    uint8_t endIdx   :IIR_OLD_VALUES_BUFFER_LEN_BITS;
}ffOldBufferIIR_t;

typedef struct{
    double data[IIR_OLD_VALUES_BUFFER_LEN];
    uint8_t beginIdx :IIR_OLD_VALUES_BUFFER_LEN_BITS;
    uint8_t endIdx   :IIR_OLD_VALUES_BUFFER_LEN_BITS;
}ffOldBufferIIRFloat_t;

enum iirType{
    IIR_MAXIMALLY_FLAT = 0x00
};

void iir_init(int16_t* inputFFCofs, uint16_t ffLen, int16_t* inputFBCofs, uint16_t fbLen);
void iir_runFiP(int32_t* data, int32_t* output, uint16_t len);
void iir_runFlP(int32_t* data, double* output, uint16_t len);

#endif // FILTER_IIR_H_INCLUDED