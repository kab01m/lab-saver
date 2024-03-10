#!/bin/env python

import pyvisa
import sys
import array
from PIL import Image, ImageDraw, ImageFont

DEBUG=False

rm = pyvisa.ResourceManager()

#print (rm.list_resources())

res = rm.list_resources()

if len (res) < 1:
    print ('No resources found')
    sys.exit(0)

inst = rm.open_resource(res[0])

IDN = inst.query("*IDN?")

Voltage1 = float(inst.query("CHANnel1:SCALe?"))
Voltage2 = float(inst.query("CHANnel2:SCALe?"))
Coupling1 = inst.query("CHANnel1:COUPling?")
Coupling2 = inst.query("CHANnel2:COUPling?")

TriggerMode = inst.query("TRIGger:MODE?")

print (TriggerMode)

# You can make other modes if you are a geek
if TriggerMode.lower() in ("edge","pulse","slope"):
    TriggerSource = int(inst.query("TRIGger:" + TriggerMode + ":SOURce?")[-1])
    TriggerLevel = float(inst.query("TRIGger:" + TriggerMode + ":LEVel?"))
else:
    TriggerSource = 0

# TODO: Vectors vs Dots have different view
#Vectors = inst.query(":DISPlay:TYPE?") == "VECTors"

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

inst.timeout=15000
#inst.write(':WAVeform:DATA:ALL?')
#data = inst.read_raw()
           
try:

    inst.write(':WAVeform:DATA:ALL?')
    dataBytes = inst.read_raw()

    dataLen = len(dataBytes)
    if (dataLen > 128):
        raise Exception("Wrong message length: " + str(dataLen))
    else:
        print ("Got " + str(dataLen) + " bytes")

    data = dataBytes[0:116].decode("ascii")

    if DEBUG:
        file_id = open('hantek1.bin', 'wb')
        file_id.write(dataBytes)
        file_id.close()

    # This is probably oscilloscope bug. With only second channel turned on zero header is received
    if len(data) < 39:
        print ("Seems you run only channel 2. Channel 1 is only supported due to software bug")
        sys.exit(1)

    # Just in case this is inside try() block
    Offset1 = int(data[31:35])
    Offset2 = int(data[35:39])
    Enable1 = bool(int(data[79:80]))
    Enable2 = bool(int(data[80:81]))
    Sampler = float(data[83:92])
    #Multiplier = int(data[92:98]) # Should be used somehow? Always 1
    TriggerShift = float(data[98:107])
 
except Exception as e:
    #print ("Exception parsing DATA: " + data[:126])
    print (e)
    sys.exit(0)

""" 

https://hantek.com/uploadpic/hantek/files/20211231/DSO2000%20Series%C2%A0SCPI%C2%A0Programmers%C2%A0Manual.pdf

Official document says [with my notes]:

The first time this command is issued, the analysis of data[x] is as follows:
data[0]-data[1] (2 digits): #9 [Correct]
data[2]-data[10](9 digits):The byte length of the current packet. [Correct, always 128]
data[11]-data[19](9 digits): The total length of bytes representing the amount of data. [Seems to be useless, but correct]
data[20]-data[28](9 digits): The byte length of the uploaded data. [Nobody knows what does it mean]
data[29](1 digit): The current running status. [Correct]
data[30](1 digit): Trigger status. [Correct?]
data[31-34] (4 digits): Offset of channel 1 [Correct]
data[35-38] (4 digits): Offset of channel 2 [Correct]
data[39-42] (4 digits): Offset of channel 3 [Correct]
data[43-46] (4 digits): Offset of channel 4 [Correct]
data[47]-data[53]( 7 digit): Voltage of channel 1 [Problems: seems it is 8 bytes, not 7 and the number does not add up]
data[54]-data[60](7 digits): Voltage of channel 2 [ --//-- ]
data[61]-data[67](7 digits): Voltage of channel 3 [ --//-- ]
data[68]-data[74](7 digits): Voltage of channel 4 [ --//-- ]
data[75]-data[78] (4 digit): Channel enable of channel (1-4) [Correct with 4 byte shift because of the above]
data[79]-data[87] (9 digits): Sampling rate. [Correct + 4 bytes]
data[88]-data[93] (6digits): Sampling multiple. [Always 1 - correct? + 4 bytes]
data[94]-data[102] (9 digits): Display trigger time of current frame. [Correct + 4 bytes]
data[103]-data[111] (9 digits): The current frame displays the start point of the data acquisition start time point. [Correct? + 4 bytes]
data[112]-data[127] (16 digits): Reserved bit. [+4 bytes and 12 bytes]
"""

