#include "main.h"

#include <stdint.h>
#include "filter_IIR.h"
#include "filter_FIR.h"
#include "ioModul.h"
#include "filterCoefs/mf_qFormFilterCof.h"
#include "filterCoefs/wk_qFormFilterCof.h"
#include "filterCoefs/lsq_qFormFilterCof.h"
#include "filterCoefs/eq_qFormFilterCof.h"
#include "filterCoefs/wb_qFormFilterCof.h"
#include "filterCoefs/wr_qFormFilterCof.h"

int main()
{
    int32_t temp[BUFFER_MAX_LENGTH]={0};
    int32_t filtered[BUFFER_MAX_LENGTH]={0};
    double dFilterd[BUFFER_MAX_LENGTH]={0};
    uint16_t len = sizeof(temp)/sizeof(int32_t);
    readFile();
    getData(temp,&len);
    iir_init((int16_t*)mf_num,mf_numLen,(int16_t*)mf_den,mf_denLen);

//#define SEG_1_MAIN
#ifdef SEG_1_MAIN
    iir_runFiP(temp,filtered,len);
    writeFile((uint8_t*)"output_mf_fixed_c",sizeof("output_mf_fixed_c"),TEXT_FORM,filtered,len);
    writeFile((uint8_t*)"output_mf_fixed_c",sizeof("output_mf_fixed_c"),CSV_FORM,filtered,len);
#endif // SEG_1_MAIN

//#define SEG_2_MAIN
#ifdef SEG_2_MAIN
    iir_runFlP(temp,dFilterd,len);
#endif // SEG_2_MAIN

//#define SEG_3_MAIN
#ifdef SEG_3_MAIN
    fir_init((int16_t*)wk_num,wk_numLen);
    fir_runFiP(temp,filtered,len);
    writeFile((uint8_t*)"output_wk_fixed_c",sizeof("output_wk_fixed_c"),TEXT_FORM,filtered,len);
    writeFile((uint8_t*)"output_wk_fixed_c",sizeof("output_wk_fixed_c"),CSV_FORM,filtered,len);
#endif // SEG_3_MAIN

//#define SEG_4_MAIN
#ifdef SEG_4_MAIN
    fir_init((int16_t*)lsq_num,lsq_numLen);
    fir_runFiP(temp,filtered,len);
    writeFile((uint8_t*)"output_lsq_fixed_c",sizeof("output_lsq_fixed_c"),TEXT_FORM,filtered,len);
    writeFile((uint8_t*)"output_lsq_fixed_c",sizeof("output_lsq_fixed_c"),CSV_FORM,filtered,len);
#endif // SEG_4_MAIN

//#define SEG_5_MAIN
#ifdef SEG_5_MAIN
    fir_init((int16_t*)eq_num,eq_numLen);
    fir_runFiP(temp,filtered,len);
    writeFile((uint8_t*)"output_eq_fixed_c",sizeof("output_eq_fixed_c"),TEXT_FORM,filtered,len);
    writeFile((uint8_t*)"output_eq_fixed_c",sizeof("output_eq_fixed_c"),CSV_FORM,filtered,len);
#endif // SEG_5_MAIN

//#define SEG_6_MAIN
#ifdef SEG_6_MAIN
    fir_init((int16_t*)wb_num,wb_numLen);
    fir_runFiP(temp,filtered,len);
    writeFile((uint8_t*)"output_wb_fixed_c",sizeof("output_wb_fixed_c"),TEXT_FORM,filtered,len);
    writeFile((uint8_t*)"output_wb_fixed_c",sizeof("output_wb_fixed_c"),CSV_FORM,filtered,len);
#endif // SEG_6_MAIN

#define SEG_7_MAIN
#ifdef SEG_7_MAIN
    fir_init((int16_t*)wr_num,wr_numLen);
    fir_runFiP(temp,filtered,len);
    writeFile((uint8_t*)"output_wr_fixed_c",sizeof("output_wr_fixed_c"),TEXT_FORM,filtered,len);
    writeFile((uint8_t*)"output_wr_fixed_c",sizeof("output_wr_fixed_c"),CSV_FORM,filtered,len);
#endif // SEG_7_MAIN
    return 0;
}