# uart_dma_rx.py - 21.07.22
#
# 25.07.2022
# - DMA_BASE Adressen werden in Assembler-Code erstellt
#   Übergabe als Parameter entfällt
# - bit_reverse_8(): Read- / Write-Adr können unterschiedlich sein
# - Daten können über ein externes Array abgeholt werden.

from machine import Pin, mem32
import uarray as arr
from rp2 import PIO, StateMachine, asm_pio

# --- helper -------------------------------------------------

@micropython.asm_thumb
def adr_of_array(r0):
    nop()

"""
@micropython.asm_thumb
# write_mem32(register, value)
def write_mem32(r0, r1): 
    str(r1, [r0, 0]) # Channel Offset
"""

@micropython.asm_thumb
# read_dma_count(channel)
def read_dma_count(r0):
                     # r0 = DMA_BASE
    mov(r3, 0x40)    # Channel Offset
    mul(r3, r0)      # 4 * Pin
    mov(r1, 0x50)
    lsl(r1, r1, 24)  # DMA_BASE
    add(r1, r1, r3)  # Channel-Offset
    ldr(r0, [r1, 8]) # Register-Offset 8

@micropython.asm_thumb
# read_dma_trig(channel)
def read_dma_trig(r0):
                      # r0 = DMA_BASE
    mov(r3, 0x40)     # Channel Offset
    mul(r3, r0)       # 4 * Pin
    mov(r1, 0x50)
    lsl(r1, r1, 24)   # DMA_BASE     
    add(r1, r1, r3)
    ldr(r0, [r1, 12]) # Offset 12

@micropython.asm_thumb
# dma_busy(channel)
def dma_busy(r0):
                       # r0 = channel
    mov(r3, 0x40)      # Channel Offset
    mul(r3, r0)        # 0x40 * Pin
    mov(r1, 0x50)
    lsl(r1, r1, 24)    # DMA_BASE
    add(r1, r1, r3)
    ldrb(r0, [r1, 15]) # Offset 15 für Byte 3
    mov(r1, 1)         
    and_(r0, r1)       # test Bit 1

# setzt das Bit für den Channel in Register CHAN_ABORT
# wartet bis das Bit gelöscht wurde
# dma_abort(DMA_BASE, dmaChannel)
@micropython.asm_thumb
def dma_abort(r0):
    mov(r1, 0x50)
    lsl(r1, r1, 24)    # r1 = DMA_BASE   
    
    mov(r2, 0x04)
    lsl(r2, r2, 8)
    mov(r3, 0x44)
    add(r2, r2, r3)   # r2 = 0x444 = Reg-Offset
    add(r1, r1, r2)   # Register DMA-Abort
    
    mov(r2, 1)
    lsl(r2, r0)       # r0 = channel bit
    str(r2, [r1, 0])  # Bit schreiben
    
    label(WAIT)
    ldr(r3, [r1, 0])  # CHAN_ABORT Register laden
    and_(r3, r2)      # Channel-Bit freistellen
    cmp(r2, r3)       # vergleichen mit Maske
    beq(WAIT)

