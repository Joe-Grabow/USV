from machine import Pin, Timer

led = Pin("LED", Pin.OUT)
tim = Timer()
#led.value(0)
def tick(timer):
  global led
  led.toggle()
 
tim.init(freq=2.5, mode=Timer.PERIODIC, callback=tick)

