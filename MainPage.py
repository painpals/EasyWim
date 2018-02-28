# Created by Ryan Rubash and Tyler Ziegler
# EasyWIM 0.6 2/22/2018
# for flashing wim images into hard drives
# written for python 2.7

from Tkinter import *
import tkFileDialog
import tkMessageBox
import subprocess


main = Tk()

# global vars
isWim = False
wimlocation = StringVar()
destLocation = StringVar()
driveList = []


def callpath():
    global isWim
    global wimlocation
    wimlocation.set(tkFileDialog.askopenfilename(parent=main, initialdir="/", title='Please select a directory'))
    # now checks path and will print error message if not a .wim file
    if str(wimlocation.get()).endswith(".wim"):
        isWim = True
    elif str(wimlocation.get()) is "":
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

    checkPhyDrives = subprocess.Popen("wmic diskdrive get index,model", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in checkPhyDrives.stdout.readlines():
        if "Index" in line:
            continue
        driveList.append(line.rstrip())
        driveList = filter(None, driveList)
    return driveList


def startcopy():
    global wimlocation
    global destLocation
    global isWim

    if isWim == True:
        print(wimlocation.get())
        print(destLocation)

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
    source = Entry(main, width=80, textvariable=wimlocation)
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

    destinationRefresh = Button(main, text="Refresh", width=20, anchor=NW, command=destinationframe)
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
