<br/>
<p align="center">
  <h1 align="center">Throw / Catch</h1>
  <p align="center">
    Exfilling Data over an 'AirGap' (sort of)
    <br/>
    <br/>
  </p>
</p>

## Table Of Contents

* [Preamble](#preamble)
* [Background](#background)
* [Initial Efforts](#initial-efforts)
* [Final Product](#final-product)
* [Extras](#extra-implementation-details)


## Preamble

This project is old and unsupported. As is explained below, it was written a few years ago on a closed system with only Python 2.7 and notepad++ available. The quality of the code is not a representation of the author's current work. As such, this repo functions more as a project write-up than a code repository intended for distribution.

## Background

In 2019 I participated in an educational program that relied on virtual machines accessible through web browser interfaces. These virtual machines were networked within a private LAN, and they were intentionally configured to restrict outbound network connections. These VMs operated on Windows XP, equipped with Python 2.7 and Notepad++, alongside other standard Windows applications. Over the course of this program, I accumulated a substantial repository of notes and documentation, which were stored on one of these virtual machines. Upon completion of the course, student VMs were destroyed. The project presented within this repository is the result of my efforts to recover these notes from the virtual machine, utilizing an unconventional method involving the web browser's 'video' feed.

## Initial Efforts
#### OCR
The first approach was to employ OCR, however due to the image quality of the video and the nature of the notes (many symbols and precise syntax including whitespace) this approach was unsuccessful. OCR dropped most of the whitespace and frequently missed or confused symbols.

#### Bitmap
Another approach involved generating a bitmap representation from the contents of the file in question. This method treated the input file as a byte stream, with every triplet of bytes translated into a hexadecimal RGB color code. These color codes were then integrated to form a bitmap image. The intention behind this approach was to capture the generated image on my local workstation, allowing for the reversal of this process to retrieve the original text.

After some research on the structure of bitmap files, I wrote a Python script which could construct a bitmap image from arbitrary data. The script would create a square bitmap by adding padding when necessary.  An illustrative example of such an image, generated using the 'map.py' script contained within this repository, is included below. This demonstration involved running the script against its own source data.

```python2 map.py map.py```

<img src="https://github.com/ChrisBuilds/throw/assets/57874186/e4427695-eed0-4959-87cd-edf3a476c2ab" alt="TTE" width="240" height="240">

In the initial stages of testing on my local workstation, the procedure was successful. However, when attempting to execute the same process within the virtual machine, the introduction of video compression into the equation altered the color values, leading to a loss of fidelity in the original data. This issue was due to the inherent limitations of video compression algorithms, particularly their inability to effectively handle high-frequency data.

To address this challenge, I aimed at reducing the data's frequency. Instead of consolidating all the data into a single bitmap, I opted to partition it into smaller sections, each constituting a bitmap with larger color squares.

While it was possible to manually modify the 'map.py' script to create multiple bitmaps, subsequently capturing and processing these images locally, I automated this process using the Python Imaging Library (PIL) and tkinter.

## Catch / Throw Concept
The methodology here is simple:
1. Read an input file into a byte stream.
2. Separate the input byte stream into three byte chunks.
3. Create a visual grid using a tkinter canvas.
5. Set the color in each grid cell to correspond to a three byte chunk from the byte stream. ASCII hex values would become RGB colors. The larger the grid, the more data represented in each cycle.
6. Cycle the grid to progress through the byte stream.
7. Run a second program to detect the grid using PIL.
8. Screenshot that grid
9. Split it into individual cells
10. Transcode the colors back to ASCII text.

The program is divided into two distinct components: Throw and Catch. The Throw component operates within the virtual machine (VM), granting it access to the input file. Conversely, the Catch component is designed to run on my local workstation. The purpose of Catch is to receive information about the grid's location, enabling it to capture color data and subsequently perform the reverse transformation to recover the original ASCII text.

To allow for flexibility in adjusting the grid size to optimize data transfer rates, Catch is designed to detect and adapt to the grid's dimensions. This is accomplished by using a distinctive fill color for the cells during 'discovery mode.' Additionally, the color red is used to identify the left boundary of the grid, while the color green is used to identify the top boundary. By providing Catch the location of the top left cell (using the mouse cursor at the start of the process), along with the number of cells in a grid row, and the number of pixels in a cell, Catch will identify the extent of the grid and calculate the coordinates of all grid cells. Using these coordinates, Catch will screenshot the grid location on screen, split the image into individual cells, detect the color, and convert the color's hex representation back into ASCII text.

Here's a visual example:

![explaination_animation](https://github.com/ChrisBuilds/throw/assets/57874186/962d8259-2d62-43f4-b262-520906080d01)

## Final Product

Excuse the low quality, these are captures from an older video I made to explain the process.

#### Throw - Displaying the data as a grid of colors (9 cells per row, 60 pixels per cell)
```python2 throw_grid.py smashing.txt --grid 9 --square 60 --colortime 900 --synctime 500```

![grid](https://github.com/ChrisBuilds/throw/assets/57874186/80ab3771-aa07-42a4-ac10-65b7808fb9ed)

#### Catch - Capturing the output and displaying it in the terminal
```python2 catch_grid.py -o out.txt -g 9 -s 60```

![catch_output](https://github.com/ChrisBuilds/throw/assets/57874186/e3fc8192-ec86-49a5-8521-886977168e94)

## Extra Implementation Details
* The black screen shown between each grid of colors is actually two alternating shades of black that are used to help synchronize the catch program. If catch sees the same shade twice, it knows it missed a cycle. If Catch captures multiple frames without a syncronization frame, it treats those frames as representing the same data.
* Each cell in the grid was still experiencing compression artifacts. However, by examining every pixel in the cell, the most common color ended up being the correct color. Each cell often contained over 400 slight variations of the intended color.
* Catch takes screenshots as fast as the system will process. This allows it to take many captures of the same data. The synchronization colors mentioned above help prevent duplicate data. Additionally, video compression tends to produce a higher quality image when the data doesn't change between frames. Often the third or fourth frame of a given grid cycle will have the most accurate color representation. Catch will look at all frames between synchronization frames and average the colors to find the most likely correct color.
* The data is hashed on both side to allow for comparisons.
* Any missed cycles (detected using the sync colors) are marked in the data and a note is provided after the transfer to allow for manual review.
