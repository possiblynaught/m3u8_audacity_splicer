#!/usr/bin/env python3

"""Audacity playlist audio splicer script

Takes a M3U8 playlist and a recording of the whole playlist and automatically
splices the recording into seperate tracks using Audacity. It will then store
the exported file locations of the spliced tracks to a new M3U8 playlist. All
exported tracks are stored as 16-bit WAV audio files.

1) To prepare for use, download pipeclient module from audacity source code:
https://raw.githubusercontent.com/audacity/audacity/master/scripts/piped-work/pipeclient.py

2) Install slugify to create safe filenames from the track names
pip install python-slugify

3) Place the pipeclient module (pipeclient.py) and splice audio script (splice_audio.py) into
the Audacity modules folder, you should make the directory if it doesn't exist yet:
- Linux: ~/.audacity-files/modules/
- Windows: the "modules" folder should be in the same location as audacity.exe
- Mac: the "modules" folder should be in the "Contents" folder.

4) Next, enable mod-script-pipe by going to the menu in Audactity:
Edit -> Preferences -> Modules -> Select 'Ask' in drop down menu for mod-script-pipe

5) Now, reboot Audacity and select 'Yes' to start the mod-script-pipe. If you had any 
issues, you can find more info here: https://manual.audacityteam.org/man/scripting.html

6) Then, run the script from within the audacity modules folder with:
python3 splice_audio.py

Prompts user for the following input:
- A playlist file (.m3u/.m3u8)
- A recording of the whole playlist (.wav/.aiff/.flac/.mp3)
- Location to create the output folder for the new tracks + playlist
- During the run, it will prompt the user to edit the cursor position
  to where the previous song ends and the new song begins

"""

# Imports
import os
import re
import sys
import time
from datetime import datetime
# Import tkinter for file selection
import tkinter
from tkinter import filedialog
# Import slugify for filename linting
# (requires you to have run: pip install python-slugify)
from slugify import slugify
# Import Audacity pipe client
import pipeclient

# Test for python 3
if sys.version_info[0] < 3:
    sys.exit("Error, Python 3 required")

class Song:
    """Store song data from/for a playlist file"""

    def __init__(self):
        self.track = None
        self.artist = None
        self.runtime = None
        self.file = None
        self.number = 0

    def set_track(self, track):
        """Set track name"""
        self.track = track

    def set_artist(self, artist):
        """Set artist name"""
        self.artist = artist

    def set_runtime(self, seconds):
        """Set song length (seconds)"""
        self.runtime = seconds

    def set_file(self, fil):
        """Set file path"""
        self.file = fil

    def set_number(self, number):
        """Set track number"""
        self.number = number

    def get_track(self):
        """Get track name"""
        return self.track

    def get_artist(self):
        """Get artist name"""
        return self.artist

    def get_runtime(self):
        """Get song length (seconds)"""
        return self.runtime

    def get_file(self):
        """Get file path"""
        return self.file

    def get_number(self):
        """Get track number"""
        return self.number

def get_filename():
    """Prompt a user to select a file and test file can be opened, return file path"""
    root = tkinter.Tk()
    root.withdraw()
    input_file = filedialog.askopenfilename()
    try:
        with open(input_file, encoding='utf-8')  as test:
            print("Selected playlist file: " + input_file)
        test.close()
    except IOError:
        sys.exit("Error, unable to open file: " + input_file)
    root.destroy()
    return input_file

