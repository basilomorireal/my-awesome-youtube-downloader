<p align="center">
  <img src="assets/images/title.gif" alt="title gif">
</p>

<h1 align="center">My Awesome YouTube Downloader</h1>

a simple youtube downloader made with python, tkinter, yt-dlp, and ffmpeg.

i made this because dad doesnt really know how to use yt-dlp so i made it very simple for him

it can download single videos, multiple videos at once, or entire playlists. it also has light/dark mode, animated buttons, optional background music, and a cat because im fucking awesome.

## safety warning
if you dont trust the release file that i uploaded, you can always build the program by yourself. everything is open sourced.

i will not be including any contributors to this project so if you see a potential clone of this with my name and someone elses on the contributor list, that is not legit.

## features

- download single videos
- download multiple videos (bulk mode)
- download entire playlists
- video-only downloads
- audio-only (mp3) downloads
- audio + video downloads (merged)
- multiple file formats
- selectable quality options
- custom download folder
- light / dark mode
- animated gif buttons
- background music because i grew up with keygens

## planned features

- nothing i think

## requirements

- python 3.8+
- yt-dlp
- ffmpeg
- pyinstaller (included. build.bat downloads it for you)
- pycaw (included. build.bat downloads it for you)
- comtypes (included. build.bat downloads it for you)
- pillow (included. build.bat downloads it for you)
- tkinter (comes with python)

im unable to upload both yt-dlp and ffmpeg for safety reasons (plus ffmpeg is huge so just download it by yourself and put it in the bin folder)
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- ffmpeg: https://ffmpeg.org/download.html#build-windows (download the exe files and not the source code)

## building exe

run  
build.bat  

output  
dist\YT Downloader.exe  

## project structure

My Awesome YouTube Downloader/

├── build.bat                  <- build script  
├── src/  
│   └── yt_downloader.py       <- main app source code  
├── assets/  
│   ├── icons/  
│   │   ├── icon.png  
│   │   └── icon.ico  
│   ├── images/  
│   │   ├── title.gif  
│   │   ├── cat.png  
│   │   ├── download.gif  
│   │   ├── download2.gif  
│   │   └── download3.gif  
│   └── audio/  
│       └── theme.mp3  
├── bin/  
│   ├── yt-dlp.exe  
│   ├── ffmpeg.exe  
│   └── ffplay.exe  
└── dist/  
    └── YT Downloader.exe  

## notes

- video mode downloads video only (no audio)  
- audio mode converts to mp3  
- audio + video mode downloads and merges both streams

## disclaimer

this project is for educational and personal use only pls dont steal ty :3 
