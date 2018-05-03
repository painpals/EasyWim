# EasyWim
#   Created by Ryan Rubash and Tyler Ziegler
#     for flashing wim images into hard drives
"""
1.0.0 = (2/22/2018) GUI and initial Alpha
1.0.1 = added fail checks, robocopy for desktopfiles
1.0.2 = (3/20/2018) added blacklist file, timestamp
1.0.3 = Separation of GUI Generation and Logic functions, added raise ValueError
        added checkbox to GUI for copying DesktopFiles, added textboxes for stdout with details
1.0.4 = Rewritten GUI to have more specific variables, added tab for wim capture (not functional)
        added error_stop function, added drive to title when running
"""

version = "1.0.4"


from Tkinter import *
import ttk
import tkFileDialog
import tkMessageBox
import ScrolledText
import threading
import subprocess, string, os, uuid, time, sys, datetime
main = Tk()
main.resizable(width=False, height=False)


############################################################################
########################### GUI Structure
############################################################################
tabFrame = Frame(main)
tabFrame.grid(row=0)

tabLocation = ttk.Notebook(tabFrame)
tabLocation.grid(row=0, column=0, columnspan=50, rowspan=49, sticky='NESW')

tab_deploy = ttk.Frame(tabLocation)
tabLocation.add(tab_deploy, text="DEPLOY")

tab_capture = ttk.Frame(tabLocation)
tabLocation.add(tab_capture, text="CAPTURE")

tab_about = ttk.Frame(tabLocation)
tabLocation.add(tab_about, text="ABOUT")



def frame_gui():
    titleLabel = main
    titleLabel.title("EasyWim_" + str(version))

#tab1 variables
wim_location = StringVar()
check_desktopfiles = IntVar()
check_desktopfiles.set(1)
destination_drive = ""
drive_list = []
def frame_deploy():
    global destination_drive
    tab1_lbl_source = Label(tab_deploy, text=" Source File :", anchor=NW, width=70)
    tab1_lbl_source.grid(row=0)
    tab1_txtbox_wimlocation = Entry(tab_deploy, width=80, textvariable=wim_location)
    tab1_txtbox_wimlocation.grid(row=1)
    tab1_btn_selectwim = Button(tab_deploy, width=20, text="Image Location...", command=trig_wim_location)
    tab1_btn_selectwim.grid(row=1, column=1)

    tab1_lbl_destintation = Label(tab_deploy, text=" Destination Drive :", anchor=NW, width=70)
    tab1_lbl_destintation.grid(row=2)
    tab1_lstbx_destinationdrives = Listbox(tab_deploy, width=80, selectmode=SINGLE)
    tab1_lstbx_destinationdrives.bind('<<ListboxSelect>>', cursor_select)
    tab1_lstbx_destinationdrives.grid(row=3, rowspan=2)
    Generate_Drive_List()
    for item in drive_list:
        tab1_lstbx_destinationdrives.insert(END, item)
    tab1_btn_refreshdrives = Button(tab_deploy, text="Refresh Drives", width=20, command=frame_deploy)
    tab1_btn_refreshdrives.grid(row=3, column=1)

    tab1_deploy_exit = Frame(tab_deploy)
    tab1_deploy_exit.grid(row=5, column=1)
    tab1_btn_deploy = Button(tab1_deploy_exit, width=10, text="Deploy", command=trig_deploy)
    tab1_btn_deploy.grid(row=0, column=0)
    tab1_btn_exit = Button(tab1_deploy_exit, width=10, text="Exit", command=exit_script)
    tab1_btn_exit.grid(row=0, column=1)

    tab1_chbx_desktopfiles = Checkbutton(tab_deploy, text="Copy DesktopFiles", variable=check_desktopfiles)
    tab1_chbx_desktopfiles.grid(row=5, column=0, sticky=W)

    destination_drive = tab1_lstbx_destinationdrives.get(ACTIVE)

