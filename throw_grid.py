#coding=UTF-8
# Version 2.0
import Tkinter as tk
import sys
import hashlib
import binascii
import argparse

parser = argparse.ArgumentParser(description='Display bytes from input file as a grid of colors.')
parser.add_argument('in_file', type=str, help='Path/Name of file to send.')
parser.add_argument('-g','--grid', type=int, default=2, help='Grid size. Ex. 3 = 3x3 grid. Default=2')
parser.add_argument('-s', '--square', type=int, default=80, help='Square size. Ex. 60 = 60 pixels per square. Default=80')
parser.add_argument('-ct', '--colortime', type=int, default=900, help="Time in ms that color grid will display. Default=900")
parser.add_argument('-st', '--synctime', type=int, default=500, help='Time in ms that sync grid will display. Only applies if colortime > 600. Default=500')
cli_args = parser.parse_args()

start = False
manual = False # debugging
total_bytes = 0
bytes_sent = 0
base = cli_args.grid
in_file = cli_args.in_file
square_length = cli_args.square
color_time = cli_args.colortime
sync_color_time = cli_args.synctime
squares = []
splash = ''
splash_cleared = False

def change(delay, canvas, squares, hex_list, progress_label):
    global start
    global bytes_sent
    global splash
    global splash_cleared

    if not start:
        raw_input("Press Enter to start")
        start = True
    if len(hex_list) == 0:
        sys.exit()
    for square in squares:
        byte_block = hex_list.pop(0)
        if byte_block == "3f3f3f":
            progress_label.config(text="Status: PREAMBLE")
        elif byte_block == "262626":
            progress_label.config(text="Status: EOF")
        else: 
            pass
        bytes_sent += 3
        progress_label.config(text="Status: {} / {} Bytes Sent".format(bytes_sent, total_bytes))
        canvas.itemconfig(square, fill='#'+byte_block, outline='#'+byte_block)
        if not splash_cleared:
            canvas.itemconfig(splash,text='')
            splash_cleared = True
    if manual:   
        raw_input('enter')
    if byte_block == "161616" or byte_block == "171717":
        if delay > 600:
            delay = sync_color_time
    else:
            delay = color_time
    canvas.after(delay, lambda: change(delay, canvas, squares, hex_list, progress_label))

def main(argv=None):
    global squares
    global total_bytes
    global splash
    grid_h = grid_w = square_length*base # grid height/width
    
    root = tk.Tk()
    root.title('༼ つ ◕_◕ ༽つ               (╯°□°）╯︵ ┻━┻                   ༼ ༎ຶ ෴ ༎ຶ༽                ( •_•)O*¯`·.¸.·´¯`°Q(•_• )')
    canvas = tk.Canvas(root, bg="yellow", height=grid_h+2, width=grid_w+2, borderwidth=0, highlightthickness=0)
    progress_label_width = 10*base
    if progress_label_width > 100:
        progress_label_width = 100
    progress_label = tk.Label(root, text="Status: Showing Discovery", relief=tk.RIDGE, anchor=tk.W, width=progress_label_width)
    root.geometry('%dx%d+%d+%d' % (grid_w+6,grid_h+20,0,0)) #+20 for label
    # Create color squares
    x = 1
    y = 1
    while y < grid_h:
        while x < grid_w:
            new_square = canvas.create_rectangle(x,y,x+square_length,y+square_length, outline = "", fill="#111111")
            squares.append(new_square)
            x += square_length
        y += square_length
        x=1
    # create single pixel wide borders around canvas
    canvas.create_line(0,1,0,grid_h+1, width=1,fill="#FF0000") # left border
    canvas.create_line(0,grid_h+1,grid_w+2,grid_h+1, width=1,fill="#00FFFF") # bottom border
    canvas.create_line(0,0,grid_w+2,0,width=1,fill="#00FF00")# top border
    canvas.create_line(grid_w+1,1,grid_w+1,grid_h+1,fill="#0000FF") # right border
    # spash logo
    font_size = 2*base+2
    if font_size > 20:
        font_size = 20
    splash = canvas.create_text(grid_h/2,grid_w/2,fill="GREEN", text="________                 \n/_  __/ /  _______ _    __\n / / / _ \/ __/ _ \ |/|/ /\n/_/ /_//_/_/  \___/__,__/ ", font=('Courier New', font_size),justify=tk.CENTER)
    canvas.grid(row=0, column=0,)
    progress_label.grid(row=1, column=0)
    # read in data and convert to hex
    with open(in_file,'rb') as f:
        raw_data = f.read()
        hash = hashlib.md5(raw_data).hexdigest()
        data = binascii.hexlify(raw_data).upper()
    # bbl is the byte capacity of the grid
    bbl = 3*(base**2) # byte block length
    # insert sync codes, alternating, every bbl
    sync_code_a = '16'*bbl
    sync_code_b = '17'*bbl
    sca_gap = 4*bbl # distance between sync code a
    scb_gap = 6*bbl # distance between sync code b
    s = sync_code_a.join(data[i:i+sca_gap] for i in range(0, len(data), sca_gap))
    s = s[0:bbl*2]+ sync_code_b +(sync_code_b.join(s[i:i+scb_gap] for i in range(2*bbl, len(s), scb_gap)))
    # determine last sync code used
    last_sync_eval = {sync_code_a:s.rfind(sync_code_a),
                      sync_code_b:s.rfind(sync_code_b)}
    # insert sync code for last byte
    sync_last_byte = [sync_code for sync_code, count in last_sync_eval.items() if count == min(last_sync_eval.values())]
    # ensure data ends on a bbl length boundary
    s = s + '26' * (((bbl*2)-(len(s) % (bbl*2)))/2)    
    s = s + sync_last_byte[0]*2 
    # add preamble and EOF code   
    s = ('3f'*bbl*2)+s+('26'*bbl*2)
    # separate data into three byte pieces
    s_list = [s[i:i+6] for i in range(0, len(s), 6)]
    total_bytes = len(s_list) *3
    # calculate time estimate
    if color_time > 600:
        sync_time = sync_color_time
    else:
        sync_time = color_time
    sync_code_count = s_list.count('161616') + s_list.count('171717')
    seconds_estimate = int(round((sync_code_count/(base**2))*(sync_time/1000.0)))
    seconds_estimate = int(round(((len(s_list)-sync_code_count)/(base**2))*(color_time/1000.0)))
    seconds_estimate = int(round(seconds_estimate+(.27*seconds_estimate)))
    minutes = seconds_estimate/60
    seconds = seconds_estimate % 60
    # calculate speed estimate
    data_rate_a = (3*(base**2)*8*(1000.0/color_time))
    data_rate_b = (3*(base**2)*8*(1000.0/sync_time))
    print "--------------------"
    print "MD5: {}".format(hash)
    print "Estimated Transfer Time: {} Minutes {} Seconds".format(minutes,seconds)
    print "Data Rate: {} bits per second".format(((data_rate_a+data_rate_b)/2))
    change(color_time, canvas, squares, s_list,progress_label)
    root.mainloop()
    return 0
main()