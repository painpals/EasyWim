# Created by Ryan Rubash and Tyler Ziegler
# EasyWIM 1.0 2/22/2018
# for flashing wim images into hard drives
# written for python 2.7

#1.0 = GUI and initial Alpha
#1.1 = added fail checks, robocopy for desktopfiles

from Tkinter import *
import ttk
import tkFileDialog
import tkMessageBox
import ScrolledText
import threading
import subprocess, string, os, uuid, time, sys
from shutil import copyfile


main = Tk()
root = Tk()

# global vars
isWim = False
wimLocation = StringVar()
destLocation = StringVar()
captureFrom = StringVar()
captureTo = StringVar()
subprocessOutput = None
driveList = []
dpartfilename = str(uuid.uuid4().hex) #this is the tempfile for diskpart

class redirectStdOut(object):
    def __init__(self, text_ctrl):
        """Constructor"""
        self.output = text_ctrl

    def write(self, string):
        """"""
        self.output.insert(Tkinter.END, string)

rows = 0
while rows < 50:
    main.rowconfigure(rows, weight=1)
    main.columnconfigure(rows, weight=1)
    rows += 1

tabFrame = Frame(main)
tabFrame.grid(row=0)

tabLocation = ttk.Notebook(tabFrame)
tabLocation.grid(row=0, column=0, columnspan=50, rowspan=49, sticky='NESW')

tab1 = ttk.Frame(tabLocation)
tabLocation.add(tab1, text="Flash Image")

tab2 = ttk.Frame(tabLocation)
tabLocation.add(tab2, text="Capture Image")

tab1Leftside = Frame(tab1)
tab1Leftside.grid(column=0)

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


def closescript():
    exit()


