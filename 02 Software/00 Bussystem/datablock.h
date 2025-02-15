/////////////////////////////////////////////////////////////////////////////////////////
// datablock.h
//
// Created: 19.01.2024 16:00:18
//  Author: Franke
//
//  file rev. 1.0
//
//  - Header for documentation "\USV\00 doc\00 Bussystem\Bussystem.pdf"
//
//  - data rev. 1
//
/////////////////////////////////////////////////////////////////////////////////////////

#ifndef DATABLOCK_H_
#define DATABLOCK_H_

/////////////////////////////////////////////////////////////////////////////////////////
//
// Enumeratoren
//
/////////////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////////////////
// Datenblock Addressen
/////////////////////////////////////////////////////////////////////////////////////////
enum DatablockAddresses_e
{
	SB1  = 0x0000,
	SB2  = 0x0001,
	SB3  = 0x0005,
	SB4  = 0x0009,
	SB5  = 0x000A,
	SB6  = 0x000C,
	SB7  = 0x000E,
	SB8  = 0x0012,
	SB9  = 0x0014,
	SB20 = 0x0020,
	SB21 = 0x0024,
	SB22 = 0x0028,
	SB23 = 0x0029,
	SB24 = 0x002B,
	SB25 = 0x002D,
	SB26 = 0x002F,
	SB27 = 0x0031,
	SB28 = 0x0033,
	SB29 = 0x0035,
	SB30 = 0x0037,
	SB31 = 0x0039,
	SB32 = 0x003B,
	SB33 = 0x003D,
	AF1  = 0x0100,
	AF2  = 0x0108,
	AF3  = 0x0110,
	AF4  = 0x0112,
	AS1  = 0x0120,
	AS2  = 0x0122,
	EM1  = 0x0130,
	EM2  = 0x0132,
	EM3  = 0x0134,
	EM4  = 0x0136,
	EM5  = 0x0138,
	EM6  = 0x013A,
	EM7  = 0x013C,
	EM8  = 0x013E,
	EM9  = 0x013F,
	ER1  = 0x0200,
	ER2  = 0x0201,
	ER3  = 0x0202,
	ER4  = 0x0203,
	ER5  = 0x0204,
	ER6  = 0x0205,
	ER7  = 0x0206,
	ER8  = 0x0207,
	ER9  = 0x0208,
	ES1  = 0x0220,
}

/////////////////////////////////////////////////////////////////////////////////////////
// Datenblock Längen
/////////////////////////////////////////////////////////////////////////////////////////
enum DatablockLength_e
{
	SB1_len  = 001,
	SB2_len  = 004,
	SB3_len  = 004,
	SB4_len  = 001,
	SB5_len  = 002,
	SB6_len  = 002,
	SB7_len  = 003,
	SB8_len  = 002,
	SB9_len  = 001,
	SB20_len = 004,
	SB21_len = 004,
	SB22_len = 001,
	SB23_len = 002,
	SB24_len = 002,
	SB25_len = 002,
	SB26_len = 002,
	SB27_len = 002,
	SB28_len = 002,
	SB29_len = 002,
	SB30_len = 002,
	SB31_len = 002,
	SB32_len = 002,
	SB33_len = 002,
	AF1_len  = 008,
	AF2_len  = 008,
	AF3_len  = 002,
	AF4_len  = 002,
	AS1_len  = 002,
	AS2_len  = 002,
	EM1_len  = 002,
	EM2_len  = 002,
	EM3_len  = 002,
	EM4_len  = 002,
	EM5_len  = 002,
	EM6_len  = 002,
	EM7_len  = 002,
	EM8_len  = 001,
	EM9_len  = 002,
	ER1_len  = 001,
	ER2_len  = 001,
	ER3_len  = 001,
	ER4_len  = 001,
	ER5_len  = 001,
	ER6_len  = 001,
	ER7_len  = 001,
	ER8_len  = 001,
	ER9_len  = 001,
	ES1_len  = 362,
}

#endif // DATABLOCK_H_ //

