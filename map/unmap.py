import binascii
import struct
import sys

with open(sys.argv[1],'rb') as image:
    debug = True
    if debug:
        print "Header"
        print "------"
        print "Signature: ", image.read(2) ## Signature
        print "Filesize: ", struct.unpack('<I', image.read(4))[0] # file size
        print "Reserved: ", binascii.hexlify(image.read(4)) # reserved
        print "PixelDataOffset: ", struct.unpack('<I', image.read(4))[0] # data offset
        print "------"
        print "DIB Header"
        print "----------"
        print "Header Size: ", struct.unpack('<I', image.read(4))[0] # header size, should be 40
        print "Image Width: ", struct.unpack('<i', image.read(4))[0] # image width
        print "Image Height: ", struct.unpack('<i', image.read(4))[0] # image height
        print "Planes: ", struct.unpack('<H', image.read(2))[0] # Planes (should be 1)
        print "Bits per pixel: ", struct.unpack('<H', image.read(2))[0] # bits per pixel color
        print "Compression: ", struct.unpack('<I', image.read(4))[0] # compression 
        print "Image Size: ", struct.unpack('<I', image.read(4))[0] # image size, should be 0 when no compression is used
        print "x pixels per meter: ", struct.unpack('<i', image.read(4))[0] # horizontal resolution, should be 0 for no preference
        print "y pixels per meter: ", struct.unpack('<i', image.read(4))[0] # vertical resolution
        print "Total Colors: ", struct.unpack('<I', image.read(4))[0] # Number of colors in the color pallet. If 0, 2^BitsPerPixel colors are used.
        print "Important Colors: ", struct.unpack('<I', image.read(4))[0]  # Generally ignored  
    else:
        header = image.read(54)
    data=image.read()
outfile = sys.argv[1].split('.')[0]+'.txt'
with open(outfile, 'wb') as textout:
    textout.write(data)
    print "Bytes written to {}".format(outfile)