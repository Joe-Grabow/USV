/*
 * usvMonitorHandlerAPI.c
 *
 * Created: 7/7/2023 8:42:59 AM
 * Author: Thach
 * Version: 1.3
 * Revision: 1.1
 */

#include "usvMonitorHandlerAPI.h"

//statische Fehlerdefinition
typedef enum {
	NO_ERROR,
	NULL_POINTER,
	FIFO_EMPTY,
	FIFO_FULL,
	DATA_INVALID,
	PROCESS_FAIL,
	HANDLER_NOT_INIT
}processResult_t;

volatile uint8_t protocol[MAX_FRAME_LEN] = {0};

/**
 * \brief Bildung der checksum-Code f�r Programm
 * 
 * \param data der Zeiger zum Datenblock
 * \param len die L�nge des Datenblocks
 * \param polynom das bin�re Polynom (in hex Form)
 * 
 * \return uint8_t das checksum-Code
 */
static uint8_t crc8Checksum(uint8_t *data, uint16_t len, uint8_t polynom){
	uint8_t crc = 0;
	uint8_t mix;
	uint8_t inbyte;
	while (len--){
		inbyte = *data++;
		for (uint8_t i = 8; i; i--){
			mix = ( crc ^ inbyte ) & 0x80;
			crc <<= 1;
			if (mix){
				crc ^= polynom;
			}
			inbyte <<= 1;
		}
	}
	return crc;
}

/**
 * \brief die Position des Registers in der Liste suchen
 * 
 * \param reg die Adresse des Registers
 * 
 * \return int8_t -1: kein gefunden, sonst: die Position in der Liste
 */
static inline int16_t getRegLen(uint16_t reg){
	int16_t result = 0;
	switch(reg){
		//Sensorblock
		case SEN_GESB_ADD:
			result = 1;//0
			break;
		case SEN_LONGNITUDE_ADD:
			result = 4;//1
			break;
		case SEN_LATITUDE_ADD:
			result = 4;//2
			break;
		case SEN_SATFIX_ADD:
			result = 1;//3
			break;
		case SEN_GPS_VEL_ADD:
			result = 2;//4
			break;
		case SEN_COURSE_ANGLE_ADD:
			result = 2;//5
			break;
		case SEN_TIMESTAMP_ADD:
			result = 3;//6
			break;
		//Radar
		case RADAR_1_ADD:
			result = 1;//7
			break;
		case RADAR_2_ADD:
			result = 2;//8
			break;
		//F�hrungsgr��en der Antriebsregelung
		case REF_DRV_CTRL_REF_A_ADD:
			result = 8;//9
			break;
		case REF_DRV_CTRL_REF_B_ADD:
			result = 8;//10
			break;
		case REF_DRV_CTRL_VEL_ADD:
			result = 2;//11
			break;
		case REF_DRV_CTRL_EPS_ADD:
			result = 2;//12
			break;
		//Stellgr��en der Antriebsregelung
		case CTRL_DRV_CTRL_THRUST_ADD:
			result = 2;//13
			break;
		case CTRL_DRV_CTRL_RUDDER_ANGLE_ADD:
			result = 2;//14
			break;
		//lokaler Error Block
		case ESB_GPS_ADD:
			result = 1;//15
			break;
		case ESB_COMPASS_ADD:
			result = 1;//16
			break;
		case ESB_CTRL_ADD:
			result = 1;//17
			break;
		//Lidar
		case LIDAR_VALUE_ADD:
			result = 361;
			break;
		default:
			result = -1;
			break;
	}
	return result;
}

static inline bool checkRxData(uint8_t* data,uint16_t dataLen, uint8_t rxChecksumValue, uint8_t crc8Polynom){
	return crc8Checksum(data,dataLen,crc8Polynom)==rxChecksumValue;
}


/**
 * \brief Initalisierung des Handlers
 * 
 * \param dev_p Zeiger zum zu initalisierenden Handler 
 * \param inputRxFunc_p der Zeiger zur Datenempfangen Funktion
 * \param inputTxFunc_p der Zeiger zur Datensenden Funktion
 * \param inputWaitFunc_p der Zeiger zur Warte Funktion
 * \param inputCrc8 der Checksum-CRC8 Polynom
 * 
 * \return uint8_t 0: keinen Fehler, sonst Fehler
 */