# Kehrt die Bitreihenfolge einer Folge von Bytes (8 Bit) um
# Der PIO-UART-Receiver kann damit die empfangenen Bits
# mit PIO.SHIFT_RIGHT einlesen, damit können die Daten
# in ein array aus uint8 (anstelle uint32) eingelesen werden.
@micropython.asm_thumb
# bit_reverse_8(source-adr, target_adr, count)
def bit_reverse_8(r0, r1, r2) -> uint:
                         # r0 = Source-Adresse
                         # r1 = Target-Adresse
    add(r2, r0, r2)      # r2 = End-adresse r0 + r2
                         # r3 = Zwischenrrgebnis von "and"
                         # r4 = Bitzähler
    mov(r5, 0x80)        # r5 = Konstante "0x80" (Bitmaske)
                         # r6 = reversed Wert
    label(NEXTBYTE)
    ldrb(r7, [r0, 0])    # r7 = Ausgangswert
    mov(r6, 0)           # Ergebnisregister löschen
    mov(r4, 8)           # Bitzähler auf 8
    
    label(NEXTBIT)
    lsr(r6, r6, 1)       # das Bit war nicht gesetzt, nach rchts shiften
    mov(r3, r7)          # Wert nach r3 kopieren für and mit 0x80 
    and_(r3, r5)         # ist das 7.Bit gesetzt
    cmp(r3, r5)          # war das Bit 7 gesetzt
    bne(LOWBIT)
    orr(r6, r5)          # wenn ja, dann das Bit 7 im Ziel setzen
    
    label(LOWBIT)   
    lsl(r7, r7, 1)       # den Ausgangswert nach links shiften
    sub(r4, r4, 1)       # Den Bitcounter um 1 decrementieren
    mov(r3, 0)           # Vergleichswert 0 nach r3
    cmp(r4, r3)          # mit "0" vergleihcen
    bne(NEXTBIT)         # wenn noch nicht 0, dann das nächste Bit
    
    strb(r6, [r1, 0])    # alle Bits sind reversed, Ergebnis zurückschreiben
    
    add(r0, r0, 1)       # Adresse incrementieren
    add(r1, r1, 1)       # 
    cmp(r0, r2)          # ist das Ende erreicht ?
    bne(NEXTBYTE)        # wenn nicht, dann das nächste Byte bearbeiten
                         # in r0 steht die nächst folgende Adresse

# DREQ-Table Kap. 2.5.3.1
# DREG für pio als Receiver
def dreq_pio_rx(sm):
    if sm < 4:
        return (4 + sm)
    else:
        return (12 + (sm & 0x03))

# --- DMA - Read ----------------------------------------------------- 
 
def Dma_Read(buffer_adr, buffer_size, smNumber, dmaChannel=0):
    DMA_BASE          = 0x50000000 + (dmaChannel * 0x40)
    DMA_RD_ADR        = DMA_BASE + 0x00
    DMA_WR_ADR        = DMA_BASE + 0x04
    DMA_WR_CNT        = DMA_BASE + 0x08
    DMA_WR_TRG        = DMA_BASE + 0x0C
    
    PIOx_BASE         = 0x50200000 + ((smNumber >> 2) << 20)
    PIOx_RXFx         = PIOx_BASE + 0x20 + ((smNumber & 3) * 4)
    
    mem32[DMA_RD_ADR] = PIOx_RXFx                # Where to copy from
    mem32[DMA_WR_ADR] = buffer_adr               # Where to write to
    mem32[DMA_WR_CNT] = buffer_size              # Number of items to transfer

    IRQ_QUIET         = 1                        # No interrupt
    TREQ_SEL          = dreq_pio_rx(smNumber)    # Wait for PIO_RXF
    CHAIN_TO          = dmaChannel               # Do not chain (if chain to it self)
    RING_SEL          = 0                        # No ring selected
    RING_SIZE         = 0                        # No wrapping
    INCR_READ         = 0                        # Do not increment read address
    INCR_WRITE        = 1                        # Increment write address
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
    
def Dma_Trigger_WriteAdr(dmaChannel, buffer_adr):
    # Trigger Alias 2 -> Write Adress
    # Startet den DMA-Transfer durch Schreiben einer neuen Write-Adresse
    # Der Counter und die Source Adresse bleiben unverändert !
    DMA_WR_ADR        = 0x50000000 + 0x2C + (dmaChannel * 0x40)
    mem32[DMA_WR_ADR] = buffer_adr

# --- UART - RX -----------------------------------------------------------

# Prüft das Startbit 2x, das Stopbit und die nachfolgende Pause
# Jedes Bit hat eine Länge von 15 PIO-Takten.
# Die Datenbits werden jeweils 1x in der Bitmitte abgetastet.
# Takt = Baud * 15

@asm_pio(in_shiftdir=PIO.SHIFT_LEFT,
        fifo_join=PIO.JOIN_RX ) 

