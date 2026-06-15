<p align="center">
  <img src="assets/images/title.gif" alt="title gif">
</p>

<h1 align="center">My Awesome YouTube Downloader</h1>

a simple youtube downloader made with python, tkinter, yt-dlp, and ffmpeg.

i made this because dad doesnt really know how to use yt-dlp so i made it very simple for him

it can download single videos, multiple videos at once, or entire playlists. it also has light/dark mode, animated buttons, optional background music, and a cat because im fucking awesome.

## features

- download single videos
- download multiple videos (bulk mode)
- download entire playlists
- video-only downloads
- audio-only (mp3) downloads
- audio + video downloads (merged)
- selectable quality options
- custom download folder
- light / dark mode
- animated gif buttons
- background music because i grew up with keygens

## planned features

- multiple file types for audio and video (ogg, flac, wav, mov, mkv, webm)
- more awesome features and ui changes because fuck yeah

## requirements

- python 3.8+
- yt-dlp
- ffmpeg
- pillow (included. build.bat downloads it for you)
- tkinter (comes with python)

im unable to upload both yt-dlp and ffmpeg for safety reasons (plus ffmpeg is huge so just download it by yourself and put it in the bin folder)
yt-dlp: https://github.com/yt-dlp/yt-dlp
ffmpeg: https://ffmpeg.org/download.html#build-windows (download the exe files and not the source code)

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
- optional gifs and music are not required  

## disclaimer

this project is for educational and personal use only pls dont steal ty :3 