uint8_t initDev(usvMonitorHandler_t* dev_p, dataRx_t inputRxFunc_p, dataTx_t inputTxFunc_p, uint8_t inputCrc8){
	uint8_t result = NO_ERROR;
	if ((inputRxFunc_p!=NULL)&&(inputTxFunc_p!=NULL)){
		dev_p->receiveFunc_p = inputRxFunc_p;
		dev_p->transmitFunc_p = inputTxFunc_p;
		dev_p->crc8Polynom = inputCrc8;
		dev_p->initState = 1;
	} else{
		result = NULL_POINTER;
	}
	return result;
	
}

static inline uint8_t setAndCheckData(uint8_t add, uint16_t reg, uint16_t regLen, usvMonitorHandler_t* dev_p, uint8_t* input_p, uint16_t length){
	uint8_t result = NO_ERROR;
	volatile uint8_t temp1;
	protocol[USV_START_BYTE_POS] = USV_PROTOCOL_START_BYTE;
	protocol[USV_OBJ_ID_BYTE_POS] = add;
	protocol[USV_REG_ADDR_AND_WR_LBYTE_POS] = SET_SLAVE_ADD_LOW_PART(reg);
	protocol[USV_REG_ADDR_AND_WR_HBYTE_POS] = SET_SLAVE_ADD_HIGH_PART(reg,PROTOCOL_W_REQ);
	protocol[USV_FRAME_LEN_BYTE_POS] = length+PROTOCOL_OVERHEAD_LEN;
	memcpy((uint8_t*)&(protocol[USV_DATA_BEGIN_POS]),input_p,length);
	protocol[USV_DATA_BEGIN_POS+length] = crc8Checksum(input_p,length,dev_p->crc8Polynom);
	protocol[USV_DATA_BEGIN_POS+1+length] = USV_PROTOCOL_END_BYTE;
	//Senden
	__asm__("nop");
	(*(dev_p->transmitFunc_p))((uint8_t*)protocol,USV_DATA_BEGIN_POS+2+length,(USV_DATA_BEGIN_POS+2+length)*BYTE_TRANSFER_TIME_US);//begin bei 0
	//Empfangen
	temp1 = !(*(dev_p->receiveFunc_p))((uint8_t*)&(protocol[USV_START_BYTE_POS]),1,1*BYTE_TRANSFER_TIME_US+DST_PROG_WORK_TIME_US);//magic number 1: Anzahl der empfangenen Bytes
	__asm__("nop");
	temp1 = temp1 && (protocol[USV_START_BYTE_POS] == USV_PROTOCOL_ACK_BYTE);
	if (!temp1){
		result = PROCESS_FAIL;
	}
	return result;
}

/**
 * \brief Zum Schreiben in einem Register im Slave-Ger�t
 * 
 * \param add Adresse vom Slave
 * \param reg die slavespezifische ID (Adresse von Register vom Slave)
 * \param dev_p der Zeiger zum Handler
 * \param input_p der Zeiger zur Eingabedaten 
 * \param length die L�nge der Eingabe
 * 
 * \return uint8_t 0: keinen Fehler, sonst: Fehler
 */
#pragma GCC push_options
#pragma GCC optimize ("O3")
uint8_t setData(uint8_t add, uint16_t reg, usvMonitorHandler_t* dev_p, uint8_t* input_p, uint16_t length){
	//TODO zu optimieren
	uint8_t result = NO_ERROR;
	if ((dev_p==NULL)|(input_p==NULL)){
		result = NULL_POINTER;
	} else{
		int8_t regLen = getRegLen(reg);
		if (((uint8_t)regLen) == length){
			result = setAndCheckData(add,reg,regLen,dev_p,input_p,length);
		} else{
			result = DATA_INVALID;
		}
	}
	return result;
}
#pragma GCC pop_options

/**
 * \brief zum Schreiben in vielen Registern nur mit einem Protokoll (bis zum 255 Bytes unterst�tzt)
 * 
 * \param add die Adresse vom geschriebenen Ger�t
 * \param reg die Adresse des ersten Registers im geschriebenen Datenblock
 * \param dev_p der Zeiger zum Handler
 * \param input_p das Eingabebuffer
 * \param inputLen die L�nge vom Eingabebuffer
 * 
 * \return uint8_t 0: kein Fehler, sonst: Fehler
 */
