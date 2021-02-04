# esp-bloom

ESPPixelStick + ESP8266 Bias Lighting

Inspired by ScreenBloom but I don't want to have to use Hue/ZigBee lights.

This will use addressable LEDs for higher resolution.

## connecting to esp8266

### serial

Once the device is flashed, it can be connected to via serial with this command:

```shell
screen /dev/tty.usbserial-0001 115200
```

The path of your serial port might be different.  You can run `ls /dev/tty.*` to
try to find it.

## LED strips

I'm using some SK6812 LED strips I have.  They are RGB + W channels.

Due to the RGBW LEDs I need to use a nightly build of ESPixelStick fw that has support
for RGBW LEDs.

The important settings are:
- Color Order: GRBW