#tab 2 variables
wimSaveLocation = StringVar()
lst_volumes = []
def frame_capture():
    tab2_lbl_save = Label(tab_capture, text=" Destination :", anchor=NW, width=70)
    tab2_lbl_save.grid(row=0)
    tab2_txtbox_savelocation = Entry(tab_capture, width=80, textvariable=wimSaveLocation)
    tab2_txtbox_savelocation.grid(row=1)
    tab2_btn_selectsave = Button(tab_capture, width=20, text="Save Location...", command=None) #change command later
    tab2_btn_selectsave.grid(row=1, column=1)

    tab2_lbl_sourcevol = Label(tab_capture, text=" Source Volume :", anchor=NW, width=70)
    tab2_lbl_sourcevol.grid(row=2)
    tab2_lstbx_sourcevol = Listbox(tab_capture, width=80, selectmode=SINGLE)
    tab2_lstbx_sourcevol.bind('<<ListboxSelect>>', cursor_select)
    tab2_lstbx_sourcevol.grid(row=3, rowspan=2)
    #need the function to get source volumes
    for item in lst_volumes:
        tab2_lstbx_sourcevol.insert(END, item)
    tab2_btn_refreshvolumes = Button(tab_capture, text="Refresh Volumes", width=20, command=None) #change command later
    tab2_btn_refreshvolumes.grid(row=3, column=1)

    tab2_capture_exit = Frame(tab_capture)
    tab2_capture_exit.grid(row=5, column=1)
    tab2_btn_capture = Button(tab2_capture_exit, width=10, text="Capture", command=None) #change command later
    tab2_btn_capture.grid(row=0, column=0)
    tab2_btn_exit = Button(tab2_capture_exit, width=10, text="Exit", command=exit_script)
    tab2_btn_exit.grid(row=0, column=1)

    tab2_lbl_note = Label(tab_capture, text="Note: Capture is for Windows OS")
    tab2_lbl_note.grid(row=5, column=0, sticky=W)


def frame_about():
    about_lbl = Label(tab_about, text="This EasyWim was created by Ryan Rubash and Tyler Ziegler\n\nIt's purpose is to speed up the WIM deployment process", anchor=NW)
    about_lbl.grid(row=0, rowspan=3)
    

def cursor_select(event): #this is the event for clicking on the drive in the tab_deploy
    global destLocation
    widget = event.widget
    selection = widget.curselection()
    destLocation = widget.get(selection[0])

############################################################################
########################### GUI Triggers
############################################################################
#tab1
def trig_wim_location():
    global wim_location
    wim_location.set(tkFileDialog.askopenfilename(parent=main, initialdir="/", title="Select your .wim file.", filetypes=(("WIM File","*.wim"),("All Files","*.*"))))
    
