<br/>
<p align="center">
  <h2 align="center">Throw / Catch</h2>
  <p align="center">
    Exfilling Data over an 'AirGap' (sort of)
    <br/>
    <br/>
  </p>
</p>

## Table Of Contents

* [Preamble](#preamble)


## Preamble

This project is old and unsupported. As is explained below, it was written a few years ago on a closed system with only Python 2.7 and notepad++ available. The quality of the code is not a representation of the author's current work. As such, this repo functions more as a project write-up than a code repository intended for distribution.

## Background

In 2019/2020, I attended a course which utilized virtual machines accessible through a web browser interface. These VMs were networked together in a private LAN and did not allow outbound connections. These VMs were Windows (XP?) with Python 2.7 and Notepad++, as well as generic Windows applications. By the end of the course, I had developed an extensive collection of notes that were stored on one of the VMs. After completing the course, the student VMs would be destroyed. The project in this repo was developed in an effort to recover the notes from the VM, through the web browser 'video' feed. Could I have contacted the course staff and asked them to get the notes for me? Maybe, but this was a fun way to spend a weekend.

## Initial Efforts
#### OCR
Yeah, I tried OCR, due to the image quality of the video and the nature of the notes (many symbols and precise syntax including whitespace) this approach as a failure. OCR dropped most of the whitespace and frequently missed or confused symbols.

#### Bitmap
My second approach was to write a script to generate a bitmap from the file contents. By reading the input file as a bytestream, converting every three bytes into a RGB hex color, and packing them into a bitmap, I could potentially screengrab the image on my local workstation and reverse the process to get my text. I looked up the file structure of a bitmap and wrote a quick Python script to generate a bitmap from arbitrary data, padded out to a square. Here's an example image made using the map.py script found in this repo, run against itself.

<img src="https://github.com/ChrisBuilds/throw/assets/57874186/e4427695-eed0-4959-87cd-edf3a476c2ab" alt="TTE" width="240" height="240">

Testing locally, this works as expected. However, when used from the VM, the video compression changes the color values and the original data is lost. Given video compression doesn't do well with high frequency data, my next approach was to lower the frequency. Rather than load all of the data into a single bitmap, I can load it in smaller sections into a bitmap with larger color squares. Now, I could modify the map.py script create a bunch of bitmaps and manually capture and process that image data locally, but that's not fun or cool, so I automated the process using PIL and tkinter. 

## Catch / Throw Concept
The methodology here is simple:
1. Read an input file into a bytestream.
2. Create a visual grid using a tkinter canvas.
3. Separate the input byte stream into three byte chunks.
4. Set the color in each visible grid cell to correspond to a three byte chunk from the bytestream. ASCII hex values would become RGB colors. The larger the grid, the more data represented in each cycle.
5. Cycle the grid to progress through the bytestream.
6. Run a second program to detect the visual grid using PIL, screenshot that area, split it into individual cells, and transcode the colors back to ASCII text.
7. Output the text to the terminal and to a file.

The first half of the program would be called 'Throw' and would run in the VM where it would have access to the input file. The second half of the program would be called 'Catch' and would run on my local workstation. By informing 'Catch' of the location of the grid, it could capture the color information and convert that data back into ASCII text. Given I would want to be able to vary the size of the grid to find the optimal transfer rate, I would need to find a way to automatically detect the grid and extrapolate where each color cell should be. 

To facilitate automatically detecting the grid, I used a unique fill color for the cells when the grid is in 'detecting mode'. I also used the color red to identify the left side of the grid, and green to identify the top of the grid. Catch will accept arguments specifying the number of cells in the grid and the width of a cell. With that information, along with a simple algorithm for finding the top left corner using the red/green border colors, the cells can be isolated within the screenshot. Here's how that looks:

![explaination_animation](https://github.com/ChrisBuilds/throw/assets/57874186/962d8259-2d62-43f4-b262-520906080d01)

## Final Product

Here's how it looks in action. Excuse the low quality, these are captures from an older video I made to explain the process. The example text is "Smashing The Stack For Fun And Profit". 

#### Throw - Displaying the data as a grid of colors
![grid](https://github.com/ChrisBuilds/throw/assets/57874186/80ab3771-aa07-42a4-ac10-65b7808fb9ed)

#### Catch - Capturing the output and displaying it in the terminal
![catch_output](https://github.com/ChrisBuilds/throw/assets/57874186/e3fc8192-ec86-49a5-8521-886977168e94)

## Extra Implementation Details
* The black screen shown between each grid of colors is actually an alternating 'blackish' color that is used to help syncronize the catch program. There are two different shades of black used. If catch sees the same shade twice, it knows it missed a cycle.
* Each cell in the grid was still experiencing compression artifacts. However, by examining every pixel in the cell, the most common color ended up being the correct color. Each cell often contained over 400 slight variations of the intended color.
* The data was hashed on both side to allow for comparisons.
* Any missed cycles (detected using the sync colors) was marked in the data and a note was provided in after the transfer to allow for manual review.