uint8_t setMultiregister(uint8_t add, uint16_t reg, usvMonitorHandler_t* dev_p, uint8_t* input_p, uint16_t inputLen){
	uint8_t result = NO_ERROR;
	if((dev_p==NULL)||(input_p==NULL)){
		result = NULL_POINTER;
	} else{
		const uint16_t maxLen = getRegLen(USV_LAST_DATA_BLOCK_ADDR) + USV_LAST_DATA_BLOCK_ADDR;
		uint16_t tempLen = (reg+inputLen);
		int8_t checkReg = (getRegLen(reg) != -1) && (tempLen <= maxLen);
		if (checkReg){
			uint8_t processTime = inputLen/PAYLOAD_PER_FRAME + ((inputLen%PAYLOAD_PER_FRAME)?1:0);
			uint16_t temp4;
			__asm__("nop");
			for (volatile uint8_t i = 0; i < processTime; i++){
				temp4 = (inputLen >PAYLOAD_PER_FRAME)?PAYLOAD_PER_FRAME:inputLen;
				result = setAndCheckData(add, reg+i*PAYLOAD_PER_FRAME, temp4,dev_p, &(input_p[i*PAYLOAD_PER_FRAME]), temp4);
				if (result==NO_ERROR){
					inputLen -= PAYLOAD_PER_FRAME;
				} else{
					result = PROCESS_FAIL;
					break;
				}
			}
			__asm__("nop");
		} else{
			result = DATA_INVALID;
		}
	}
	return result;
}

volatile uint8_t rxRes = 0;
#pragma GCC push_options
#pragma GCC optimize ("O0")
static inline uint8_t getAndCheckData(uint8_t add, uint16_t reg, uint16_t regLen, usvMonitorHandler_t* dev_p, uint8_t* output_p, uint16_t outputLen){
	uint8_t result = NO_ERROR;
	uint8_t temp1, temp2;
	uint16_t temp3;
	protocol[USV_START_BYTE_POS] = USV_PROTOCOL_START_BYTE;
	protocol[USV_OBJ_ID_BYTE_POS] = add;//slave-id = addr
	temp1 = SET_SLAVE_ADD_LOW_PART(reg);
	protocol[USV_REG_ADDR_AND_WR_LBYTE_POS] = temp1;
	temp2 = SET_SLAVE_ADD_HIGH_PART(reg,PROTOCOL_R_REQ);
	protocol[USV_REG_ADDR_AND_WR_HBYTE_POS] = temp2;
	protocol[USV_FRAME_LEN_BYTE_POS] = PROTOCOL_OVERHEAD_LEN+1;
	protocol[USV_FRAME_LEN_BYTE_POS+1] = (uint8_t)regLen;//Datenteil = L�nge des Registers
	protocol[USV_FRAME_LEN_BYTE_POS+2] = crc8Checksum((uint8_t*)&(protocol[USV_FRAME_LEN_BYTE_POS+1]),1,dev_p->crc8Polynom);//CRC8-Code
	protocol[USV_FRAME_LEN_BYTE_POS+3] = USV_PROTOCOL_END_BYTE;
	//Senden der Daten
	(*(dev_p->transmitFunc_p))((uint8_t*)protocol, USV_FRAME_LEN_BYTE_POS+3+1,(USV_FRAME_LEN_BYTE_POS+3+1)*BYTE_TRANSFER_TIME_US*2);//begin bei 0
	
	//Nach dem Request-Senden, empfangen erste Byte
	rxRes = (*(dev_p->receiveFunc_p))((uint8_t*)&(protocol[USV_START_BYTE_POS]), 1,BYTE_TRANSFER_TIME_US*1+DST_PROG_WORK_TIME_US);//magic number 0=timeout, 1=Anzahl der empfangenen Bytes
	if(protocol[USV_START_BYTE_POS] == USV_PROTOCOL_START_BYTE){ //Wenn erfolgreich, checken weitere 4 Bytes
		//Byte 4 beim Daten lesen: Bei Hinprotokoll 0x4X, bei R�ckprotokoll 0x0X => 0x4X XOR 0x0X = 0x40
		rxRes = (*(dev_p->receiveFunc_p))((uint8_t*)&(protocol[USV_OBJ_ID_BYTE_POS]), 4,BYTE_TRANSFER_TIME_US*4);
		bool checkByteReg = add == protocol[USV_OBJ_ID_BYTE_POS];
		bool checkByteAddAndRw = (temp1 == protocol[USV_REG_ADDR_AND_WR_LBYTE_POS]) && ((temp2 ^ protocol[USV_REG_ADDR_AND_WR_HBYTE_POS])==0x40);
		bool checkAll = checkByteReg && checkByteAddAndRw;
		if(checkAll){
			//empfangen weitere n Datenbytes sowie 1 CRC8- und 1 Endbyte
			rxRes = (*(dev_p->receiveFunc_p))((uint8_t*)&(protocol[USV_DATA_BEGIN_POS]), protocol[USV_FRAME_LEN_BYTE_POS]-5, (protocol[USV_FRAME_LEN_BYTE_POS]-5)*BYTE_TRANSFER_TIME_US);
			temp3 = USV_DATA_BEGIN_POS + protocol[USV_FRAME_LEN_BYTE_POS] - 7;
			bool checkDataBlock = checkRxData((uint8_t*)&(protocol[USV_DATA_BEGIN_POS]),protocol[USV_FRAME_LEN_BYTE_POS] - 7, protocol[temp3],dev_p->crc8Polynom);
			bool checkEnd = protocol[temp3+1] == USV_PROTOCOL_END_BYTE;
			if (checkEnd&&checkDataBlock){
				//kopieren aller Datenbytes in Ausgabe
				memcpy(output_p,(uint8_t*)&(protocol[USV_DATA_BEGIN_POS]),(protocol[USV_FRAME_LEN_BYTE_POS]-7));
			} else {
				result = PROCESS_FAIL;
			}
		} else{
			result = PROCESS_FAIL;
		}
	} else{
		result = PROCESS_FAIL;
	}
	return result;
}
#pragma GCC pop_options

