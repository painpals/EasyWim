# Created by Ryan Rubash and Tyler Ziegler
# for flashing wim images into hard drives
# written for python 2.7
"""
1.0.0 = (2/22/2018) GUI and initial Alpha
1.0.1 = added fail checks, robocopy for desktopfiles
1.0.2 = (3/20/2018) added blacklist file, timestamp
1.0.3 = Separation of GUI Generation and Logic functions, added raise ValueError
        added checkbox to GUI for copying DesktopFiles, added textboxes for stdout with details
"""
version = "1.0.3"

from Tkinter import *
import tkFileDialog
import tkMessageBox
import subprocess, string, os, uuid, time, datetime


main = Tk()

# global vars
isWim = False
wimLocation = StringVar()
destLocation = StringVar()
driveList = []
dpartfilename = str(uuid.uuid4().hex) #this is the tempfile for diskpart, unique to each running script

#####################################################################
############################# GUI GENERATION
#####################################################################

def CurSelect(event):
    global destLocation
    widget = event.widget
    selection = widget.curselection()
    destLocation = widget.get(selection[0])

def sourceframe():
    # title
    titleLabel = main
    titleLabel.title("EasyWIM v" + version)

    # Source text on top
    fileMessageLabel = Label(main, text="Source:", anchor=NW, width=70)
    fileMessageLabel.grid(row=0)

    # entry box for file path
    source = Entry(main, width=80, textvariable=wimLocation)
    source.grid(row=1)

    # select source button here
    sourceButton = Button(main, width=20, text="Image Location...", command=callpath)
    sourceButton.grid(row=1, column=1)

def destinationframe():
    global destLocation
    # destination text here
    destinationMessageLabel = Label(main, text="Destination:", anchor=NW, width=70)
    destinationMessageLabel.grid(row=2)
    # list of destinations found
    destinationOptions = Listbox(main, width=80, selectmode=SINGLE)
    destinationOptions.bind('<<ListboxSelect>>', CurSelect)
    destinationOptions.grid(row=3)
    scandestination()
    for item in driveList:
        destinationOptions.insert(END, item + " Drive")
    destinationRefresh = Button(main, text="Refresh Drive List", width=20, command=destinationframe)
    destinationRefresh.grid(row=3, column=1)
    destLocation = destinationOptions.get(ACTIVE)

def optionframe():
    # start/cancel container
    optionContainer = Frame(main)
    optionContainer.grid(row=4, column=1)

    # insert start button
    startButton = Button(optionContainer, width=10, text="Start", command=startcopy)
    startButton.grid(row=0, column=0)

    # insert cancel button
    cancelButton = Button(optionContainer, width=10, text="Cancel", command=closescript)
    cancelButton.grid(row=0, column=1)

def checkbox():
    #checkbox for user to decided if they want the DesktopFiles copied or not. CHECKED by default.
    global checkDesktopFiles
    checkDesktopFiles = IntVar()
    checkDesktopFiles.set(1)
    Checkbutton(main, text="Copy DesktopFiles", variable=checkDesktopFiles).grid(row=4, column=0, sticky=W)    

#####################################################################
############################# GENERAL FUNCTIONS
#####################################################################
def abox(*args):
    masterlist = []
    mastertextlength = 0
    for argument in args:
        if type(argument) == list:
            if argument:
                currentlist = [str(element) for element in argument] #make usable list from list that is STR
                checklength = len(max(currentlist))
                if checklength >= mastertextlength: #check if this list has the longest string in it...
                    mastertextlength = checklength
                for element in currentlist:
                    masterlist.append(element)
        else:
            argument = str(argument)
            checklength = len(str(argument))
            if checklength >= mastertextlength:
                mastertextlength = checklength
            masterlist.append(argument)
    topbottom = " "
    for i in range(mastertextlength + 6):
        topbottom += chr(177)
    masterlist = list(filter(None, masterlist))
    if len(masterlist) > 0:
        print topbottom
        for element in masterlist:
            while len(element) < mastertextlength:
                element += " "
            print " " + chr(177) +  chr(177) + " " + element + " " + chr(177) + chr(177)
        print topbottom
#####################################################################
############################# TRIGGERS FROM BUTTON
#####################################################################

