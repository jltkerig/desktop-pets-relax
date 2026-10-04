#!/bin/sh
# Builds "Pixel Fox.exe" in the app's folder. Needs Pillow and the MinGW-w64 cross compiler
# (on Ubuntu/Debian: apt install gcc-mingw-w64-x86-64 binutils-mingw-w64-x86-64).
set -e
cd "$(dirname "$0")"
python3 make_icon.py
x86_64-w64-mingw32-windres launcher.rc -O coff -o launcher.res
x86_64-w64-mingw32-gcc -municode -mwindows -Os -s -Wall -o "../Pixel Fox.exe" launcher.c launcher.res
rm -f launcher.res
echo "Built ../Pixel Fox.exe"
