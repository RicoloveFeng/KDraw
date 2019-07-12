import json
def point(x, y):
    return (float(x), float(y),)

def interpret(rawCommandList):
    '''
    will check id validity.
    generally, if a command is valid, divide it into 3 parts:
        for draw related command:
            command name;
            id;
            color;
            points.
        for adjusting command:
            command name;
            id;
            parameters.
        for canvas command:
            command name.
    see code for exact defination
    '''
    ids = {}
    opcodes = []
    penColor = (0,0,0)
    pc = 0
    for cmd in rawCommandList:
        cmd = cmd.split()
        name = cmd[0]

        if name in ["resetCanvas","saveCanvas"]: #canvas command
            if name == "resetCanvas":
                for x in cmd[1:]:
                    if not 100 <= int(x) <= 1000:
                        raise ValueError(pc) 
                opcodes.append({"command":"RC", "width":cmd[1], "height":cmd[2]})
            
            else: # name == "saveCanvas"
                opcodes.append({"command":"SC", "path":cmd[1]})

        elif name == "setColor": # color setting
            buffer = tuple(int(x) for x in cmd[1:])
            for color in buffer:
                if not 0 <= color <= 255:
                    raise ValueError(pc)
            penColor = buffer

        elif name in ["drawLine","drawPolygon","drawEllipse","drawCurve"]: # draw commamd
            #checking id firstly
            cmdId = cmd[1]
            if cmdId in ids:
                raise KeyError("id " + str(cmdId) + " has been used.")
            else:
                ids[cmdId] = name
            
            if name == "drawLine":
                algorithm = cmd[6]
                points = [point(cmd[2], cmd[3]), point(cmd[4], cmd[5])]
                opcodes.append({
                    "command":"DL",
                    "id":cmdId,
                    "points":points,
                    "algorithm":algorithm,
                    "color": penColor
                })
            
            elif name == "drawEllipse":
                opcodes.append({
                    "command":"DE",
                    "id":cmdId,
                    "points":[point(cmd[2], cmd[3])],
                    "rx": float(cmd[4]),
                    "ry": float(cmd[5]),
                    "color": penColor
                })

            else:
                commandName = ""
                points = []
                if name == "drawPolygon":
                    commandName = "DP"
                elif name == "drawCurve": 
                    commandName = "DC"
                algorithm = cmd[3]
                
                for index in range(len(cmd[4:]) // 2):
                    loc = index * 2 + 4
                    points.append(point(cmd[loc], cmd[loc + 1]))

                if commandName == "DC" and algorithm == "B-spline" and len(points) < 4:
                    raise ValueError(pc) # 3 degree b-spline curve requires at least 4 points.

                opcodes.append({
                    "command":commandName,
                    "id": cmdId,
                    "points": points, # we dont need to record points number, just use len().
                    "algorithm": algorithm,
                    "color": penColor
                })
        else: #if name in ["translate","rotate","scale","clip"] # adjusting command
            cmdId = cmd[1]
            if cmdId not in ids:
                print(cmd, ids, cmdId)
                raise KeyError("Unused id:" + str(cmdId))
            
            if name == "translate":
                opcodes.append({
                    "command":"T",
                    "id":cmdId,
                    "dx":float(cmd[2]),
                    "dy":float(cmd[3])
                })
            
            elif name == "rotate":
                if ids[cmdId] == "drawEllipse":
                    raise TypeError(name, ids[cmdId])
                opcodes.append({
                    "command":"R",
                    "id":cmdId,
                    "x":float(cmd[2]),
                    "y":float(cmd[3]),
                    "r":float(cmd[4])
                })
            
            elif name == "scale":
                opcodes.append({
                    "command":"S",
                    "id":cmdId,
                    "x":float(cmd[2]),
                    "y":float(cmd[3]),
                    "s":float(cmd[4])
                })

            elif name == "clip":
                if ids[cmdId] != "drawLine":
                    raise TypeError(name, ids[cmdId])
                opcodes.append({
                    "command":"C",
                    "id":cmdId,
                    "left":float(cmd[2]),
                    "bottom": float(cmd[3]),
                    "right": float(cmd[4]),
                    "top": float(cmd[5]),
                    "algorithm": cmd[6]
                })

        pc += 1

    return opcodes