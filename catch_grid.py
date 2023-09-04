# Version: 2.0

from PIL import ImageGrab
import binascii
import time
import sys
from timeit import default_timer as timer
import hashlib
import Tkinter
import string
import pyautogui
import argparse

parser = argparse.ArgumentParser(description='Receive bytes as a grid of colors from throw.py')
parser.add_argument('-o', '--out_file', required=True, type=str, help='Path/Name of output file for bytes.')
parser.add_argument('-g', type=int, default=2, help='Grid size. Ex. 3 = 3x3 grid. Default=2')
parser.add_argument('-s', type=int, default=80, help='Square size. Ex. 60 = 60 pixels per square. Default=80')
cli_args = parser.parse_args()

# The following codes correspond the ASCII characters that
#  are deprecated or not commonly found in text files
base = cli_args.g
square_length = cli_args.s
out_file = cli_args.out_file
bbl = (base**2)*3 # byte block length
discover_code = '11'*bbl
preamble_code = '3F'*bbl
sync_code_a = '16'*bbl
sync_code_b = '17'*bbl
eof_code = '26'*bbl

last_chars = sync_code_a
received_string = ''
pos_x, pos_y = 0,0
img_count = 0
dup = 0
unsynced = 0
unsynced_chars=[]
bad_capture_chars = []
last_sync = ''
skipped_blocks = 0
batch = {}
# Establish a list of printable characters for comparison later
ascii_printable = range(32,127)
ascii_printable.extend(range(9,16))
ascii_printable_hex = map(lambda x: hex(x)[2:].upper().zfill(2), ascii_printable)
capturing = True
bad_captures = 0 # This is count of the images from which too many colors were found
bad_char_contexts = [] # This is the context in which non-printable characters were found
bad_char_count = 0

def get_color_boxes():
    """Locate the throw.py window and find the boundaries for each internal color box"""
    pos_x = 50
    pos_y = 0
    left_boundary = 0
    top_boundary = 0
    right_boundary = 0
    bottom_boundary = 0
    screenshot = ImageGrab.grab()
    s_width, s_height = screenshot.size
    # Scan for a 50x50 region of the screen with
    #  (17,17,17) as the most common color value
    while pos_x <= s_width:
        while pos_y <= s_height:
            test_square = screenshot.crop(box=(pos_x,pos_y,pos_x+50,pos_y+50))
            colors = test_square.getcolors()
            if colors and colors[0][1] == (17,17,17):
                print "Found discovery code"
                print "Finding left boundary"
                pixel_color = screenshot.getpixel((pos_x,pos_y))
                while pos_x > 0:
                    pos_x -= 1
                    pixel_color = screenshot.getpixel((pos_x,pos_y))
                    # Move left until the color changes, indicating the border
                    if pixel_color[0] >= 200:
                        left_boundary = pos_x + 1
                        break
                    # If the edge of the screen is hit, the original
                    #  origin may have been outside the box, jump 50
                    #  pixels in and keep looking
                    if pos_x == 0:
                        pos_x += 50
                # Look for the top border 
                print "Finding top boundary"
                pos_x += 50   
                while pos_y > 0:
                    pos_y -= 1
                    pixel_color = screenshot.getpixel((pos_x,pos_y))
                    if pixel_color[1] >= 230:
                        top_boundary = pos_y + 1
                        break
                pos_y += 50
                # Find right boundary
                print "Finding right boundary"
                while pos_x < s_width:
                    pos_x += 1
                    pixel_color = screenshot.getpixel((pos_x,pos_y))
                    if pixel_color[2] >= 200:
                        right_boundary = pos_x - 1
                        break
                pos_x -= 50
                # Find bottom boundary
                print "Finding bottom boundary"
                while pos_y < s_height:
                    pos_y += 1
                    pixel_color = screenshot.getpixel((pos_x,pos_y))
                    if pixel_color[1] >= 190 and pixel_color[2] >= 190:
                        bottom_boundary = pos_y - 1
                        break
                # Return the boundary box for the full color area
                return (left_boundary,top_boundary,right_boundary+1,bottom_boundary+1)                    
            pos_y += 50
        pos_x += 50
        pos_y = 0
    print "Color Box NOT Found."
    sys.exit()

def get_hex(color_box):
    """Find all color values in a given boundary. Return the most common color."""
    colors = color_box.getcolors(maxcolors=square_length**2)
    #print colors
    if colors:
        if len(colors) > 1: 
            colors.sort(key=lambda x:x[0], reverse=True)
        color = colors[0][1]
        #print color
        h,m,l=color
        hex_color = "{}{}{}".format("{0:0{1}X}".format(h,2),"{0:0{1}X}".format(m,2),"{0:0{1}X}".format(l,2))
        return hex_color
    else:
        color_box.show()   
        return False

def grab_to_hex():
    """Crop each color box and pass to get_hex(), then return most common color."""
    data_box_image = ImageGrab.grab(bbox=data_box)
    data_box_width, data_box_height = data_box_image.size
    # debugging
    #data_box_image.show()
    hex_bytes = []
    x = y = 0
    while y <= data_box_height-square_length:
        while x <= data_box_width-square_length:
            box = data_box_image.crop(box=(x,y,x+(data_box_width/base),y+(data_box_height/base)))
            hex_bytes.append(get_hex(box))
            x += data_box_width/base
        y += (data_box_height/base)
        x=0
    return hex_bytes