def main():
    """Start a splice run"""

    # For print use in future
    newline = "-------------------------------------------------------------------------------\n"

    # Prompt user to select playlist file
    print(newline + "Please select a playlist file (.m3u/.m3u8):")
    input_playlist_file = get_filename()

    # Check file type
    playlist_ext = [".m3u", ".m3u8"]
    if not input_playlist_file.endswith(tuple(playlist_ext)):
        sys.exit("Error, playlist doesn't appear to be a M3U8 file: " + input_playlist_file)

    # Check M3U8 header
    expected_header="#EXTM3U"
    with open(input_playlist_file, encoding='utf-8') as input_playlist:
        test_header = input_playlist.readline().strip('\n')
    if test_header != expected_header:
        sys.exit("Error, playlist doesn't have a M3U8 header: " + input_playlist_file)

    # Ask user for a save directory
    print(newline + "Please select the directory where the output folder will be generated:")
    root = tkinter.Tk()
    root.withdraw()
    top_directory = filedialog.askdirectory()
    root.destroy()

    # Create output dir
    print(top_directory)
    timestamp = "spliced_" + datetime.now().strftime('%H_%M_%S')
    output_directory = os.path.join(top_directory, timestamp)
    try:
        os.makedirs(output_directory)
    except OSError:
        sys.exit("Error, couldn't create output directory: " + output_directory)
    print("Selected output directory: " + output_directory)

    # Start pipeclient and import comprehensive audio track
    audacity = pipeclient.PipeClient()
    audacity.write("Close:")
    time.sleep(1)
    audacity.write("ImportAudio:")
    input(newline + "Please select the audio recording to import, hit Enter once loaded: ")
    # Loop per line in playlist file
    track_header="#EXTINF:"
    songs = []
    with open(input_playlist_file, encoding='utf-8') as input_playlist:
        line = input_playlist.readline()
        num = 0
        while line:
            if line.startswith(track_header):
                # Create song metadata and get runtime in seconds, track name, artist
                songs.append(Song())
                songs[num].set_runtime(re.search(':(.+?),', line).group(1))
                songs[num].set_artist(re.search(',(.+?) -', line).group(1))
                songs[num].set_track(re.search('- ([^\n]+)$', line).group(1))
                songs[num].set_number(num + 1)
                # Iterate num
                num += 1
            line = input_playlist.readline()

    # Export songs + playlist data to output dir
    error_songs = []
    output_playlist_file = os.path.join(output_directory, "playlist.m3u8")
    with open(output_playlist_file, 'w', encoding='utf-8') as output_playlist:
        # Create header
        output_playlist.write(expected_header + "\n")
        # Read songs and edit Audacity waveforms
        for song in songs:
            # Set song length and zoom in on end
            audacity.write("Select: Start=0 End=" + song.get_runtime())
            audacity.write("ZoomSel:")
            # Zoom in on end of selection
            for z in range(7):
                audacity.write("ZoomIn:")
            audacity.write("SkipSelEnd:")
            # Get expected song length in min and seconds
            len_min = str(int(int(song.get_runtime()) / 60))
            len_sec = int(int(song.get_runtime()) % 60)
            if len_sec < 10:
                len_sec = "0" + str(len_sec)
            else:
                len_sec = str(len_sec)
            # Prompt user to verify end point
            choice = input(newline + "Edit the end of the song (~" + len_min + ":" + \
                len_sec + ") with the cursor, press Enter when done or 'q' to quit: ")
            # Quit if 'q' passed
            if choice == 'q':
                break
            audacity.write("SelPrevClipBoundaryToCursor:")
            audacity.write("Split:")
            # Create an output filename and export the track, strip illegal chars
            wavname = slugify(song.get_track()).replace("\n", "/n").replace("\r", "/r")
            wavname = wavname + ".wav"
            # Guard against newline \n in filenames on Windows
            if wavname[0] = 'n':
                wavname = "_" + wavname
            # Replace spaces with underscores
            song.set_file(os.path.join(output_directory, wavname).replace(" ", "_"))
            # Export file and trim remaining
            audacity.write("Export2: Filename=" + song.get_file())
            audacity.write("Delete:")
            audacity.write("Align_StartToZero:")
            # Check for output file
            if os.path.exists(song.get_file()):
                # Export song metadata to playlist file
                output_playlist.write(track_header + song.get_runtime() + "," + \
                    song.get_artist() + " - " + song.get_track() + "\n" + song.get_file() + "\n")
            else:
                # If missing file, add to error list
                error_songs.append(song)

    # Check for errors
    if len(error_songs) > 0:
        # Warn of errors and create error playlist of tracks that failed export
        error_playlist_file = os.path.join(output_directory, "failed_export_songs.m3u8")
        with open(error_playlist_file, 'w', encoding='utf-8') as error_playlist:
            # Create header
            error_playlist.write(expected_header + "\n")
            for song in error_songs:
                # Export song metadata to playlist file
                error_playlist.write(track_header + song.get_runtime() + "," + \
                    song.get_artist() + " - " + song.get_track() + "\n" + song.get_file() + "\n")
                # Also print error msg
                print("Error exporting track " + song.get_number() + ": " + song.get_track())
            # Notify of error present
            print(newline + "All failed track exports have been saved to playlist file: " \
                + output_playlist_file)

    # Notify of finish
    print(newline + "Generated playlist file: " + output_playlist_file)

    # TODO: Close pipe?
    # TODO: Finish readme

if __name__ == '__main__':
    main()
