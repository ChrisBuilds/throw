import binascii
import struct
import sys
import math

# Read in text
with open(sys.argv[1],'rb') as f:
    data = f.read()
    data_length = len(data)
    # If the number of data bytes isn't divisible by 3, add extra
    # 255 values as padding to complete the last pixel
    pixel_diff = []
    missing_channels = 3 - (data_length % 3)
    if missing_channels != 3:
        pixel_diff = [255] * missing_channels
    # Find a square image with enough pixels for the data.
    # Find the square root (rounded up) of the number of bytes
    # in the data, divided by 3 (24 bits per pixel), rounded up
    pixel_length = int(math.ceil(((data_length/3.0)+len(pixel_diff))**0.5))
    # Bitmap scanlines should have a byte count that falls on a 4 byte boundary
    # Check the length to ensure this is the case
    pixel_length = pixel_length + (4 - (pixel_length % 4))
    # Fill the remaining pixels with r:255,g:255,b:255 (white)
    padding = [255] * (((pixel_length**2)-((data_length+len(pixel_diff))/3))*3)
    # Start building image data bytes
    image_data = b''
    # Header
    # Signature
    image_data+= bytearray(b'\x42\x4d')
    # File Size (header + number of pixels * 3)
    size = 54+((pixel_length**2)*3)
    image_data+= struct.pack('<I', size)
    # Reserved
    image_data+= struct.pack('<I', 0)
    # Pixel data offset
    image_data+= struct.pack('<I', 54)
    # DIB Header
    # Header Size
    image_data+= struct.pack('<I', 40)
    # Image Width
    image_data+= struct.pack('<i', pixel_length)
    # Image Height
    image_data+= struct.pack('<i', pixel_length)
    # Planes
    image_data+= struct.pack('<H', 0)
    # Bits per pixel
    image_data+= struct.pack('<H', 24)
    # Compression
    image_data+= struct.pack('<I', 0)
    # Image Size
    image_data+= struct.pack('<I', 0)
    # x pixels per meter
    image_data+= struct.pack('<i', 0)
    # y pixels per meter
    image_data+= struct.pack('<i', 0)
    # Total Colors
    image_data+= struct.pack('<I', 0)
    # Important Colors
    image_data+= struct.pack('<I', 0)
    # Add pixel data
    image_data+=data
    image_data+=bytearray(pixel_diff)
    image_data+=bytearray(padding)
with open(sys.argv[1].split('.')[0]+'.bmp', 'wb') as image:
    image.write(image_data)
            
            
            
