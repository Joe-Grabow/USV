/*
 * lidarHandler.c
 *
 * Created: 11/26/2023 4:06:34 PM
 * Author: Thach
 * Version: 1.0
 * Revision: 1.0
 */ 

#include "lidarHandler.h"

/*Konstante Variable von USART-FIFO*/
static const uint16_t usartFIFOMaxLen = _FIFO_max_def - 2;
/*Lokalvariable f�r Lidar*/
static uint8_t lidar_addr = LIDAR_PROTOCOL_DEFAULT_ADDR;
volatile uint16_t lidar_tempChecksumVal = 0;
//Lokalvariable f�r Protokoll
volatile uint8_t lidar_protocol[LIDAR_REQ_PROTOCOL_MAX_LEN] = {0};
volatile uint8_t lidar_protocolToHandleBytes = 0;
volatile uint8_t lidar_protocolIdx = 0; //Idx: Index
//Lokalvariable f�r RX-Buffer (Ausgabe)
volatile uint8_t* lidar_rxBuffer;
volatile uint16_t* lidar_rxBufferStrLen;
volatile uint16_t lidar_rxBufferToHandleBytes = 0;
volatile uint16_t lidar_rxBufferIdx = 0;
volatile uint8_t lidar_expectedRxBytes = 0;
//Lokalvariable f�r TX-Buffer
static uint8_t lidar_txDataBuffer[10];
//Lokalvariable zur Modul-Verwaltung
volatile lidarMgr_t lidar_mgr = {0};
volatile lidarStatus_t  lidar_status = {0};
volatile usartConfig_t lidar_comParam = {0};
static int8_t lidar_tryTime = 1; 
volatile uint16_t lidar_checksumPolynom = 0;

volatile reg8Model_t* lidar_ioStream = NULL;
volatile uint8_t lidar_programPos = COM_PROGRAMM_NORMAL_POS; 

/* temp-Var zum Speichern des Params von der R�ckruffunktion */
//f�r usart TX - callback Funktion angewendet
volatile uint8_t* lidar_txTempData[1] = {0};
volatile uint8_t* lidar_txTempLength;
volatile uint8_t lidar_txTempMax_length;
//f�r usart RX - callback Funktion angewendet
volatile uint8_t* lidar_rxTempData;
volatile uint8_t lidar_rxTempLength;
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//Interne FSM-Deklaration
volatile uint8_t lidar_mode = LIDAR_PARAM_MODE;
volatile uint8_t lidar_fsmState[LIDAR_MODE_NUM] = {
	LIDAR_PARAM_FSM_END_STATE,
	LIDAR_RESET_FSM_END_STATE,
	LIDAR_GETTER_FSM_END_STATE
};
volatile uint8_t tempState = 0;
//FSM - Parametrierung
static uint8_t lidar_paramStartSHandlerFunc();
static uint8_t lidar_paramFPHandleSHandlerFunc();
static uint8_t lidar_paramRX1stCheckSHandlerFunc();
static uint8_t lidar_paramRXSHandlerFunc();
static uint8_t lidar_paramRX2ndCheckSHandlerFunc();
static uint8_t lidar_paramEndSHandlerFunc();

lidar_fsmStateHandlerFunc_t lidar_paramtCbTable[LIDAR_PARAM_FSM_STATE_NUM] = {
	&lidar_paramStartSHandlerFunc,
	&lidar_paramFPHandleSHandlerFunc,
	&lidar_paramRX1stCheckSHandlerFunc,
	&lidar_paramRXSHandlerFunc,
	&lidar_paramRX2ndCheckSHandlerFunc,
	&lidar_paramEndSHandlerFunc
};
	
//FSM-Getter
static uint8_t lidar_getterStartSHandlerFunc();
static uint8_t lidar_getterTXSHandlerFunc();
static uint8_t lidar_getterRX1stCheckSHandlerFunc();
static uint8_t lidar_getterRX2ndCheckSHandlerFunc();
static uint8_t lidar_getterRXDataSHandlerFunc();
static uint8_t lidar_getterRX3rdSHandlerFunc();
static uint8_t lidar_getterEndSHandlerFunc();

