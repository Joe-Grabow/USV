# uart_dma_tx.py - 20.07.22
#
# 25.07.2022
# - DMA_BASE Adressen werden in Assembler-Code erstellt
#   Übergabe als Parameter entfällt

from machine import Pin, mem32
import uarray as arr
from rp2 import PIO, StateMachine, asm_pio

# --- helper -------------------------------------------------

@micropython.asm_thumb
def adr_of_array(r0):
    nop()

@micropython.asm_thumb
# read_dma_count(channel)
def read_dma_count(r0):
                     # r0 = DMA_BASE
    mov(r3, 0x40)    # Channel Offset
    mul(r3, r1)      # 4 * Pin
    mov(r1, 0x50)
    lsl(r1, r1, 24)  # DMA_BASE
    add(r1, r1, r3)  # Channel-Offset
    ldr(r0, [r1, 8]) # Register-Offset 8

@micropython.asm_thumb
# dma_busy(channel)
def dma_busy(r0):
                       # r0 = channel
    mov(r3, 0x40)      # Channel Offset
    mul(r3, r1)        # 0x40 * Pin
    mov(r1, 0x50)
    lsl(r1, r1, 24)    # DMA_BASE
    add(r1, r1, r3)
    ldrb(r0, [r1, 15]) # Offset 15 für Byte 3
    mov(r1, 1)         
    and_(r0, r1)       # test Bit 1

# DREQ-Table Kap. 2.5.3.1
# DREG für pio als Transmitter
def dreq_pio_tx(sm):
    if sm < 4:
        return sm
    else:
        return (8 + (sm & 0x03))
    
# ----DMA Write ----------------------------------------------------------

def Dma_Write(buffer_adr, buffer_size, smNumber, dmaChannel=0):
    DMA_BASE          = 0x50000000 + (dmaChannel * 0x40)
    DMA_RD_ADR        = DMA_BASE + 0x00
    DMA_WR_ADR        = DMA_BASE + 0x04
    DMA_WR_CNT        = DMA_BASE + 0x08
    DMA_WR_TRG        = DMA_BASE + 0x0C
    
    PIOx_BASE         = 0x50200000 + ((smNumber >> 2) << 20)
    PIOx_TXFx         = PIOx_BASE + 0x10 + ((smNumber & 3) * 4)
    
    mem32[DMA_RD_ADR] = buffer_adr               # Where to copy from
    mem32[DMA_WR_ADR] = PIOx_TXFx                # Where to write to
    mem32[DMA_WR_CNT] = buffer_size              # Number of items to transfer

    IRQ_QUIET         = 1                        # No interrupt
    TREQ_SEL          = dreq_pio_tx(smNumber)    # Wait for PIO_RXF
    CHAIN_TO          = dmaChannel               # Do not chain (if chain to it self)
    RING_SEL          = 0                        # No ring selected
    RING_SIZE         = 0                        # No wrapping
    INCR_READ         = 1                        # Increment read address
    INCR_WRITE        = 0                        # do not increment write address
    DATA_SIZE         = 0                        # Data size - 0=8-bit, 1=16-bit, 2=32-bit
    HIGH_PRIORITY     = 1                        # High priority
    ENABLE            = 1                        # Enabled
    
    mem32[DMA_WR_TRG] = ((IRQ_QUIET     << 21) | # Initiate the transfer
                         (TREQ_SEL      << 15) |
                         (CHAIN_TO      << 11) |
                         (RING_SEL      << 10) |
                         (RING_SIZE     <<  9) |
                         (INCR_WRITE    <<  5) |
                         (INCR_READ     <<  4) |
                         (DATA_SIZE     <<  2) |
                         (HIGH_PRIORITY <<  1) |
                         (ENABLE        <<  0))

# --- Transmitter ------------------------------------------

@asm_pio(out_init=PIO.OUT_HIGH,
         set_init=PIO.OUT_HIGH,
         fifo_join=PIO.JOIN_TX,
         out_shiftdir=PIO.SHIFT_RIGHT,
         pull_thresh=8)

def uart_tx():
    wrap_target()
    pull(block)                #  1 Warten auf Daten in der Fifo
                               #    Jetzt sind Daten eingegangen ...
    set(pins, 0)           [8] #  2 Das Startbit setzen für 9 Takte
    
    label("next_bit")
    out(pins, 1)           [7] #  3 Das nächste Bit ausgeben

    jmp(not_osre, "next_bit")  #  4 nächstes Bit ausgeben, solange OSR Daten enthält
                               #    Alle 8 Bits sind rausgeschiftet
                               #    1 Stopbit senden
    set(pins, 1)           [7] #  5 Das Stopbit für 9 Takt setzen (1 + 7 + pull )
    wrap()
    
class UART_PIO_DMA_TX(object):
    def __init__(self, statemachine, dmaChannel, tx_pin, baud=9600):
        self._tx = StateMachine(statemachine, uart_tx, freq = 9 * baud,
                out_base=Pin(tx_pin),
                set_base=Pin(tx_pin) )
        self.sm = statemachine
        self.dmaChannel = dmaChannel
        self._tx.active(1)
             
    def write(self, data, cnt = None):
        if cnt is None:
            cnt = len(data)
        else:     
            cnt = cnt if cnt <= len(data) else len(data)
        # wenn noch eine Transaktion aktiv ist, dann das Ende abwarten
        while dma_busy(self.dmaChannel):
            pass

        Dma_Write(adr_of_array(data), cnt, self.sm, self.dmaChannel)
        return cnt
    
    def dma_busy(self):
        return dma_busy(self.dmaChannel)
    
    def out_waiting(self):
        # wieviele Bytes stehen noch zum Senden an ?
        return read_dma_count(self.dmaChannel)

if __name__ == "__main__":
    
    import time
    
    # --- Test Transmitter ------------------------------------ 

    BAUD         = 9600
    tx_pin       = 26
    statemachine = 0     # [0 ...  7]
    dmaChannel   = 0     # [0 ... 11]
    
    data_size    = 70
    
    data = arr.array("B", [0] * data_size)
    for i in range(data_size):
        data[i] = 65 + i
    
    tx_1 = UART_PIO_DMA_TX(statemachine = statemachine,
                       dmaChannel = dmaChannel,
                       tx_pin = tx_pin,
                       baud=BAUD)

    def test():
        for i in range(10):
            print(f"sending {tx_1.write(data, data_size)} Bytes")
            while tx_1.dma_busy():
                print(".", end = "")
                time.sleep(.001)
            time.sleep(.001)
      
    test()
    
    print("\ndone")