def capture_data():
    """Turn hex color values from throw.py into bytes and output to file."""
    global last_chars
    global received_string
    global capturing
    global bad_char_contexts
    global bad_captures
    global bad_capture_chars
    global img_count
    global dup
    global unsynced
    global unsynced_chars
    global last_sync
    global skipped_blocks
    global batch
    global bad_char_count
    block_fail = False
    hex_bytes = grab_to_hex()
    for block in hex_bytes:
        if not block:
            block_fail = True
    # One of these may be False if too many colors were detected in one block
    # this can happen due to compression/refresh issues over the VM
    if not block_fail:
        new_chars = ''.join(block for block in hex_bytes)
        # If a .txt file is being copied, remove non-printable characters
        #  which likely resulted from a bad color value detection the
        #  context will be recorded and displayed in the console at
        #  the end of the task
        if new_chars not in (discover_code, eof_code, preamble_code, sync_code_a, sync_code_b):
            bad_char_context_added = False
            clean_chars = ''
            if '.txt' in out_file:
                for i in range(0,len(new_chars),2):
                    if new_chars[i]+new_chars[i+1] not in ascii_printable_hex:
                        if not bad_char_context_added:
                            if new_chars not in bad_char_contexts:
                                bad_char_contexts.append(new_chars)
                                bad_char_context_added = True
                                bad_char_count += 1
                    else:
                        clean_chars += new_chars[i]+new_chars[i+1]
                new_chars = clean_chars
    else:
        new_chars = False
        # replace False bool with ASCII <<unk>>
        incomplete_string = ''
        for block in hex_bytes:
            if not block:
                incomplete_string += '3c3c756e6b3e3e'
            else:
                incomplete_string += block
        bad_captures += 1
        bad_capture_chars.append(incomplete_string)
        img_count += 1
    if new_chars:
        if new_chars == discover_code:
            pass
            img_count+=1
        elif new_chars == eof_code:
            capturing = False
            img_count +=1
        elif new_chars == preamble_code:
            sys.stdout.write('.')
            img_count +=1
        # This is the ideal condition in which data is accepted
        elif last_chars in (sync_code_a,sync_code_b) and new_chars not in (sync_code_a,sync_code_b):
            if new_chars not in batch.keys():
                batch[new_chars] = 1
            else:
                batch[new_chars] = batch[new_chars]+1
            img_count += 1
            #print new_char, colors
            last_chars = new_chars
            
        # This is the ideal condition after data has been accepted                   
        elif last_chars not in (sync_code_a,sync_code_b) and new_chars in (sync_code_a,sync_code_b) and new_chars != last_sync:
            last_chars = new_chars
            last_sync = new_chars
            img_count+=1
            most_received = [k for k, v in batch.items() if v == max(batch.values())]
            accepted_string = ''
            #print batch
            if len(most_received) > 1:
                accepted_string += max(most_received, key = len)
            else:
                accepted_string += most_received[0]
            received_string += accepted_string
            batch = {}
            if '.txt' in out_file:
                sys.stdout.write(accepted_string.decode("hex"))
                pass
            elif '.py' in out_file:
                sys.stdout.write(accepted_string.decode("hex"))
            else:
                sys.stdout.write(accepted_string)
        # The current image data matches the previous
        elif last_chars not in (sync_code_a,sync_code_b) and new_chars == last_chars:
            dup += 1
            img_count+=1
            batch[new_chars] = batch[new_chars] + 1
        # New data is found but the sync code was not seen
        # last_chars is updated but the data is not written
        # as this is not ideal
        elif last_chars not in (sync_code_a,sync_code_b) and new_chars not in (sync_code_a,sync_code_b):
            last_chars = new_chars
            img_count+=1
            #unsynced+=1
            #unsynced_chars.append((new_chars,new_chars.decode('hex')))
            if new_chars not in batch.keys():
                batch[new_chars] = 1
            else:
                batch[new_chars] = batch[new_chars]+1
        elif last_chars in (sync_code_a,sync_code_b) and new_chars in (sync_code_a,sync_code_b) and last_chars != new_chars:
            skipped_blocks += 1
        else:
            dup += 1
            
    else:
        return

print "Locating color boxes...",
data_box = get_color_boxes()
print "done."
print "DataBox:", data_box
sys.stdout.write("PREAMBLE")
start = timer()
while capturing:
    capture_data()

with open(out_file,'wb') as notes:
    data = bytearray.fromhex(received_string.rstrip('26'))
    notes.write(data)

print "\n---------------"
print "Data written to {}".format(out_file)
print "\nMD5: {}".format(hashlib.md5(data).hexdigest())
end = timer()
seconds_elapsed = int(round(end - start))
minutes = seconds_elapsed / 60
seconds = seconds_elapsed % 60
print "Time Elapsed: {} minutes {} seconds".format(minutes, seconds)
if bad_captures:
    print "Bad Captures: {}".format(bad_captures)
if bad_char_contexts:
    print "Non-Printable Character Contexts"
    for i in bad_char_contexts:
        print "{}  :  {}".format(i,i.decode("hex"))
print "bad character count: ",bad_char_count
print "image count: ",img_count
print "dup: ",dup
print "unsynced: ",unsynced
print "unsynced chars: ",unsynced_chars
print "skipped blocks: ",skipped_blocks