def trig_deploy():
    os.system("title EasyWim_" + str(version) + ": " + str(destination_drive))
    time_start = datetime.datetime.now()
    global wim_location
    wim_location = str(wim_location.get())
    wim_location = wim_location.replace("/","\\")
    wim_name = wim_location.split("\\"); wim_name = wim_name[-1]; wim_name = wim_name.replace(".wim","") ## get just the name
    global destination_drive
    destination_drive_num = destination_drive.split(); destination_drive_num = destination_drive_num[0]
    dpart_filename = str(uuid.uuid4().hex) #this is the tempfile for diskpart
    ## Check for unattend.xml file
    if not os.path.isfile("unattend.xml"):
        error_stop("Error: No unattend.xml found in directory")
    ## Verify file is WIM and exists
    if not str(wim_location).endswith(".wim"):
        error_stop("Error: File selected is not a wim")
    if not os.path.exists(wim_location):
        error_stop("Error: Wim file not found")
    ## Clean
    abox("CLEANING DRIVE", destination_drive)
    dpart_file = open(dpart_filename, "w")
    dpart_file.write('select disk ' + str(destination_drive_num))
    dpart_file.write('\nclean')
    dpart_file.close()
    try:
        subprocess.check_call("diskpart /s " + dpart_filename)
    except subprocess.CalledProcessError:
        os.remove(dpart_filename)
        error_stop("Error: There was a problem cleaning the drive")
    os.remove(dpart_filename)
    ## Get Volume Letters as Variables
    alphabet = []
    for i in string.ascii_uppercase:
        alphabet.append(i)
    mounted_letters = subprocess.Popen("wmic logicaldisk get name", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in mounted_letters.stdout.readlines():
        if "Name" in line:
            continue
        for letter in alphabet:
            if letter in line:
                alphabet.pop(alphabet.index(letter))
    del alphabet[0:2] #this is to ensure there are a couple free letters not in use
    if len(alphabet) < 3:
        error_stop("Error: There are not enough available volume letters.")
    volume_windows = alphabet[0]
    del alphabet[0]
    volume_recovery = alphabet[0]
    del alphabet[0]
    volume_hidden = alphabet[0]
    volume_windows = volume_windows[:1]
    volume_recovery = volume_recovery[:1]
    volume_hidden = volume_hidden[:1]
    ## Partition
    dpart_file = open(dpart_filename, "w")
    dpart_file.write('select disk ' + str(destination_drive_num))
    dpart_file.write('\nconvert gpt')
    dpart_file.write('\ncreate partition primary size=440')
    dpart_file.write('\nassign letter ' + volume_recovery)
    dpart_file.write('\nformat quick fs=ntfs label="Windows RE tools"')
    dpart_file.write('\nset id="de94bba4-06d1-4d40-a16a-bfd50179d6ac"')
    dpart_file.write('\ngpt attributes=0x8000000000000001')
    dpart_file.write('\ncreate partition efi size 260')
    dpart_file.write('\nassign letter ' + volume_hidden)
    dpart_file.write('\nformat quick FS=FAT32')
    dpart_file.write('\ncreate partition msr size 128')
    dpart_file.write('\ncreate partition primary')
    dpart_file.write('\nformat quick FS=NTFS LABEL="WINDOWS"')
    dpart_file.write('\nassign letter ' + volume_windows)
    dpart_file.close()
    abox("CREATING PARTITIONS",volume_windows + " - Windows", volume_recovery + " - Recovery", volume_hidden + " - EFI")
    try:
        subprocess.check_call("diskpart /s " + dpart_filename)
    except subprocess.CalledProcessError:
        os.remove(dpart_filename)
        error_stop("Error: There was a problem with partitioning the drive")
    os.remove(dpart_filename)
    ## Apply WIM File
    abox("DEPLOYING .WIM FILE",wim_name)
    try:
        subprocess.check_call('dism /apply-image /imagefile:"' + wim_location + '" /index:1 /ApplyDir:' + volume_windows + ':\\')
    except subprocess.CalledProcessError:
        error_stop("Error: DISM failed to write to volume.")
    ## Make Drive Bootable
    try:
        os.system("copy unattend.xml "+ volume_windows + ":\\")
    except:
        error_stop("Error: Failed to copy unattend.xml file.")
    try:
        subprocess.check_call("bcdboot.exe " + volume_windows + ":\\windows /s " + volume_hidden + ":")
    except subprocess.CalledProcessError:
        error_stop("Error: BCDBoot failed.")
    ## DesktopFiles Check and Copy
    global check_desktopfiles
    if check_desktopfiles.get() == 1:
        if os.path.exists("DesktopFiles"):
            abox("COPYING DESKTOP FILES")
            try:
                subprocess.check_call("robocopy DesktopFiles " + volume_windows + ":\\Users\\Public\\Desktop /E")
            except subprocess.CalledProcessError:
                print "WARN: RoboCopy found an error, this might be just a missing file on desktop"
        else:
            print "WARN: DesktopFile directory not found"
    else:
        print ""
    file1 = open(volume_windows + ":\\Users\\Public\\Desktop\\" + wim_name + ".txt", "w")
    file1.close()
    ## Deploy Complete
    os.system("color 20")
    time_end = datetime.datetime.now()
    time_dif = time_end - time_start
    time_dif = divmod(time_dif.days * 8600 + time_dif.seconds, 60)
    abox("--IMAGE PROCESS COMPLETE--","Run Time = " + str(time_dif[0]) + " minutes and " + str(time_dif[1]) + " seconds.","WIM: " + str(wim_name),"Drive: " + destLocation)
    pausing = raw_input("\nPress ENTER to EXIT")
    exit()

#tab2
def trig_save_location():
    print "Clicked Save Location"

def trig_capture():
    print "Clicked Capture"

############################################################################
########################### Functions
############################################################################
def Generate_Drive_List():
    import os, subprocess
    os.system("color")
    os.system("cls")
    if os.path.exists("Blacklist.txt"):
        with open("Blacklist.txt") as f:
            contents = f.readlines()
        Blacklist = [x.strip() for x in contents]
        print "Blacklist file loaded"
    else:
        print "No Blacklist file found"
    global drive_list
    while len(drive_list) > 0:
        drive_list.pop()
    checkPhyDrives = subprocess.Popen("wmic diskdrive get index,model,serialnumber", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in checkPhyDrives.stdout.readlines():
        if "Index" in line:
            continue
        drive_list.append(line.rstrip())
        drive_list = filter(None, drive_list)
    i = 0 #this counter is to run through all the options of the system.. later we might try math of len*len
    while i < 500:
        for drive in drive_list:
            for anti in Blacklist:
                if anti.lower() in drive.lower():
                    drive_list.remove(drive)
        i +=1
    return drive_list

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

def error_stop(errorname):
    os.system("color 40")
    raise ValueError(errorname)

def exit_script():
    exit()










############################################################################
########################### Execution
############################################################################

os.system("cls")
os.system("color")
frame_gui()
frame_deploy()
frame_capture()

frame_about()
main.mainloop()
