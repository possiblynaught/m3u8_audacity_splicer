# M3U8 Audacity Splicer

Python automation for [Audacity](https://www.audacityteam.org/) or an Audacity fork (like [tenacity](https://tenacityaudio.org/))

This playlist audio splicer script takes a M3U8 playlist and a recording of the whole playlist and automatically splices the recording into seperate tracks using Audacity. It will then store the exported file locations of the spliced tracks to a new M3U8 playlist. All exported tracks are stored as 16-bit WAV audio files.

## USE

1) To prepare for use, download pipeclient module from audacity source code:
https://raw.githubusercontent.com/audacity/audacity/master/scripts/piped-work/pipeclient.py

2) Install slugify to create safe filenames from the track names and pytaglib to set metadata:

```bash
pip install python-slugify
pip install pytaglib
```  

3) Place the pipeclient module (pipeclient.py) and splice audio script (splice_audio.py) into the Audacity modules folder, you should make the directory if it doesn't exist yet:
- Linux: ~/.audacity-files/modules/
- Windows: the "modules" folder should be in the same location as audacity.exe
- Mac: the "modules" folder should be in the "Contents" folder.

4) Next, enable mod-script-pipe by going to the menu in Audactity:  
Edit -> Preferences -> Modules -> Select 'Ask' in drop down menu for mod-script-pipe

5) Now, reboot Audacity and select 'Yes' to start the mod-script-pipe. If you had any issues, you can find more info here: https://manual.audacityteam.org/man/scripting.html

6) Then, run the script from within the audacity modules folder with:

```bash
python3 splice_audio.py
```  

## INFO

This script will prompt user for the following input:
- A playlist file (.m3u/.m3u8)
- A recording of the whole playlist (.wav/.aiff/.flac/.mp3)
- Location to create the output folder for the new tracks + playlist
- During the run, it will prompt the user to edit the cursor position
  to where the previous song ends and the new song begins

## TODO

- [x] Make readme
- [ ] Use venv?
- [ ] Use python-slugify for file name guard?
- [ ] Finish audacity script