def uart_rx():
    label("restart")  
    mov(isr, null)            #  1 Bei einem Fehler sicherheitshalber das ISR zurücksetzen
    
    wait(0, pin, 0)       [1] #  2 Warten auf eine fallende Flanke
    
    label("start")    
    wrap_target() 
    set(y, 7)                 #  3 den Counter fpr die Bits setzen
                              #    Das Signal ist mindestens 4 Takte gesetzt
    jmp(pin, "restart")   [6] #  4 - Fehler, wenn der Takt das Startbit nicht mehr low 
    jmp(pin, "restart")  [12] #  5 - Fehler, wenn der Takt das Startbit nicht mehr low 
    label("next_bit")
    
    in_(pins, 1)         [13] #  6 Den Pegel einlesen und nach
    
    jmp(y_dec, "next_bit")    #  7 weiteren 15 Takten das nächste Bit einlesen
    
    jmp(pin, "stop_bit_1")    #  8 Das Stopbit muss high, sein 
    jmp("restart")            #  9 wenn nicht gesetzt, dann ist das ein Fehler
    
    label("stop_bit_1")
    jmp(pin, "byte_end")      # 10 Das Stopbit muss high sein, 
    jmp("restart")            # 11 wenn nicht gesetzt, dann ist das ein Fehler                         
    
    label("byte_end")
    push(block)          [3]  # 12 die empfangenen Bits ins Fifo

    label("end_1")
    set(y, 4)                 # 13 Wartezeit nach dem Stopbit nach 'y'
                              #    wenn innerhalb dieser Zeit der Level nicht
                              #    azf gnd geht, dann ist die Übertragung beendet
    label("end_2")
    jmp(y_dec, "end_3")       # 14 Zähler Wartezeit decrementieren
    jmp("read_end")           # 15
    
    label("end_3")            #
    jmp(pin, "end_2")         # 16 hier prüfen, ob eine fallende Flanke auftrat 
    wrap()                    #    wenn ja, dann das nächste Byte einlesen
 
    label("read_end")
    irq(rel(0))               # 17 den Interrupt auslösen
    
    jmp("restart")            # 18
    
class UART_PIO_DMA_RX(object):
    def __init__(self, statemachine, dmaChannel, rx_pin,
                 buffer_size, callback = None, baud = 9600):
        self.sm = StateMachine(statemachine, uart_rx, 
                in_base=Pin(rx_pin, Pin.IN, Pin.PULL_UP),
                jmp_pin=Pin(rx_pin, Pin.IN, Pin.PULL_UP),
                freq=baud * 15)
        
        self.statemachine = statemachine
        self.dmaChannel   = dmaChannel
        self.buffer_size  = buffer_size
        self.callback     = callback
        self.rx_recv      = 0          # Anzahl der empfangenen Bytes
        self.rx_msg_cnt   = 0          # counter fur gelesene Datensätze
                                       # >1 -> Datensätze wurden überschrieben
        self.buffer_1 = arr.array("B", [0x65] * buffer_size)
        self.buffer_2 = arr.array("B", [0x66] * buffer_size)

        self.sm.irq(self._irq_handler)
        Dma_Read(adr_of_array(self.buffer_1), self.buffer_size,
                 self.statemachine, self.dmaChannel)

        self.sm.active(1)
        while self.sm.rx_fifo():
            print(self.sm.get())
        
    def active(self, state=None):
        if state is None:
            return self.sm.active()
        if state:
            self.sm.active(1)
            self.idx = 0
            Dma_Trigger_WriteAdr(self.dmaChannel, adr_of_array(self.buffer_1))
        else:
            self.sm.active(0)
            self._stop()
        
    def _irq_handler(self, _):
        # wird ausgelöst, wenn kein weiteres Startbit erkannt wurde.
        # liest das DMA-Count Register aus: -> wieviele Bytes wurden gelesen ?
        self.rx_recv = self.buffer_size - read_dma_count(self.dmaChannel)
        self.rx_msg_cnt += 1
        # eine nicht abgeschlossen Transaktion beenden
        if dma_busy(self.dmaChannel):
                dma_abort(self.dmaChannel)

        # den Receiver neu starten 
        Dma_Trigger_WriteAdr(self.dmaChannel, adr_of_array(self.buffer_1))
        # die Bitreihenfolge der empfangenen Bytes umkehren
        # von buffer_1 lesen und nach buffer_2 schreiben
        bit_reverse_8(self.buffer_1, self.buffer_2, self.rx_recv)
        if self.callback is not None:
            self.callback(self.buffer_2, self.rx_recv)
    
    def _stop(self):
        dma_abort(self.dmaChannel)
 
    def ready(self):
        # wieviele Bytes wurden empfangen ?
        return self.rx_recv

    def get_buffer(self):
        cnt = self.rx_recv
        self.rx_recv = 0
        return (self.buffer_2, cnt)
 
    def check(self):
        if not dma_busy(self.dmaChannel):
            if self.sm.active():
                # der DMA-Buffer ist voll !
                raise IndexError("dma-buffer overflow")
        