/**
 * \brief Empfangen die Daten aus dem Slave-Ger�t, inklusiv CRC-Byte
 * 
 * \param add die Adresse vom Slave
 * \param reg die slavespezifische ID (Adresse von Register vom Slave)
 * \param dev_p der Zeiger zum Handler
 * \param output der empfangene Datenteil im gelesenen Register zusammen mit der CRC8-Checksum-Datei
 * \param outputLen die L�nge der empfangenen Daten inklusiv der Checksum
 * 
 * \return uint8_t 0: keinen Fehler, sonst: Fehler
 */
#pragma GCC push_options
#pragma GCC optimize ("O3")
uint8_t getData(uint8_t add, uint16_t reg, usvMonitorHandler_t* dev_p, uint8_t* output_p, uint16_t outputLen){
	//TODO zu optimieren
	uint8_t result = NO_ERROR;
	if((dev_p==NULL)||(output_p==NULL)){
		result = NULL_POINTER;
	} else if (dev_p->initState==0)
	{
		result = HANDLER_NOT_INIT;
	} else{
		
		int16_t regLen = getRegLen(reg);
		if (regLen!=-1){
			result = getAndCheckData(add, reg, (uint16_t) regLen, dev_p, output_p, outputLen);
		} else{
			result = DATA_INVALID;
		}
	}
	return result;
}
#pragma GCC pop_options

/**
 * \brief zum Lesen in vielen Registern nur mit einem Protokoll (bis zum 255 Bytes unterst�tzt)
 * 
 * \param add die Adresse vom abgefragten Ger�t
 * \param reg die Adresse des ersten Registers im gelesenen Datenblock
 * \param dev_p der Zeiger zum Handler
 * \param output_p das Buffer zur Ausgabe
 * \param outputLen die L�nge der Ausgabebuffer
 * 
 * \return uint8_t 0: kein Fehler, sonst: Fehler
 */
#pragma GCC push_options
#pragma GCC optimize ("O3")
uint8_t getMultiregister(uint8_t add, uint16_t reg, usvMonitorHandler_t* dev_p, uint8_t* output_p, uint16_t outputLen){
	uint8_t result = NO_ERROR;
	if((dev_p==NULL)||(output_p==NULL)){
		result = NULL_POINTER;
	} else if (dev_p->initState==0)
	{
		result = HANDLER_NOT_INIT;
	} else{
		const uint16_t maxLen = getRegLen(USV_LAST_DATA_BLOCK_ADDR) + USV_LAST_DATA_BLOCK_ADDR;
		uint16_t tempLen = (reg+outputLen);
		int8_t checkReg = (getRegLen(reg) != -1) && (tempLen <= maxLen);
		if (checkReg){
			uint8_t processTime = outputLen/PAYLOAD_PER_FRAME + ((outputLen%PAYLOAD_PER_FRAME)?1:0);
			uint16_t temp4;
			for (volatile uint8_t i = 0; i < processTime; i++){
				temp4 = (outputLen > PAYLOAD_PER_FRAME)?PAYLOAD_PER_FRAME:outputLen;
				result = getAndCheckData(add, reg+i*PAYLOAD_PER_FRAME, (uint16_t) temp4, dev_p, &(output_p[i*PAYLOAD_PER_FRAME]), temp4);
				if (result==NO_ERROR){
					outputLen -= PAYLOAD_PER_FRAME;
				} else{
					break;
				}
			}
		} else{
			result = DATA_INVALID;
		}
	}
	return result;
}
#pragma GCC pop_options