lidar_fsmStateHandlerFunc_t lidar_getterCbTable[LIDAR_GETTER_FSM_STATE_NUM] = {
	&lidar_getterStartSHandlerFunc,
	&lidar_getterTXSHandlerFunc,
	&lidar_getterRX1stCheckSHandlerFunc,
	&lidar_getterRX2ndCheckSHandlerFunc,
	&lidar_getterRXDataSHandlerFunc,
	&lidar_getterRX3rdSHandlerFunc,
	&lidar_getterEndSHandlerFunc
};

//FSM-Reset
static uint8_t lidar_resetStartSHandlerFunc();
static uint8_t lidar_resetRxSHandlerFunc();
static uint8_t lidar_resetTerminalSHandlerFunc();
static uint8_t lidar_resetEndSHandlerFunc();
lidar_fsmStateHandlerFunc_t lidar_resetCbTable[LIDAR_RESET_FSM_STATE_NUM] = {
	&lidar_resetStartSHandlerFunc,
	&lidar_resetRxSHandlerFunc,
	&lidar_resetTerminalSHandlerFunc,
	&lidar_resetEndSHandlerFunc
};

//Gesamte Look-up-Tabelle f�r Zustand-Handler-Routinen vom allen FSM
lidar_fsmStateHandlerFunc_t* lidar_allFsmLookuptable[LIDAR_MODE_NUM] = {
	(lidar_fsmStateHandlerFunc_t*)&lidar_paramtCbTable,
	(lidar_fsmStateHandlerFunc_t*)&lidar_resetCbTable,
	(lidar_fsmStateHandlerFunc_t*)&lidar_getterCbTable
};
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//externe FSM- Deklaration
static uint8_t lidar_mainSyncSHandler();
static uint8_t lidar_mainSyncPollingSHandler();
static uint8_t lidar_mainSyncSignalCheckSHandler();
static uint8_t lidar_mainDataReqSHandler();
static uint8_t lidar_mainRspPollingSHandler();
static uint8_t lidar_mainDataCheckSHandler();
static uint8_t lidar_mainResetSHandler();
static uint8_t lidar_mainResetPollingSHandler();
static uint8_t lidar_mainErrorSHandler();

lidar_mainFsmSHandlerFunc_t lidar_mainFsmLookupTable[LIDAR_MAIN_FSM_STATE_NUM] = {
	&lidar_mainSyncSHandler,
	&lidar_mainSyncPollingSHandler,
	&lidar_mainSyncSignalCheckSHandler,
	&lidar_mainDataReqSHandler,
	&lidar_mainRspPollingSHandler,
	&lidar_mainDataCheckSHandler,
	&lidar_mainResetSHandler,
	&lidar_mainResetPollingSHandler,
	&lidar_mainErrorSHandler
};
/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//interne verwendete Funktionen

uint16_t lidar_checksum16(uint8_t* input, uint16_t length){
	/* siehe "Telegramme zur Konfiguration und Bedienung der Lasermesssysteme LMS2xx-V2.30"
	 * f�r weitere Informationen*/
	uint16_t uCrc16=0;
	uint8_t temp[]={0,0};
	for (uint32_t i=0;i<length;i++){
		temp[1]=temp[0];
		temp[0]=input[i];
		if (uCrc16&0x8000){
			uCrc16 = (uCrc16&0x7fff)<<1;
			uCrc16 ^= lidar_checksumPolynom;
		} else {
			uCrc16<<=1;
		}
		uCrc16 ^= (temp[0]|(temp[1]<<8));
	}
	return uCrc16;
}

static inline uint8_t lidar_rspVal(uint8_t cmdOAddr){
	return (cmdOAddr+0x80);
}

static inline void lidar_rxRountine(){
	if (lidar_rxBufferToHandleBytes <= usartFIFOMaxLen){
		lidar_expectedRxBytes = lidar_rxBufferToHandleBytes;
		USART_set_Bytes_to_receive(lidar_comParam.usartNo, lidar_rxBufferToHandleBytes);
	} else{
		lidar_expectedRxBytes = (uint8_t)usartFIFOMaxLen;
		USART_set_Bytes_to_receive(lidar_comParam.usartNo, usartFIFOMaxLen);
	}	
}

