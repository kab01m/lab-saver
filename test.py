f = open("hantek2.bin", mode="rb")
data = f.read()

print (hex(data[28]))
for i in range(5):
    print (str(i))
