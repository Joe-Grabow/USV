from picozero import LED, Button

led = LED(21)
button = Button(20)

button.when_pressed = led.on
button.when_released = led.off