def scandestination():
    global driveList
    while len(driveList) > 0:
        driveList.pop()
    checkPhyDrives = subprocess.Popen("wmic diskdrive get index,model,serialnumber", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in checkPhyDrives.stdout.readlines():
        if "Index" in line:
            continue
        driveList.append(line.rstrip())
        driveList = filter(None, driveList)
    return driveList


def startcopy():
    global wimLocation
    global destLocation
    global isWim
    if isWim == True:
        #print(wimLocation.get())
        #print(destLocation)
        ## Ryan can type code here- this is on start button
        #CLEAN DISK
        dpartfile = open(dpartfilename, "w")
        #clean selected disk
        dpartfile.write('select disk ' + str(destLocation[:1]))
        dpartfile.write('\nclean')
        dpartfile.close()
        #EXECUTE THE DISKPART TO CLEAN THE SELECTED DISK NUMBER
        os.system("diskpart /s " + dpartfilename)
        os.remove(dpartfilename)
        #DEFINING ALPHABET OF UNSUED VOLUMES
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
        print alphabet
        del alphabet[0:2] #this is to ensure there are a couple free letters not in use
        if len(alphabet) < 3:
            print "There are not enough free Volume Letters"
            exit(2)
        partitionWindows = alphabet[0]
        del alphabet[0]
        partitionRecovery = alphabet[0]
        del alphabet[0]
        partitionHidden = alphabet[0]
        print "--- Volume letters for drive partitions..."
        print "Windows - " + partitionWindows
        print "Recovery - " + partitionRecovery
        print "Hidden - " + partitionHidden
        partitionWindows = partitionWindows[:1]
        partitionRecovery = partitionRecovery[:1]
        partitionHidden = partitionHidden[:1]
        #CREATE DRIVE PARTITONS
        dpartfile = open(dpartfilename, "w")
        dpartfile.write('select disk ' + str(destLocation[:1]))
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
        try:
            #exDiskPart = subprocess.Popen("diskpart /s " + dpartfilename, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            subprocess.check_call("diskpart /s " + dpartfilename)
            #print exDiskPart
            pausing = raw_input()
            #os.system("diskpart /s " + dpartfilename)
        except ValueError:
            os.system("color 40")
            time.sleep(1)
            print "ERROR ERROR ERROR"
            print "There was a problem cleaning and partitioning drive"
            pausing = raw_input()
            exit(1)
        os.remove(dpartfilename)
        #COPY UNATTEND FILE
        os.system("copy unattend.xml "+ partitionWindows + ":\\")
        #APPLY IMAGE
        pausing = raw_input()
        pathWim = wimLocation.get()
        pathWim = pathWim.replace("/","\\")
        try:
            os.system('dism /apply-image /imagefile:"' + pathWim + '" /index:1 /ApplyDir:' + partitionWindows + ':\\')
        except ValueError:
            os.system("color 40")
            time.sleep(1)
            print "ERROR ERROR ERROR"
            print "There was a problem when imaging the drive"
            pausing = raw_input()
            exit(1)
        #MAKE BOOTABLE
        os.system("bcdboot.exe " + partitionWindows + ":\\windows /s " + partitionHidden + ":")
        #COPY DESKTOP FILES
        if os.path.exists("DesktopFiles"):
            from distutils.dir_util import copy_tree
            print "Copying Desktop Files"
            #copy_tree("DesktopFiles", partitionWindows + ":\\Users\\Public\\Desktop")
            os.system("robocopy DesktopFiles " + partitionWindows + ":\\Users\\Public\\Desktop /E")
        print "Image Process Is Complete"
        #os.system("color 20") #this turns prompt green.. needs errorchecking
        time.sleep(5)
        pausing=raw_input()
        closescript()
    else:
        tkMessageBox.showerror(title="Error", message="File selected is either not a .wim file, or no file was selected")


def CurSelect(event):
    global destLocation
    widget = event.widget
    selection = widget.curselection()
    destLocation = widget.get(selection[0])


def sourceframe():
    # title
    titleLabel = main
    titleLabel.title("EasyWIM")

    # Source text on top
    fileMessageLabel = Label(tab1, text=" Source File:", anchor=NW, width=70)
    fileMessageLabel.grid(row=0)

    # entry box for file path
    source = Entry(tab1, width=80, textvariable=wimLocation)
    source.grid(row=1)

    # select source button here
    sourceButton = Button(tab1, width=20, text="Image Location...", command=callpath)
    sourceButton.grid(row=1, column=1)


def destinationframe():
    global destLocation
    # destination text here
    destinationMessageLabel = Label(tab1, text=" Destination:", anchor=NW, width=70)
    destinationMessageLabel.grid(row=2)
    # list of destinations found
    destinationOptions = Listbox(tab1, width=80, selectmode=SINGLE)
    destinationOptions.bind('<<ListboxSelect>>', CurSelect)
    destinationOptions.grid(row=3, rowspan=2)
    scandestination()
    for item in driveList:
        destinationOptions.insert(END, item + " Drive")
    destinationRefresh = Button(tab1, text="Refresh Drive List", width=20, command=destinationframe)
    destinationRefresh.grid(row=3, column=1)
    destLocation = destinationOptions.get(ACTIVE)


def captureDirectoryframe():
    global captureDirectory
    # directory text here
    captureMessageLabel = Label(tab2, text=" Select capture directory:", anchor=NW, width=70)
    captureMessageLabel.grid(row=0)

    directoryOptions = Listbox(tab2, width=80, selectmode=SINGLE)
    #directoryOptions.bind('<<ListboxSelect>>', CurSelect)
    directoryOptions.grid(row=1)
    scandestination()
    for item in driveList:
        directoryOptions.insert(END, item)
    directoryRefresh = Button(tab2, text="Refresh Directory List", width=20, command=captureDirectoryframe)
    directoryRefresh.grid(row=1, column=1, pady=(0,140))
    captureFrom = directoryOptions.get(ACTIVE)


def storeCaptureframe():
    # Source text on top
    captureMessageLabel = Label(tab2, text=" Destination:", anchor=NW, width=70)
    captureMessageLabel.grid(row=2)

    # entry box for file path
    source = Entry(tab2, width=80, textvariable=captureTo)
    source.grid(row=3)

    # select source button here
    sourceButton = Button(tab2, width=20, text="Select Image Destination", command=callpath)
    sourceButton.grid(row=2, column=1)

def loggingframe():
    loggingMessageTitle = Label(main, text="Logging:", width=92, anchor=W)
    loggingMessageTitle.grid(row=2)

    loggingMessageFrame = Frame(main, width=90, height=120)
    loggingMessageFrame.grid(row=4)
    loggingMessageFrame.columnconfigure(0, weight=10)
    scrollbar = Scrollbar(loggingMessageFrame, bg="gray30", troughcolor="gray4")
    scrollbar.pack(side="right", fill="y")
    loggingMessageBody = Text(loggingMessageFrame, background="gray17", fg="ghost white", yscrollcommand=scrollbar.set)

    loggingMessageBody.config(state="normal")
    loggingMessageBody.insert(INSERT, "EasyWim Initialized...")
    loggingMessageBody.pack(side="left", fill="both", expand=True)

    loggingMessageBody.config(state="disabled")
    scrollbar.config(command=loggingMessageBody.yview)


def optionframe(w, x, y, z):
    # start/cancel container
    optionContainer = Frame(x)
    optionContainer.grid(row=w, column=1, pady=(z, 0))

    # insert start button
    startButton = Button(optionContainer, width=10, text="Start", command=y)
    startButton.grid(row=0, column=0)

    # insert cancel button
    cancelButton = Button(optionContainer, width=10, text="Cancel", command=closescript)
    cancelButton.grid(row=0, column=1)


main.resizable(width="false", height="false")
root.withdraw()

#initializetabs()
sourceframe()
destinationframe()
optionframe(4, tab1, startcopy, 110)

captureDirectoryframe()
storeCaptureframe()
optionframe(3, tab2, None, 0)

loggingframe()

main.mainloop()