if __name__ == "__main__":
    
    import time
    
    def callback(buffer, recv):
        print(f"received: {recv} Bytes in {buffer}")
    
    # --- Test Receiver -------------------------------
        
    BAUD         = 9600 
    rx_pin       = 27
    buffer_size  = 20
    statemachine = 1     # [0 ...  7]
    dmaChannel   = 1     # [0 ... 11]
    a = arr.array("b", [0] * 5)
    rx_1 = UART_PIO_DMA_RX(statemachine=statemachine,
                 dmaChannel=dmaChannel,
                 rx_pin=rx_pin,
                 buffer_size = buffer_size,
                 # callback = callback,
                 baud=BAUD)
    '''
    BAUD         = 9600 
    rx_pin       = 13
    buffer_size  = 40
    statemachine = 1     # [0 ...  7]
    dmaChannel   = 2     # [0 ... 11]
      
    rx_2 = UART_PIO_DMA_RX(statemachine=statemachine,
                 dmaChannel=dmaChannel,
                 rx_pin=rx_pin,
                 buffer_size=buffer_size,
                 baud=BAUD)
    
    BAUD         = 9600 
    rx_pin       = 12
    buffer_size  = 40
    statemachine = 4     # [0 ...  7]
    dmaChannel   = 3     # [0 ... 11]
      
    rx_3 = UART_PIO_DMA_RX(statemachine=statemachine,
                 dmaChannel=dmaChannel,
                 rx_pin=rx_pin,
                 buffer_size=buffer_size,
                 baud=BAUD)
    
    BAUD         = 9600 
    rx_pin       = 11
    buffer_size  = 40
    statemachine = 7     # [0 ...  7]
    dmaChannel   = 4     # [0 ... 11]
      
    rx_4 = UART_PIO_DMA_RX(statemachine=statemachine,
                 dmaChannel=dmaChannel,
                 rx_pin=rx_pin,
                 buffer_size=buffer_size,
                 baud=BAUD)
    '''
    print("\nWaiting for UART-Data ... Ctrl-C to stop.")
    
    rx_1.active(1)
    #rx_2.active(1)
    #rx_3.active(1)
    #rx_4.active(1)
    
    try:    
        while True:
            if rx_1.ready():
                d, cnt = rx_1.get_buffer()
                print("rx_1", end = " ")
                for i in range(cnt):
                    print(f"{d[i]:02X}", end = " ")
                print(f" -> #{cnt}")
            rx_1.check()
            '''
            if rx_2.ready():
                d, cnt = rx_2.get_buffer()
                print("rx_2", end = " ")
                for i in range(cnt):
                    print(f"{d[i]:02X}", end = " ")
                print(f" -> #{cnt}")
            rx_2.check()
                
            if rx_3.ready():
                d, cnt = rx_3.get_buffer()
                print("rx_3", end = " ")
                for i in range(cnt):
                    print(f"{d[i]:02X}", end = " ")
                print(f" -> #{cnt}")
            rx_3.check()

            if rx_4.ready():
                d, cnt = rx_4.get_buffer()
                print("rx_4", end = " ")
                for i in range(cnt):
                    print(f"{d[i]:02X}", end = " ")
                print(f" -> #{cnt}")
            rx_4.check()
            '''
    except KeyboardInterrupt:
        pass

    rx_1.active(0)
    #rx_2.active(0)
    #rx_3.active(0)
    #rx_4.active(0)
    
    print("\ndone")
