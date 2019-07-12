import sys, Kdraw
from instruction import interpret

#command usage
#n - number, f - float, s - string, ['a','b'] - options in string type, p - pairs(excluded by "points")
commandUsage={
    "resetCanvas": tuple('n' * 2), # width, height
    "saveCanvas": tuple('s'), #path
    "setColor": tuple('n' * 3), #r, g, b
    "drawLine": tuple('n') + tuple('f' * 4) + (("Bresenham","DDA"),), #id x1 y1 x2 y2 algorithm
    "drawPolygon": tuple('n' * 2) + (("Bresenham","DDA"),) + tuple('p'),# id points_amount algorithm pairs
    "drawEllipse": tuple('n') + tuple('f' * 4), #id x1 x2 y1 y2
    "drawCurve": tuple('n' * 2) + (("Bezier", "B-spline"),) + tuple('p'),# id points_amount algorithm pairs
    "translate": tuple('n') +tuple('f' * 2), # id dx dy
    "rotate": tuple('n') + tuple('f' * 3), # id x y r
    "scale": tuple('n') + tuple('f' * 3), # id x y s
    "clip": tuple('n') + tuple('f' * 4) + (("Cohen-Sutherland","Liang-Barsky"),)# id x1 y1 x2 y2 algorithm
}

def checkCommandValid(rawCommand):
    '''
    return: nothing, if meets error would raise and be caught by outside function.
    NameError: if we do not have that command
    SyntaxError: if the amount of args not enough or just excessed. Note that "points" does not have fixed length
    ValueError: if the arg does not match expected type
    '''
    global commandUsage
    rawCommand = rawCommand.split() #divide args
    commandName = rawCommand[0]

    if commandName not in commandUsage:
        raise NameError
    
    #ensure the args have same length as expected
    commandArgs = rawCommand[1:]
    usage = commandUsage[commandName]
    if usage[-1] != 'p' and len(commandArgs) != len(usage):
        print(commandArgs, usage)
        raise SyntaxError

    #remember every arg is now a string
    index = 0
    while index < len(usage):
        expectation = usage[index]
        meets = commandArgs[index] 
        if expectation == 'n' and meets.isdigit():
            try:
                meets.isdigit()
            except ValueError:
                raise ValueError('number', meets)
        elif expectation == 'f':
            try:
                float(meets)
            except ValueError:
                raise ValueError('float', meets)
        elif expectation == 's':
            pass # 100% success
        elif type(expectation) == tuple: #options
            if meets not in expectation:
                raise ValueError(expectation, meets)
        elif expectation == 'p':
            pointsAmount = int(commandArgs[1]) #id points_amount
            
            if len(commandArgs[index:]) != pointsAmount * 2: # check there are even numbers
                print(commandArgs[index:], pointsAmount * 2)
                raise SyntaxError
            for p in commandArgs[index:]:
                try:
                    float(p)
                except ValueError:
                    raise ValueError('float', p)
        #ending loop            
        index += 1

def checkAll(rawCommandList):
    '''
    check the validity of the command.

    note that range checking implements in internalized().
    '''
    rawCommand = ""
    listLength = len(rawCommandList)
    index = 0
    tmpList = []
    while index < listLength: #considering the two-line commands, should not iterate the list itself.
        #get the raw command
        rawCommand = rawCommandList[index].rstrip()
        if rawCommand.split()[0] in ["drawPolygon", "drawCurve"]:
            if index + 1 < listLength:
                rawCommand += " " + rawCommandList[index + 1].rstrip() #space for divide first coor
                index += 1
            else:
                print("Expecting a line followed to define points but meeting end of file.")
                return False

        #
        try:
            checkCommandValid(rawCommand) 
        except NameError:
            print("Undefined Command:", rawCommand.split()[0])
            exit()
        except SyntaxError:
            print("The amount of Args provided do not match the command")
            exit()
        except ValueError as errPair:
            print("Expecting",errPair.args[0],"but the arg is", errPair.args[1])
            exit()
        else:
            tmpList.append(rawCommand)
            print("command", rawCommand, "is valid.")
        #ending loop
        index += 1

    return tmpList

if __name__ == "__main__":
    # check whether input is valid
    if(len(sys.argv) == 1):
        print("Usage: main.py <command file> [directory to save]")
        exit()
    
    # get arg from command line
    commandFile = sys.argv[1]
    dirSave = sys.argv[2] if len(sys.argv) > 2 else "" #defalut to local dir
    print("Save as", commandFile, "at", dirSave)

    # check if command file exists, then read from file.
    try:
        commands = open(commandFile)
    except FileNotFoundError as err:
        print(err, "press enter to exit.")
        exit()
    
    #read all commands to list
    rawCommandList = []
    for c in commands.readlines():
        if c != '\n': rawCommandList.append(c)
    
    #translate raw command to internal command. 
    #firstly check if command args type
    try: 
        rawCommandList = checkAll(rawCommandList)
        #secondly check if things in their range and id is not reused
        drawOpcodes = interpret(rawCommandList)
    except ValueError as err:
        print("range out of limitaion in", err.args[0])
        exit()
    except KeyError as err: # 
        print(err.args[0])
        exit()
    except TypeError as err:
        print("Invalid operating behavior:", err.args[0], "->", err.args[1])
        exit()

    #draw it! Transfer savdDir to the entrence of Kdraw.
    Kdraw.run(drawOpcodes, dirSave)
    
    #exit
    print("Successfully executed",len(drawOpcodes),"commands.")