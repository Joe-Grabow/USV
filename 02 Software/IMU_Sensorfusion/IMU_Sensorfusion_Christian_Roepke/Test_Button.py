from machine import Pin, Timer

# Initialization of GPIO21 as output
led_onboard = Pin(21, Pin.OUT, value = 0)
led_onboard.off()

# Initialization of GPIO20 as input with external PULLUP resistor 
btn = Pin(20, Pin.IN)

# push-button function
def on_pressed(timer):
    led_onboard.toggle()
    print('pressed')

# debounce function
def btn_debounce(pin):
    # set timer (period in milliseconds)
    Timer().init(mode = Timer.ONE_SHOT, period = 200, callback = on_pressed)

# button triggering
btn.irq(handler = btn_debounce, trigger = Pin.IRQ_FALLING)

# button evaluation function
while True:
    # switch not pressed (logical "1")
    if btn.value() == 1:
        led_onboard.off()
    # switch pressed (logical "0")
    else:
        led_onboard.on()