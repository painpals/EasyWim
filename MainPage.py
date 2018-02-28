# Created by Ryan Rubash and Tyler Ziegler
# EasyWIM 1.0 2/22/2018
# for flashing wim images into hard drives
# written for python 2.7

from Tkinter import *
import tkFileDialog
import tkMessageBox
import subprocess, string, os, uuid, time
from shutil import copyfile



main = Tk()

# global vars
isWim = False
wimLocation = StringVar()
destLocation = StringVar()
driveList = []
dpartfilename = str(uuid.uuid4().hex) #this is the tempfile for diskpart


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
        os.system("diskpart /s " + dpartfilename)
        os.remove(dpartfilename)
        #COPY UNATTEND FILE
        os.system("copy unattend.xml "+ partitionWindows + ":\\")
        #APPLY IMAGE
        pathWim = wimLocation.get()
        pathWim = pathWim.replace("/","\\")
        os.system('dism /apply-image /imagefile:"' + pathWim + '" /index:1 /ApplyDir:' + partitionWindows + ':\\')
        #MAKE BOOTABLE
        os.system("bcdboot.exe " + partitionWindows + ":\\windows /s " + partitionHidden + ":")
        #COPY DESKTOP FILES
        if os.path.exists("DesktopFiles"):
            from distutils.dir_util import copy_tree
            print "Copying Desktop Files"
            copy_tree("DesktopFiles", partitionWindows + ":\\Users\\Public\\Desktop")
        print "Image Process Is Complete"
        os.system("color 20") #this turns prompt green.. needs errorchecking
        time.sleep(5)
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


sourceframe()
destinationframe()
optionframe()

main.mainloop()