if (1000000 > Sampler >= 1000 ):
    SampleStr = "%.2f" % (Sampler/1000) + "K"
elif (1000000000 > Sampler >= 1000000):
    SampleStr = "%.2f" % (Sampler/1000000) + "M"
elif (Sampler >= 1000000000):
    SampleStr = "%.2f" % (Sampler/1000000000) + "G"
else:
    SampleStr = "%.2f" % Sampler
    
SampleStr = SampleStr + "Sa/s"

Scale = 250/Sampler

print (str(Sampler))
print (str(Scale))

if (Scale >= 1):
    ScaleStr = str(Scale) + "s"
if (1 > Scale >= 0.001):
    ScaleStr = str(int(Scale*1000)) + "ms"
elif (0.001 > Scale >= 0.000001):
    ScaleStr = str(int(Scale*1000000)) + "μs"
elif (0.000001 > Scale >= 0.000000001):
    ScaleStr = str(int(Scale*1000000000)) + "ns"
elif (0.000000001 > Scale >= 0.000000000001):
    ScaleStr = str(int(Scale*1000000000000)) + "ps"
else:
    ScaleStr = "undef"

if (TriggerShift == 0):
    TriggerShiftStr = "0.00s"
elif (TriggerShift >= 1):
    TriggerShiftStr =  "%.2f" % TriggerShift +  "s"
elif (1 > TriggerShift >= 0.001):
    TriggerShiftStr = "%.2f" % (TriggerShift*1000) + "ms"
elif (0.001 > TriggerShift >= 0.000001):
    TriggerShiftStr = str(int(TriggerShift*1000000)) + "μs"
else:
    TriggerShiftStr = "undef"

#TODO: Trigger value

print (ScaleStr)

print ('1' + Coupling1 + '    ' + Voltage1_Str + '   ' + str(Offset1))
print ('2' + Coupling2 + '    ' + Voltage2_Str + '   ' + str(Offset2))

inst.write(':WAVeform:DATA:ALL?')
data = inst.read_raw()

print ("Got " + str(len (data)) + " bytes")

if DEBUG:
    file_id = open('hantek2.bin', 'wb')
    file_id.write(data)
    file_id.close()

    sys.exit(0)

"""
data[x] as follows:
data[0]-data[1] (2 digits): #9 [OK]
data[2]-data[10] (9 digits): Indicates the byte length of the current data packet. [Correct]
data[11]-data[19] (9 digits): the total length of bytes representing the amount of data. [We get 4099 here, what does not add up]
data[20]-data[28] (9 digits): Indicates the byte length of the uploaded data. [IDK what is this]
data[29]-data[x]: indicates the waveform data corresponding to the current data header. [Real data, ended with 0x0A]
"""

# Real length should be taken from second field, I guess its total length minus uploaded, but I do not get it.
PacketLen = int(str(data[12:20].decode('ascii'))) - int(str(data[21:29].decode('ascii')))

# This is a bug: with 2 channels they say 8000 bytes in 4029-byte packet.
# So we can't get Channel2 with 2 channels on.
# We can't get Channel2 with only 2nd enabled because they send zero header.

# So we just take what we can - Channel1 data with 1st or both channels enabled.

if DEBUG:
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
SmallestFont = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf", 13)
SmallFont = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf", 16)
Font = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf", 20)
BigFont = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf", 20)
HugeFont = ImageFont.truetype("/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf", 22)

if (TriggerSource == 1):
    TriggerColor = Color1
if (TriggerSource == 2):
    TriggerColor = Color2

XRes = 800
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
# This never happens though because of bug mentioned above
if (not Enable1):
    Color1 = GridColor

draw.rounded_rectangle ((15, 435, 215, 475), radius=2, fill=Color1)
draw.text ((25,445), "1" + Coupling1, font=HugeFont, fill=Background)

_, _, w, h = draw.textbbox((0, 0), Voltage1_Str, font=BigFont)
draw.text ((205-w, 465-h), Voltage1_Str, font=BigFont, fill=Background)

