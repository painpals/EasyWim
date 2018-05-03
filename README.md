# EasyWim

Current Status: 1.0.4 Released


Built by Ryan Rubash and Tyler Ziegler 

EasyWim is an open source program written in Python 2.7 that can flash wim files to any drive attached, while being in OS.
Simply Select the file location, the destination drive you want to flash to, and press start.


Currently supports Windows 7,8, and 10

1.0.0 = (2/22/2018) GUI and initial Alpha
1.0.1 = added fail checks, robocopy for desktopfiles
1.0.2 = (3/20/2018) added blacklist file, timestamp
1.0.3 = Separation of GUI Generation and Logic functions, added raise ValueError
        added checkbox to GUI for copying DesktopFiles, added textboxes for stdout with details
1.0.4 = Rewritten GUI to have more specific variables, added tab for wim capture (not functional)
        added error_stop function, added drive to title when running
