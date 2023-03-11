#!/usr/bin/env python3

"""Audacity playlist audio splicer script

Takes a M3U8 playlist and a recording of the whole playlist and automatically
splices the recording into seperate tracks using Audacity. It will then store
the exported file locations of the spliced tracks to a new M3U8 playlist. All
exported tracks are stored as 16-bit WAV audio files.

1) To prepare for use, download pipeclient module from audacity source code:
https://raw.githubusercontent.com/audacity/audacity/master/scripts/piped-work/pipeclient.py

2) Install slugify to create safe filenames from the track names and pytaglib to set metadata:
pip install python-slugify
pip install pytaglib

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
# Import taglib for metadata access (with: pip install pytaglib)
import taglib
# Import slugify for filename linting (with: pip install python-slugify)
from slugify import slugify
# Import Audacity pipe client
import pipeclient

# Test for python 3
if sys.version_info[0] < 3:
    sys.exit("Error, Python 3 required")

class Song:
    """Store song data from/for a playlist file"""

    m3u_track_header="#EXTINF:"

    def __init__(self):
        self.artist = "No artist"
        self.file = "No file defined for track"
        self.number = 0
        self.runtime = 0
        self.track = "No track name"

    def set_track_name(self, track):
        """Set track name"""
        self.track = str(track)

    def set_artist_name(self, artist):
        """Set artist name"""
        self.artist = str(artist)

    def set_track_runtime(self, seconds):
        """Set song length in seconds"""
        self.runtime = int(seconds)

    def set_file_name(self, fil):
        """Set file path"""
        self.file = str(fil)

    def set_track_number(self, number):
        """Set track number"""
        self.number = int(number)

    def __repr__(self):
        """Print m3u/m3u8 entry lines for the song"""
        return self.m3u_track_header + str(self.runtime) + "," + self.artist + " - " + \
            self.track + "\n" + self.file + "\n"

def select_file():
    """Prompt a user to select a file and test file can be opened, return file path"""
    root = tkinter.Tk()
    root.withdraw()
    input_file = filedialog.askopenfilename()
    root.destroy()
    try:
        with open(input_file, encoding='utf-8') as temp:
            print("Selected playlist file: " + input_file)
            temp.close()
    except IOError:
        sys.exit("Error, unable to open file: " + input_file)
    return input_file

def select_directory():
    """Prompt a user to select a directory, return dir path"""
    root = tkinter.Tk()
    root.withdraw()
    top_directory = filedialog.askdirectory()
    root.destroy()
    if not os.path.exists(top_directory):
        sys.exit("Error, unable to open directory: " + top_directory)
    return top_directory

def create_directory(new_directory):
    """Creates a directory passed to function"""
    try:
        os.makedirs(new_directory)
    except OSError:
        sys.exit("Error, couldn't create directory: " + new_directory)

def is_m3u8(playlist_file, good_header):
    """Tests a file to see if it a valid .m3u/.m3u8 playlist, returns true/false"""
    # Check M3U8 file type
    m3u_extensions = [".m3u", ".m3u8"]
    if not playlist_file.endswith(tuple(m3u_extensions)):
        print("Error, playlist has wrong file extension: " + playlist_file)
        return False
    # Check M3U8 header
    with open(playlist_file, encoding='utf-8') as test_playlist:
        test_header = test_playlist.readline().strip('\n')
        if test_header == good_header:
            return True
        else:
            print("Error, playlist file doesn't have a M3U8 header (" + good_header + \
                "): " + playlist_file)
    return False

def get_string_runtime(seconds):
    """Return runtime passed in seconds as a minutes:seconds string such as: 4:03"""
    run_min = str(int(seconds / 60))
    run_seconds = int(seconds % 60)
    if run_seconds < 10:
        return run_min + ":0" + str(run_seconds)
    return run_min + ":" + str(run_seconds)

def main():
    """Start a splice run"""

    line_break = "-------------------------------------------------------------------------------\n"

    # Prompt user to select playlist file
    print(line_break + "Please select a playlist file (.m3u/.m3u8):")
    input_playlist_file = select_file()

    # Ensure user chose a valid playlist
    m3u_playlist_header = "#EXTM3U"
    if not is_m3u8(input_playlist_file, m3u_playlist_header):
        sys.exit("Error, playlist doesn't seem to be a valid .m3u/.m3u8 playlist: " + \
            input_playlist_file)

    # Ask user for a save directory
    print(line_break + "Please select the directory to save the output folder to:")
    root_dir = select_directory()

    # Generate a new output directory within the save directory with a timestamp
    output_directory_name = "audacity_spliced_" + datetime.now().strftime('%H_%M_%S')
    output_directory = os.path.join(root_dir, output_directory_name)
    create_directory(output_directory)

    # Start pipeclient and import comprehensive audio track
    audacity = pipeclient.PipeClient()
    audacity.write("Close:")
    time.sleep(1)
    audacity.write("ImportAudio:")
    input(line_break + "Please select the audio recording to import, hit Enter once loaded: ")

    # Read the input playlist into a list of Songs
    input_songs_list = []
    track_number = 0
    with open(input_playlist_file, encoding='utf-8') as input_playlist:
        line = input_playlist.readline()
        while line:
            temp_song = Song()
            # If song line, ingest data and append Song to list
            if line.startswith(temp_song.m3u_track_header):
                track_number += 1
                temp_song.set_track_runtime(re.search(':(.+?),', line).group(1))
                temp_song.set_artist_name(re.search(',(.+?) -', line).group(1))
                temp_song.set_track_name(re.search('- ([^\n]+)$', line).group(1))
                temp_song.set_track_number(track_number)
                input_songs_list.append(temp_song)
            # Read next line
            line = input_playlist.readline()

    # Export the songs in the list via Audacity hooks and add to new playlist
    print(line_break + "Starting playlist track export process...")
    # Read songs and edit Audacity waveforms
    for song in input_songs_list:
        # Set song length and zoom in on end
        audacity.write("Select: Start=0 End=" + str(song.runtime))
        audacity.write("ZoomSel:")
        # Zoom in
        for zoom in range(7):
            audacity.write("ZoomIn:")
        # Focus on end of selection
        audacity.write("SkipSelEnd:")
        # Prompt user to verify end point
        choice = input(line_break + str(song.number) + " - Click the end of the song (~" + \
            get_string_runtime(song.runtime) + \
                ") waveform, press Enter when done or 'q' to quit: ")
        # Test user response
        if choice == 'q':
            # Quit if 'q' passed
            break
        # Select the edited song and trim it
        audacity.write("SelPrevClipBoundaryToCursor:")
        audacity.write("Split:")
        # Create an output song filename, strip illegal chars
        temp_wav_name = slugify(song.track).replace(" ", "_") + ".wav"
        # Guard against newlines '\n' in filenames on Windows
        if temp_wav_name[0] == "n":
            temp_wav_name = "_" + temp_wav_name
        # Replace spaces with underscores and save the new name
        song.set_file_name(os.path.join(output_directory, temp_wav_name))
        # Export wav file and trim remaining
        audacity.write("Export2: Filename=" + song.file + " NumChannels=2")
        time.sleep(1)
        audacity.write("Delete:")
        audacity.write("Align_StartToZero:")

    # Check exported songs are present and set .wav file metadata + add to new playlist
    print(line_break + "Setting exported track metadata...")
    # Quick pause in case of ongoing track export
    time.sleep(2)
    # Prepare an error list for missing tracks
    error_songs_list = []
    # Open output playlist
    output_playlist_name = "__" + output_directory_name + "__playlist.m3u8"
    output_playlist_file = os.path.join(output_directory, output_playlist_name)
    with open(output_playlist_file, 'w', encoding='utf-8') as output_playlist:
        # Create playlist header
        output_playlist.write(m3u_playlist_header + "\n")
        for song in input_songs_list:
            # Test for .wav file
            if os.path.exists(song.file):
                # If file good, export track to playlist
                output_playlist.write(repr(song))
                # Set .wav file metadata
                temp_wav = taglib.File(song.file)
                temp_wav.tags["ARTIST"] = [song.artist]
                temp_wav.tags["TITLE"] = [song.track]
                temp_wav.save()
            else:
                error_songs_list.append(song)

    # Check for any errors and notify user + create playlist of errored tracks
    error_playlist_file = os.path.join(output_directory, "__export_error_tracks.m3u8")
    if error_songs_list:
        with open(error_playlist_file, 'w', encoding='utf-8') as error_playlist:
            # Create playlist header
            error_playlist.write(m3u_playlist_header + "\n")
            print(line_break)
            for song in error_songs_list:
                # If missing file, warn of error and add to error file
                print("Error exporting track " + str(song.number) + ": " + song.track)
                # Write track to error playlist
                error_playlist.write(repr(song))
            # Notify of error
            print(line_break + "All failed track exports have been saved to error playlist file:")
            print(error_playlist_file)
            
    # Notify of finish
    print(line_break + "Generated output playlist file:")
    print(output_playlist_file)

if __name__ == '__main__':
    main()
