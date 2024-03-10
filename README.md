# Bench data aquisition helper

This project is designed for Electronics Work Bench.

Place Raspberry PI (or anything running Linux), connect some buttons on GPIO and use them to:
* Get image from Hantek DSO2x1x oscilloscope via SCPI.
* Upload image into Nextcloud instance.

## hantek-read.py
Hantek DSO2x1x oscilloscope is not capable to transfer screenshot, so we capture data and use PIL library to put data into image. There are some considerations due to Hantek bugs:
* Scope is not capable to send 2nd channel data (maybe I am using it wrong)
* Scope is sending empty header if 1st channel is off.

So, for now, we capture 1st channel only and always.