def callpath():
    global isWim
    global wimLocation
    wimLocation.set(tkFileDialog.askopenfilename(parent=main, initialdir="/", title='Select your .wim file'))
    # now checks path and will print error message if not a .wim file
    if str(wimLocation.get()).endswith(".wim"):
        isWim = True
    elif str(wimLocation.get()) is "":
        isWim = False
    else:
        isWim = False
        tkMessageBox.showerror(title="Warning", message="File selected is not a .wim file")

def scandestination():
    ## Blacklist Loading
    global BlackList
    BlackList = []
    os.system("color")
    os.system("cls")
    if os.path.exists("BlackList.txt"): #found blacklist make list
        with open("BlackList.txt") as f:
            content = f.readlines()
        BlackList = [x.strip() for x in content]
        abox("BLACKLIST FILE LOADED")
        for a in BlackList:
            print " - " + str(a)
    else:
        abox("NO BLACKLIST FILE FOUND")
        newBlackList = open("BlackList.txt", "w")
        newBlackList.close()
        print "BLANK BLACKLIST FILE CREATED"
    ## end of black list generation
    global driveList
    while len(driveList) > 0:
        driveList.pop()
    checkPhyDrives = subprocess.Popen("wmic diskdrive get index,model,serialnumber", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in checkPhyDrives.stdout.readlines():
        if "Index" in line:
            continue
        driveList.append(line.rstrip())
        driveList = filter(None, driveList)
    #Removing values that are blacklisted
    i = 0
    while True:
        for drive in driveList:
            for x in BlackList:
                if x.lower() in drive.lower():
                    driveList.remove(drive)
        i+=1
        if i == 300:
            break
    print "\nDrives found not a part of BlackList:"
    for a in driveList:
        print " - " + str(a)
    return driveList #this sends list to GUI

def startcopy(): #function when START BUTTON IS PRESSED
    starttime = datetime.datetime.now()
    global wimLocation
    global destLocation
    global isWim
    if isWim == True:
        os.system("color")
        #get drive selected...
        destDrive = destLocation.split(); destDrive = destDrive[0]
        #CLEAN DISK
        dpartfile = open(dpartfilename, "w")
        #clean selected disk
        dpartfile.write('select disk ' + str(destDrive))
        dpartfile.write('\nclean')
        dpartfile.close()
        #EXECUTE THE DISKPART TO CLEAN THE SELECTED DISK NUMBER
        abox("CLEANING DRIVE", destLocation)
        try:
            subprocess.check_call("diskpart /s " + dpartfilename)
        except subprocess.CalledProcessError:
            os.remove(dpartfilename)
            os.system("color 40")
            raise ValueError("ERROR: Failed to clean drive")
        os.remove(dpartfilename)
        #DEFINING ALPHABET OF UNUSED VOLUMES
        alphabet = []
        for i in string.ascii_uppercase:
            #alphabet.append(i + ':')
            alphabet.append(i)
        mounted_letters = subprocess.Popen("wmic logicaldisk get name", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in mounted_letters.stdout.readlines():
            if "Name" in line:
                continue
            for letter in alphabet:
                if letter in line:
                    #print 'Deleting letter %s from free alphabet ' + letter
                    alphabet.pop(alphabet.index(letter))
        #print alphabet
        del alphabet[0:2] #this is to ensure there are a couple free letters not in use
        if len(alphabet) < 3:
            os.system("color 40")
            raise ValueError("ERROR: There are not enough available volume letters.")
        partitionWindows = alphabet[0];
        del alphabet[0]
        partitionRecovery = alphabet[0]
        del alphabet[0]
        partitionHidden = alphabet[0]
        del alphabet[0]
        partitionWindows = partitionWindows[:1]
        partitionRecovery = partitionRecovery[:1]
        partitionHidden = partitionHidden[:1]
        #CREATE DRIVE PARTITONS
        dpartfile = open(dpartfilename, "w")
        dpartfile.write('select disk ' + str(destDrive))
        dpartfile.write('\nconvert gpt')
        dpartfile.write('\ncreate partition primary size=440')
        dpartfile.write('\nassign letter ' + partitionRecovery)
        dpartfile.write('\nformat quick fs=ntfs label="Windows RE tools"')
        dpartfile.write('\nset id="de94bba4-06d1-4d40-a16a-bfd50179d6ac"')
        dpartfile.write('\ngpt attributes=0x8000000000000001')
        dpartfile.write('\ncreate partition efi size 260')
        dpartfile.write('\nassign letter ' + partitionHidden)
        dpartfile.write('\nformat quick FS=FAT32')
        dpartfile.write('\ncreate partition msr size 128')
        dpartfile.write('\ncreate partition primary')
        dpartfile.write('\nformat quick FS=NTFS LABEL="WINDOWS"')
        dpartfile.write('\nassign letter ' + partitionWindows)
        dpartfile.close()
        #EXECUTE THE DISKPART TO CREATE PARTITIONS ON THE SELECTED DISK NUMBER
        abox("CREATING PARTITIONS",partitionRecovery + " - Recovery",partitionHidden + " - EFI",partitionWindows + " - Windows")
        try:
            subprocess.check_call("diskpart /s " + dpartfilename)
        except subprocess.CalledProcessError:
            os.remove(dpartfilename)
            os.system("color 40")
            raise ValueError("ERROR: Diskpart failed to make partitions.")
        os.remove(dpartfilename)
        #COPY UNATTEND FILE
        try:
            os.system("copy unattend.xml "+ partitionWindows + ":\\")
        except:
            os.system("color 40")
            raise ValueError("ERROR: Failed to copy unattend.xml file.")
        #APPLY IMAGE
        pathWim = wimLocation.get()
        pathWim = pathWim.replace("/","\\")
        wimFileName = pathWim.split("\\"); wimFileName = wimFileName[-1]; wimFileName = wimFileName.replace(".wim","") #gets just the filename used, without '.wim'
        abox("DEPLOYING WIM FILE",wimFileName)
        print str(pathWim)
        try:
            subprocess.check_call('dism /apply-image /imagefile:"' + pathWim + '" /index:1 /ApplyDir:' + partitionWindows + ':\\')
        except subprocess.CalledProcessError:
            os.system("color 40")
            raise ValueError("ERROR: DISM failed to write to volume.")
        #MAKE BOOTABLE
        try:
            subprocess.check_call("bcdboot.exe " + partitionWindows + ":\\windows /s " + partitionHidden + ":")
        except subprocess.CalledProcessError:
            os.system("color 40")
            raise ValueError("ERROR: BCDBoot failed.")
        #COPY DESKTOP FILES
        if checkDesktopFiles.get() == 1:
            if os.path.exists("DesktopFiles"):
                abox("COPYING DESKTOP FILES")
                try:
                    subprocess.check_call("robocopy DesktopFiles " + partitionWindows + ":\\Users\\Public\\Desktop /E")
                except subprocess.CalledProcessError:
                    print "WARNING- RoboCopy might have had a problem"
            else:
                print "There was no DestopFiles folder found in directory"
        else:
            print "User opted to not copy DesktopFiles"
        #CREATE FILE ON DESKTOP WITH IMAGE NAME
        file1 = open(partitionWindows + ":\\Users\\Public\\Desktop\\" + wimFileName + ".txt", "w")
        file1.close()
        # PROCESS COMPLETE
        os.system("color 20")
        #print "\n\nImage Process Is Complete"
        endtime = datetime.datetime.now()
        diftime = endtime - starttime
        diftime = divmod(diftime.days * 8600 + diftime.seconds, 60)
        #print "Run Time = " + str(diftime[0]) + " minutes and " + str(diftime[1]) + " seconds."
        abox("--IMAGE PROCESS COMPLETE--","Run Time = " + str(diftime[0]) + " minutes and " + str(diftime[1]) + " seconds.","WIM: " + str(wimFileName),"Drive: " + destLocation)
        time.sleep(5)
        pausing=raw_input("\nPress ENTER to EXIT")
        exit()
    else:
        tkMessageBox.showerror(title="Error", message="File selected is either not a .wim file, or no file was selected")

def closescript():
    exit()


#####################################################################
############################# EXECUTING CODE
#####################################################################
sourceframe()
destinationframe()
optionframe()
checkbox()

main.mainloop()