if (not Enable2):
    Color2 = GridColor

draw.rounded_rectangle ((220, 435, 420, 475), radius=2, fill=Color2)
draw.text ((225,445), "2" + Coupling2, font=HugeFont, fill=Background)

_, _, w, h = draw.textbbox((0, 0), Voltage2_Str, font=BigFont)
draw.text ((410-w, 465-h), Voltage2_Str, font=BigFont, fill=Background)

draw.rounded_rectangle ((425, 435, 625, 475), radius=2, fill=GridColor) # Empty box for DDL: TODO

# Draw high boxes
### TODO: AUTO/STOP/TD
draw.rounded_rectangle ((165, 5, 232, 27), radius=2, fill=RunColor)
_, _, w, _ = draw.textbbox((0, 0), "TD", font=Font)
draw.text ((165+(232-165-w)/2,6), "TD", font=Font, fill=Background)

draw.rounded_rectangle ((250, 5, 270, 27), radius=2, fill=LetterColor)
draw.text ((255,6), "H", font=Font, fill=Background)
draw.rounded_rectangle ((555, 5, 575, 27), radius=2, fill=LetterColor)
draw.text ((560,6), "D", font=Font, fill=Background)
draw.rounded_rectangle ((670, 5, 690, 27), radius=2, fill=LetterColor)
draw.text ((675,6), "T", font=Font, fill=Background)

draw.text((282,6), ScaleStr, fill=SignColor, font=SmallFont)
draw.text((360,6), SampleStr, fill=SignColor, font=SmallFont)
draw.text((485,6), "4Kpt", fill=SignColor, font=SmallFont)
draw.text((592,6), TriggerShiftStr, fill=SignColor, font=SmallFont)
draw.text((695,6), "0.000V", fill=TriggerColor, font=SmallFont)

def _Arrow (Level, Color, Letter):
    print ("Level " + Letter + " = " + str(Level))
    Y = int(YCentre - Level*2)

    if (-100 <= Level <= 100):
        arr = (
            14, Y, # Tip
            7, Y-7,
            0, Y-7,
            0, Y+7,
            7, Y+7
        )
        tpos = (1,Y-6)
    elif (Level > 100): # What idiot made that software?
        Y = int(YCentre - 200)
        arr = (
            7, Y, # Tip
            14, Y+7,
            14, Y+14,
            0, Y+14,
            0, Y+7
        )
        tpos = (3,Y+3)
    else:
        Y = int(YCentre + 200)
        arr = (
            7, Y, # Tip
            14, Y-7,
            14, Y-14,
            0, Y-14,
            0, Y-7
        )
        tpos = (3,Y-14)
    print (arr)
    draw.polygon(arr, fill=Color)
    draw.text (tpos, Letter, font=SmallestFont, fill=Background)

if Enable1:
    _Arrow (Offset1, Color1, "1")
if Enable2:
    _Arrow (Offset2, Color2, "2")
if TriggerSource > 0:
    _Arrow (TriggerLevel, TriggerColor, "T")

# It seems scope cut 15 dots from every side, so we do too
for i in range(15,XRes-15):
    #draw.point((i, int.from_bytes(data[29], byteorder='little', signed=False)))
    for j in range(4):
        ByteNo = 29+i*5+j
        Value = data[ByteNo]
        if Value > 127:
            Value = Value - 255 # Unsigned to signed
        draw.point((i, YCentre - Value*2), fill = Color1)
    #print ('Printing byte ' + str(ByteNo) + ' = ' + str(Value))

if Enable2:
    inst.write(':WAVeform:DATA:ALL?')
    data = inst.read_raw()
    print ("Got " + str(len (data)) + " bytes")
    # It seem to require second call when 2nd channel is on, but the data always the same, so we dump it

#    for i in range(15,XRes-15):
        #draw.point((i, int.from_bytes(data[29], byteorder='little', signed=False)))
#        for j in range(4):
#            ByteNo = 29+i*5+j
#            Value = data[ByteNo]
#            if Value > 127:
#                Value = Value - 255 # Unsigned to signed
#            draw.point((i, YCentre - Value*2), fill = Color2)
        #print ('Printing byte ' + str(ByteNo) + ' = ' + str(Value))


del draw
image.save("hantek2.png", "PNG")
