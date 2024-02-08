/*
 * asciiTable.h
 *
 * Created: 10/08/2023 3:13:45 PM
 *  Author: Thach
 */

#ifndef ASCIITABLE_H_INCLUDED
#define ASCIITABLE_H_INCLUDED

enum asciiChar{
    ASCII_NULL_CHAR,         ASCII_SOH_CHAR,          ASCII_STX_CHAR,          ASCII_ETX_CHAR,          ASCII_EOT_CHAR,
    ASCII_ENQ_CHAR,          ASCII_ACK_CHAR,          ASCII_BEL_CHAR,          ASCII_BS_CHAR,           ASCII_HT_CHAR,
    ASCII_LF_CHAR,           ASCII_VT_CHAR,           ASCII_FF_CHAR,           ASCII_CR_CHAR,           ASCII_SO_CHAR,
    ASCII_SI_CHAR,           ASCII_DLE_CHAR,          ASCII_DC1_CHAR,          ASCII_DC2_CHAR,          ASCII_DC3_CHAR,
    ASCII_DC4_CHAR,          ASCII_NACK_CHAR,         ASCII_SYN_CHAR,          ASCII_ETB_CHAR,          ASCII_CAN_CHAR,
    ASCII_EM_CHAR,           ASCII_SUB_CHAR,          ASCII_ESC_CHAR,          ASCII_FS_CHAR,           ASCII_GS_CHAR,
    ASCII_RS_CHAR,           ASCII_US_CHAR,           ASCII_SP_CHAR,           ASCII_EXCL_CHAR,         ASCII_QUOT_CHAR,
    ASCII_NUM_CHAR,          ASCII_DOLLAR_CHAR,       ASCII_PERCNT_CHAR,       ASCII_AMP_CHAR,          ASCII_APOS_CHAR,
    ASCII_LPAREN_CHAR,       ASCII_RPAREN_CHAR,       ASCII_AST_CHAR,          ASCII_PLUS_CHAR,         ASCII_COMMA_CHAR,
    ASCII_MINUS_CHAR,        ASCII_PERIOD_CHAR,       ASCII_SOL_CHAR,          ASCII_NUM_0_CHAR,        ASCII_NUM_1_CHAR,
    ASCII_NUM_2_CHAR,        ASCII_NUM_3_CHAR,        ASCII_NUM_4_CHAR,        ASCII_NUM_5_CHAR,        ASCII_NUM_6_CHAR,
    ASCII_NUM_7_CHAR,        ASCII_NUM_8_CHAR,        ASCII_NUM_9_CHAR,        ASCII_COLON_CHAR,        ASCII_SEMI_CHAR,
    ASCII_LT_CHAR,           ASCII_EQUALS_CHAR,       ASCII_GT_CHAR,           ASCII_QUEST_CHAR,        ASCII_COMMAT_CHAR,
    ASCII_BIG_A_CHAR,        ASCII_BIG_B_CHAR,        ASCII_BIG_C_CHAR,        ASCII_BIG_D_CHAR,        ASCII_BIG_E_CHAR,
    ASCII_BIG_F_CHAR,        ASCII_BIG_G_CHAR,        ASCII_BIG_H_CHAR,        ASCII_BIG_I_CHAR,        ASCII_BIG_J_CHAR,
    ASCII_BIG_K_CHAR,        ASCII_BIG_L_CHAR,        ASCII_BIG_M_CHAR,        ASCII_BIG_N_CHAR,        ASCII_BIG_O_CHAR,
    ASCII_BIG_P_CHAR,        ASCII_BIG_Q_CHAR,        ASCII_BIG_R_CHAR,        ASCII_BIG_S_CHAR,        ASCII_BIG_T_CHAR,
    ASCII_BIG_U_CHAR,        ASCII_BIG_V_CHAR,        ASCII_BIG_W_CHAR,        ASCII_BIG_X_CHAR,        ASCII_BIG_Y_CHAR,
    ASCII_BIG_Z_CHAR,        ASCII_LSQB_CHAR,         ASCII_BSOL_CHAR,         ASCII_RSQB_CHAR,         ASCII_HAT_CHAR,
    ASCII_LOWBAR_CHAR,       ASCII_GRAVE_CHAR,        ASCII_LITTLE_A_CHAR,     ASCII_LITTLE_B_CHAR,     ASCII_LITTLE_C_CHAR,
    ASCII_LITTLE_D_CHAR,     ASCII_LITTLE_E_CHAR,     ASCII_LITTLE_F_CHAR,     ASCII_LITTLE_G_CHAR,     ASCII_LITTLE_H_CHAR,
    ASCII_LITTLE_I_CHAR,     ASCII_LITTLE_J_CHAR,     ASCII_LITTLE_K_CHAR,     ASCII_LITTLE_L_CHAR,     ASCII_LITTLE_M_CHAR,
    ASCII_LITTLE_N_CHAR,     ASCII_LITTLE_O_CHAR,     ASCII_LITTLE_P_CHAR,     ASCII_LITTLE_Q_CHAR,     ASCII_LITTLE_R_CHAR,
    ASCII_LITTLE_S_CHAR,     ASCII_LITTLE_T_CHAR,     ASCII_LITTLE_U_CHAR,     ASCII_LITTLE_V_CHAR,     ASCII_LITTLE_W_CHAR,
    ASCII_LITTLE_X_CHAR,     ASCII_LITTLE_Y_CHAR,     ASCII_LITTLE_Z_CHAR,     ASCII_LCUB_CHAR,         ASCII_VERBAR_CHAR,
    ASCII_RCUB_CHAR,         ASCII_EQTILDE_CHAR,      ASCII_DEL_CHAR,          ASCII_EURO_CHAR,         ASCII_NONE_129_CHAR,
    ASCII_SBQUO_CHAR,        ASCII_FNOF_CHAR,         ASCII_BDQUO_CHAR,        ASCII_HELLIP_CHAR,       ASCII_DAGGER_CHAR,
    ASCII_DDAGGER_CHAR,      ASCII_CIRC_CHAR,         ASCII_PERMIL_CHAR,       ASCII_SCARON_CHAR,       ASCII_LSAQUO_CHAR,
    ASCII_OELIG_CHAR,        ASCII_NONE_141_CHAR,     ASCII_ZCARON_CHAR,       ASCII_NONE_143_CHAR,     ASCII_NONE_144_CHAR,
    ASCII_LSQUO_CHAR,        ASCII_RSQUO_CHAR,        ASCII_LDQUO_CHAR,        ASCII_RDQUO_CHAR,        ASCII_BULL_CHAR,
    ASCII_NDASH_CHAR,        ASCII_MDASH_CHAR,        ASCII_SMALL_TILDE_CHAR,  ASCII_TRADE_CHAR,        ASCII_SMALL_SCARON_CHAR,
    ASCII_RSAQUO_CHAR,       ASCII_SMALL_OELIG_CHAR,  ASCII_NONE_157_CHAR,     ASCII_SMALL_ZCARON_CHAR, ASCII_YUML_CHAR,
    ASCII_NBSP_CHAR,         ASCII_IEXCL_CHAR,        ASCII_CENT_CHAR,         ASCII_POUND_CHAR,        ASCII_CURREN_CHAR,
    ASCII_YEN_CHAR,          ASCII_BRVBAR_CHAR,       ASCII_SECT_CHAR,         ASCII_UML_CHAR,          ASCII_COPY_CHAR,
    ASCII_ORDF_CHAR,         ASCII_LAQUO_CHAR,        ASCII_NOT_CHAR,          ASCII_SHY_CHAR,          ASCII_REG_CHAR,
    ASCII_MACR_CHAR,         ASCII_DEG_CHAR,          ASCII_PLUSMN_CHAR,       ASCII_SUP2_CHAR,         ASCII_SUP3_CHAR,
    ASCII_ACUTE_CHAR,        ASCII_MICRO_CHAR,        ASCII_PARA_CHAR,         ASCII_MIDDOT_CHAR,       ASCII_CEDIL_CHAR,
    ASCII_SUP1_CHAR,         ASCII_ORDM_CHAR,         ASCII_RAQUO_CHAR,        ASCII_FRAC14_CHAR,       ASCII_FRAC12_CHAR,
    ASCII_FRAC34_CHAR,       ASCII_IQUEST_CHAR,       ASCII_AGRAVE_CHAR,       ASCII_AACUTE_CHAR,       ASCII_ACIRC_CHAR,
    ASCII_ATILDE_CHAR,       ASCII_AUML_CHAR,         ASCII_ARING_CHAR,        ASCII_BIG_AELIG_CHAR,    ASCII_BIG_CCEDIL_CHAR,
    ASCII_BIG_EGRAVE_CHAR,   ASCII_BIG_EACUTE_CHAR,   ASCII_BIG_ECIRC_CHAR,    ASCII_BIG_EUML_CHAR,     ASCII_BIG_IGRAVE_CHAR,
    ASCII_BIG_IACUTE_CHAR,   ASCII_BIG_ICIRC_CHAR,    ASCII_BIG_IUML_CHAR,     ASCII_BIG_ETH_CHAR,      ASCII_BIG_NTILDE_CHAR,
    ASCII_BIG_OGRAVE_CHAR,   ASCII_BIG_OACUTE_CHAR,   ASCII_BIG_OCIRC_CHAR,    ASCII_BIG_OTILDE_CHAR,   ASCII_BIG_OUML_CHAR,
    ASCII_TIMES_CHAR,        ASCII_BIG_OSLASH_CHAR,   ASCII_BIG_UGRAVE_CHAR,   ASCII_BIG_UACUTE_CHAR,   ASCII_BIG_UCIRC_CHAR,
    ASCII_BIG_UUML_CHAR,     ASCII_BIG_YACUTE_CHAR,   ASCII_BIG_THORN_CHAR,    ASCII_SZLIG_CHAR,        ASCII_SMALL_AGRAVE_CHAR,
    ASCII_SMALL_AACUTE_CHAR, ASCII_SMALL_ACIRC_CHAR,  ASCII_SMALL_ATILDE_CHAR, ASCII_SMALL_AUML_CHAR,   ASCII_SMALL_ARING_CHAR,
    ASCII_SMALL_AELIG_CHAR,  ASCII_SMALL_CCEDIL_CHAR, ASCII_SMALL_EGRAVE_CHAR, ASCII_SMALL_EACUTE_CHAR, ASCII_SMALL_ECIRC_CHAR,
    ASCII_SMALL_EUML_CHAR,   ASCII_SMALL_IGRAVE_CHAR, ASCII_SMALL_IACUTE_CHAR, ASCII_SMALL_ICIRC_CHAR,  ASCII_SMALL_IUML_CHAR,
    ASCII_SMALL_ETH_CHAR,    ASCII_SMALL_NTILDE_CHAR, ASCII_SMALL_OGRAVE_CHAR, ASCII_SMALL_OACUTE_CHAR, ASCII_SMALL_OCIRC_CHAR,
    ASCII_SMALL_OTILDE_CHAR, ASCII_SMALL_OUML_CHAR,   ASCII_DIVIDE_CHAR,       ASCII_SMALL_OSLASH_CHAR, ASCII_SMALL_UGRAVE_CHAR,
    ASCII_SMALL_UACUTE_CHAR, ASCII_SMALL_UCIRC_CHAR,  ASCII_SMALL_UUML_CHAR,   ASCII_SMALL_YACUTE_CHAR, ASCII_SMALL_THORN_CHAR,
    ASCII_SMALL_YUML_CHAR
};

#endif // ASCIITABLE_H_INCLUDED