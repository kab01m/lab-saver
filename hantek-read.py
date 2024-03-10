#!/bin/env python

import pyvisa
import sys
from PIL import Image, ImageDraw, ImageFont

Voltage1 = 0.5
Voltage2 = 10
Coupling1 = 'DC'
Coupling2 = 'DC'

match Voltage1:
    case Voltage1 if Voltage1 >= 1:
        Voltage1_Str = str (int(Voltage1)) + 'V'
    case Volatage1 if 1 > Voltage1 >= 0.001:
        Voltage1_Str = str (int(Voltage1*1000)) + 'mV'
    case _:
        Voltage1_Str = 'UNDEF'

match Voltage2:
    case Voltage2 if Voltage2 >= 1:
        Voltage2_Str = str (int(Voltage2)) + 'V'
    case Volatage2 if 1 > Voltage2 >= 0.001:
        Voltage2_Str = str (int(Voltage2*1000)) + 'mV'
    case _:
        Voltage2_Str = 'UNDEF'

Offset1 = 10
Offset2 = 20

print ('1' + Coupling1 + '    ' + Voltage1_Str + '   ' + str(Offset1))
print ('2' + Coupling2 + '    ' + Voltage2_Str + '   ' + str(Offset2))

f = open("hantek2.bin", mode="rb")
data = f.read()

# Real length should be taken from second field, I guess its total length - uploaded, but I do not get it.

PacketLen = int(str(data[12:20].decode('ascii'))) - int(str(data[21:29].decode('ascii')))

print ("Packet length is " + str(PacketLen))

# Set up colors
Background = "black"
Color1 = "yellow" # Channel 1
Color2 = "lime" # Chennel 2
GridColor = "#312438" # Feel free to change it
RunColor = "green" # Running button if run
RunColorStop = "crimson" # Running button if stopped
LetterColor = "cornflowerblue" # Small letter boxes
SignColor = "white" # Text on black
HorPosMarkerColor = "blue"
SmallFont = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf", 16)
Font = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf", 20)
BigFont = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf", 20)
HugeFont = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf", 22)

# This is dirty hack
XRes = int(PacketLen/5)
YRes = 480

image = Image.new("RGBA", (XRes, YRes), (0,0,0,0))

draw = ImageDraw.Draw(image)

# Draw background
draw.rectangle((0,0,XRes,YRes), fill=Background)

# Imprint logo
logo = Image.open('hantek-logo2.png', 'r')
logo.thumbnail([sys.maxsize, 26])
print (logo.mode == 'RGBA')
image.paste(logo, (16,2), logo)

# Draw grid

# Grid center is shifted up a little on Y, 10 points is just a guess
YCentre=YRes/2-10
for y in range(30,431,50):
    draw.line ((15,y,785,y),fill=GridColor)

# This looks almost precise
for x in [15, *range(50,751,50), 785]:
    draw.line ((x,30,x,430),fill=GridColor)

# Guide lines
GridH = 4
for y in [30, 430-GridH, YCentre-GridH, YCentre]:
    for x in range(20,785,10):
        draw.line ((x,y,x,y+GridH),fill=GridColor)

for x in [15, 785-GridH, XRes/2-GridH, XRes/2 ]:
    for y in range(30,430,10):
        draw.line ((x,y,x+GridH,y),fill=GridColor)

# Draw low boxes 
draw.rounded_rectangle ((15, 435, 215, 475), radius=2, fill=Color1)
draw.text ((25,445), "1" + Coupling1, font=HugeFont, fill=Background)

_, _, w, h = draw.textbbox((0, 0), Voltage1_Str, font=BigFont)
draw.text ((205-w, 465-h), Voltage1_Str, font=BigFont, fill=Background)

draw.rounded_rectangle ((220, 435, 420, 475), radius=2, fill=Color2)
draw.text ((225,445), "2" + Coupling2, font=HugeFont, fill=Background)

_, _, w, h = draw.textbbox((0, 0), Voltage2_Str, font=BigFont)
draw.text ((410-w, 465-h), Voltage2_Str, font=BigFont, fill=Background)

draw.rounded_rectangle ((425, 435, 625, 475), radius=2, fill=GridColor) # No DDL

# Draw high boxes
draw.rounded_rectangle ((165, 5, 232, 27), radius=2, fill=RunColor)
_, _, w, _ = draw.textbbox((0, 0), "TD", font=Font)
draw.text ((165+(232-165-w)/2,6), "TD", font=Font, fill=Background)

draw.rounded_rectangle ((250, 5, 270, 27), radius=2, fill=LetterColor)
draw.text ((255,6), "H", font=Font, fill=Background)
draw.rounded_rectangle ((555, 5, 575, 27), radius=2, fill=LetterColor)
draw.text ((560,6), "D", font=Font, fill=Background)
draw.rounded_rectangle ((670, 5, 690, 27), radius=2, fill=LetterColor)
draw.text ((675,6), "T", font=Font, fill=Background)

draw.text((282,6), "220us", fill=SignColor, font=SmallFont)
draw.text((370,6), "1.25MSa/s", fill=SignColor, font=SmallFont)
draw.text((480,6), "4Kpt", fill=SignColor, font=SmallFont)
draw.text((600,6), "0.00s", fill=SignColor, font=SmallFont)
draw.text((695,6), "3.44V", fill=Color1, font=SmallFont)

for i in range(15,XRes-15):
    #draw.point((i, int.from_bytes(data[29], byteorder='little', signed=False)))
    for j in range(4):
        ByteNo = 29+i*5+j
        Value = data[ByteNo]
        if Value > 127:
            Value = Value - 255
        draw.point((i, YCentre - Value*2), fill = Color1)
    #print ('Printing byte ' + str(ByteNo) + ' = ' + str(Value))

del draw
image.save("hantek2.png", "PNG")

