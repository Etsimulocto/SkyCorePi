# 3.5 TFT SPI 480x320 ILI9488 Harness

## TFT Side Order

SDO, LED, SCK, SDI, DC/RS, RESET, CS, GND, VCC

## Working LCD-Only Harness

| TFT | Wire | Pi |
|---|---|---|
| SDO | empty / not used | optional |
| LED | Brown | Pin 17 / 3.3V |
| SCK | Green | Pin 23 / GPIO11 |
| SDI | Orange | Pin 19 / GPIO10 / MOSI |
| DC/RS | Purple | Pin 18 / GPIO24 |
| RESET | White | Pin 22 / GPIO25 |
| CS | Blue | Pin 24 / GPIO8 / CE0 |
| GND | Black | Pin 6 / GND |
| VCC | Red | Pin 1 / 3.3V |

## Leftover Wires

| Wire | Future Use | Pi |
|---|---|---|
| Yellow | optional SDO/MISO | Pin 21 / GPIO9 |
| Grey | future touch CS | Pin 26 / GPIO7 |
| Extra Brown | future touch IRQ | Pin 11 / GPIO17 |

## RJ45 Note

Test every conductor with meter. Bad ground caused blank/haunted screen.