static inline uint8_t lidar_checkRXData(uint8_t* data, uint16_t dataLen, uint16_t rxChecksumValue){
	return (lidar_checksum16(data,dataLen)==rxChecksumValue);
}

static uint8_t lidar_dataCheck(uint8_t* input_p, const uint8_t* defaultVal_p, uint8_t defaultValLen){
	uint8_t result = 1;
	for (volatile uint8_t i = 0; i < defaultValLen; i++){
		if (input_p[i] != defaultVal_p[i]){
			result = 0;
			break;
		}
	}
	return result;
}

#pragma GCC push_options
#pragma GCC optimize("O3")
static int16_t lidar_getCmdDataLen(uint8_t cmdNum, uint8_t segNum){
	int16_t retVal;//keine Optimierung
	switch(cmdNum){
		case LIDAR_INIT_N_RESET:
			retVal = 0;
			break;
		case MEASURED_DATA_REQ:
			retVal = 1;
			break;
		case STATUS_REQ:
			retVal = 0;
			break;
		case ERROR_OR_TEST_TELEGRAM_REQ:
			retVal = 0;
			break;
		case OP_DATA_COUNTER_REQ:
			retVal = 0;
			break;
		case AVG_MEASURED_DATA_REQ:
			retVal = 1;
			break;
		case SEG_MEASURED_DATA_REQ:
			retVal = 4;
			break;
		case LIDAR_TYPE_REQ:
			retVal = 0;
			break;
		case MEASURED_DATA_WITH_FIELD_DATA_REQ:
			retVal = 4;
			break;
		case SEG_AVG_MEASURED_DATA_REQ:
			retVal = 5;
			break;
		case SEG_MEASURED_DATA_AND_REFLECTANCE_REQ:
			retVal = 4;
			break;
		case FIELD_REQ:
			retVal = 1;
			break;
		case FIELDS_STATUS_OUT_REQ:
			retVal = 0;
			break;
		case LIDAR_CONFIG_P1_REQ:
			retVal = 0;
			break;
		case MEASURED_DATA_WITH_REFLECTANCE_REQ:
			segNum = segNum%2;//Nur 1 bis 2 Bereiche m�glich
			retVal = (segNum?6:10);
			break;
		case MEASURED_DATA_IN_XY_COORD_REQ:
			retVal = 0;
			break;
		case LIDAR_CONFIG_P2_REQ:
			retVal = 0;
			break;
		default:
			retVal = -1;
			break;
	}
	return retVal;
}
#pragma GCC pop_options

static inline uint8_t lidar_setProtocol(uint8_t cmd, uint16_t cmdDataLen){
	uint8_t tempIdx = 0;
	lidar_protocol[LIDAR_START_BYTE_POS] = LIDAR_PROTOCOL_START_SYM;
	lidar_protocol[LIDAR_ADDR_BYTE_POS] = lidar_addr;
	lidar_protocol[LIDAR_PROTOCOL_LEN_LBYTE_POS] = (cmdDataLen+1) & 0xff;
	lidar_protocol[LIDAR_PROTOCOL_LEN_HBYTE_POS] = (cmdDataLen+1) >> 8;
	lidar_protocol[LIDAR_PROTOCOL_CMD_BYTE_POS] = cmd;
	tempIdx = LIDAR_PROTOCOL_CMD_BYTE_POS+1;
	if (cmdDataLen){
		memcpy((void*)&(lidar_protocol[tempIdx]),(void*)lidar_txDataBuffer,cmdDataLen);
		tempIdx += cmdDataLen;
	}
	lidar_tempChecksumVal = lidar_checksum16((uint8_t*)lidar_protocol,tempIdx);
	lidar_protocol[tempIdx] = lidar_tempChecksumVal & 0xff;
	tempIdx++;
	lidar_protocol[tempIdx] = lidar_tempChecksumVal >> 8;
	tempIdx++;
	return tempIdx;
}

