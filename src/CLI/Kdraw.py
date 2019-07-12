'''
KDraw v0.0.1
1. setColor has been writen in opcodes when in instruction.py
2. for resetCanvas command, change img object and clear oplist
3. for draw command, put it into list
4. for adjust command, find in list according to id, and adjusting points
5. for saveCanvas command, run drawing commands and save canvas
'''
from PIL import Image
from scipy.special import comb
import math
img = Image.new("RGB", (256, 256))
now_width = 256
now_height = 256
opQueue = []
save = ""

def getOpc(opid):
    '''
    return opid dict
    always succeed
    '''
    global opQueue
    for i in opQueue:
        if i["id"] == opid: return i
    
def drawPoint(x, y, color):
    global img
    pixels = img.load()
    width = img.width
    height = img.height
    x = int(round(x))
    y = int(round(y))
    try:
        if (0 <= x < width) and (0 <= y < height):
            pixels[x, height - y - 1] = color
    except IndexError:
        print(x, y, width, height)
    
def resetCanvas(opcode):
    global img, opQueue, now_height, now_width
    now_width = int(opcode["width"])
    now_height = int(opcode["height"])

    img = Image.new("RGB", (now_width, now_height), 0xffffff)
    opQueue = []

def drawLine(opcode):
    x1 = round(opcode["points"][0][0])
    y1 = round(opcode["points"][0][1])
    x2 = round(opcode["points"][1][0])
    y2 = round(opcode["points"][1][1])
    if opcode["algorithm"] == "N/A": # in case the line has been cliped 
        pass
    elif opcode["algorithm"] == "DDA":
        dx = x2 - x1
        dy = y2 - y1
        step = abs(dx) if abs(dx) >= abs(dy) else abs(dy)
        dx = dx / step
        dy = dy / step
        x = x1
        y = y1
        for _ in range(int(step)):
            drawPoint(x, y, opcode["color"])
            x = x + dx
            y = y + dy
    else: #bresenham
        def drawLow(a1, b1, a2, b2):
            dx = a2-a1
            dy = b2-b1
            yi = 1
            if dy < 0:
                yi = -1
                dy = -dy
            ddy = 2*dy
            ddx = 2*dx
            D = ddy - dx
            y = b1

            for x in range(a1, a2 + 1):
                drawPoint(x, y, opcode["color"])
                if D >= 0:
                    y = y + yi
                    D = D - ddx
                D = D + ddy
        def drawHigh(a1, b1, a2, b2):
            dx = a2-a1
            dy = b2-b1
            xi = 1
            if dx < 0:
                xi = -1
                dx = -dx
            ddy = 2*dy
            ddx = 2*dx
            D = ddx - dy
            x = a1

            for y in range(b1, b2 + 1):
                drawPoint(x, y, opcode["color"])
                if D >= 0:
                    x = x + xi
                    D = D - ddy
                D = D + ddx

        if abs(y2 - y1) < abs(x2 - x1):
            drawLow(x2,y2,x1,y1) if x1 > x2 else drawLow(x1,y1,x2,y2)
        else:
            drawHigh(x2,y2,x1,y1) if y1 > y2 else drawHigh(x1,y1,x2,y2)


def drawPolygon(opcode):
    pointsCount = len(opcode["points"])
    if opcode["algorithm"] == "DDA":
        i = 0
        while i + 1 < pointsCount:
            p1 = opcode["points"][i]
            p2 = opcode["points"][i+1]
            drawLine({
                "points":[p1, p2],
                "algorithm": "DDA",
                "color": opcode["color"]
            })
            i += 1
        drawLine({
                "points":[opcode["points"][-1], opcode["points"][0]],
                "algorithm": "DDA",
                "color": opcode["color"]
            })
    else: #bresenham
        i = 0
        while i + 1 < pointsCount:
            p1 = opcode["points"][i]
            p2 = opcode["points"][i+1]
            drawLine({
                "points":[p1, p2],
                "algorithm": "Brehensam",
                "color": opcode["color"]
            })
            i += 1
        drawLine({
            "points":[opcode["points"][-1], opcode["points"][0]],
            "algorithm": "Brehensam",
            "color": opcode["color"]
        })

def drawEllipse(opcode):
    cx = round(opcode["points"][0][0])
    cy = round(opcode["points"][0][1])

    def drawEllipsePoint(x, y): # refer center at above
        color = opcode["color"]
        drawPoint(cx+x, cy+y, color)
        drawPoint(cx-x, cy+y, color)
        drawPoint(cx+x, cy-y, color)
        drawPoint(cx-x, cy-y, color)
    rx = round(opcode["rx"])
    ry = round(opcode["ry"])
    rx2 = rx * rx
    ry2 = ry * ry
    trx2 = 2 * rx2
    try2 = 2 * ry2
    x = 0
    y = ry
    px = 0
    py = trx2 * y
    #initial
    drawEllipsePoint(x, y)
    # region 1
    p = round(ry2 - rx2 * ry + 0.25 * rx2)
    while px < py:
        x += 1
        px += try2
        if p < 0:
            p += ry2 + px
        else:
            y -= 1
            py -= trx2
            p += ry2 + px - py
        drawEllipsePoint(x, y)
    # region 2
    p = round(ry2 * (x + 0.5) ** 2 + rx2 * (y - 1) ** 2 - rx2 * ry2)
    while y > 0:
        y -= 1
        py -= trx2
        if p > 0:
            p += rx2 - py
        else:
            x += 1
            px += try2
            p += rx2 - py + px
        drawEllipsePoint(x, y)
    

def drawCurve(opcode):
    global img
    if opcode["algorithm"] == "Bezier":
        #18 sample points
        
        points = opcode["points"]
        pointsCount = len(points)
        samples = 18

        cof = []
        for i in range(pointsCount):
            cof.append(comb(pointsCount - 1, i))
        
        res = []
        for s in range(samples):
            t = s / (samples - 1)
            tinv = 1 - t
            x = 0.0
            y = 0.0
            for i in range(pointsCount):
                fac = cof[i] * t ** i * tinv ** (pointsCount- i - 1)
                x += points[i][0] * fac
                y += points[i][1] * fac  
            res.append((int(round(x)), int(round(y))))
        
        for i in range(samples - 1):
            drawLine({
                "points":[res[i], res[i+1]],
                "algorithm": "Brehensam",
                "color": opcode["color"]
            })
        
    else: 
        #Using Clamped B-spline curve
        points = opcode["points"]
        n = len(points) - 1 # n+1 control points, n intervals
        k = 3 # order 3
        samples = 200
        res = []
        
        #calculate knot vector, n + k + 1 in total
        u = []
        for _ in range(k - 1): # 0 ~ k-2, k-1 in total
            u.append(0.0)
        for i in range(n - k + 3): # k-1 ~ n+1, n - k + 3 in total 
            u.append( i / (n - k + 2)) 
        for _ in range(k - 1): # n+2 ~ n+k, k - 1 in total
            u.append(1.0)

        #basic function, using de Boor-Cox euqation
        def B(i, k, t):
            if k == 1:
                return 1.0 if u[i] <= t <= u[i+1] else 0 # assuming 0 / 0 = 0
            else:
                ret = 0
                fac1 = B(i, k - 1, t)
                fac2 = B(i + 1, k - 1, t)
                if fac1 and t - u[i]:
                    ret += (t - u[i]) / (u[i+k-1] - u[i]) * fac1
                if fac2 and u[i+k] - t:
                    ret += (u[i+k] - t) / (u[i+k] - u[i+1]) * fac2
                return ret

        for s in range(samples):
            t = s / (samples - 1) # u[k-1] is 0 and u[n+1] is 1
            x = 0.0
            y = 0.0
            for i in range(n + 1):
                fac = B(i, k, t)
                x += points[i][0] * fac
                y += points[i][1] * fac  
            res.append((int(round(x)), int(round(y))))

        for i in range(samples - 1):
            drawLine({
                "points":[res[i], res[i+1]],
                "algorithm": "Brehensam",
                "color": opcode["color"]
            })



def translate(opcode):
    obj = getOpc(opcode["id"])
    dx = opcode["dx"]
    dy = opcode["dy"]
    for i in range(len(obj["points"])):
        p = list(obj["points"][i])
        p[0] = p[0] + dx
        p[1] = p[1] + dy
        obj["points"][i] = tuple(p) #保存结果

def rotate(opcode):
    obj = getOpc(opcode["id"])
    xr = opcode["x"]
    yr = opcode["y"]
    r = opcode["r"] / 180 * math.pi * -1
    for i in range(len(obj["points"])):
        p = list(obj["points"][i])
        x = p[0]
        y = p[1]
        p[0] = xr + (x - xr) * math.cos(r) - (y - yr) * math.sin(r)
        p[1] = yr + (x - xr) * math.sin(r) + (y - yr) * math.cos(r)
        obj["points"][i] = tuple(p) #保存结果

def scale(opcode):
    obj = getOpc(opcode["id"])
    xf = opcode["x"]
    yf = opcode["y"]
    s = opcode["s"]
    for i in range(len(obj["points"])):
        p = list(obj["points"][i])
        p[0] = p[0] * s + xf * (1 - s)
        p[1] = p[1] * s + yf * (1 - s)
        if obj["command"] == "DE": # 椭圆的特殊处理
            obj["rx"] = obj["rx"] * s
            obj["ry"] = obj["ry"] * s
        obj["points"][i] = tuple(p) # 保存结果

def clip(opcode):
    print("start:",opQueue)
    obj = getOpc(opcode["id"])
    algorithm = opcode["algorithm"]
    top = opcode["top"]
    left = opcode["left"]
    bottom = opcode["bottom"]
    right = opcode["right"]
    x1 = obj["points"][0][0]
    y1 = obj["points"][0][1]
    x2 = obj["points"][1][0]
    y2 = obj["points"][1][1]

    if algorithm == "Cohen-Sutherland":
        L = 1
        R = 2
        B = 4
        T = 8
        def nodeCode(x, y):
            code = 0
            if x < left: code += L
            elif x > right: code += R
            if y > top: code += T
            elif y < bottom: code += B
            return code

        code1 = nodeCode(x1, y1)
        code2 = nodeCode(x2, y2)

        while True:
            if (code1 | code2) == 0: # 全都在0000
                break
            if (code1 & code2) != 0: # 有bit求余后为1
                obj["algorithm"] = "N/A"
                break
            if y1 == y2 or x1 == x2: # 考虑特殊斜率
                if y1 == y2:
                    if x1 & T: x1 = top
                    elif x1 & B: x1 = bottom
                    if x2 & T: x2 = top
                    elif x2 & B: x2 = bottom
                if x1 == x2:
                    if y1 & L: y1 = left
                    elif y1 & R: y1 = right
                    if y2 & L: y1 = left
                    elif y2 & R: y1 = right
                break
            
            # 进行裁剪
            x, y = (-1.0, -1.0)
            code = code1 if code1 != 0 else code2
            k = (y1 - y2) / (x1 - x2)
            kinv = 1 / k

            if code & L:
                y = y1 + k * (left - x1)
                x = left
            elif code & R:
                y = y1 + k * (right - x1)
                x = right
            elif code & T:
                x = x1 + kinv * (top - y1)
                y = top
            elif code & B:
                x = x1 + kinv *(bottom - y1)
                y = bottom
            
            if code1:
                x1, y1 = (x, y)
                code1 = nodeCode(x, y)
            else:
                x2, y2 = (x, y)
                code2 = nodeCode(x, y)

        #保存结果
        obj["points"][0] = (x1, y1,)
        obj["points"][1] = (x2, y2,)

    else: #Liang-Barsky
        dx = x2 - x1
        dy = y2 - y1
        #处理平行的直线
        if (dx == 0 and not left <= x1 <= right) or (dy == 0 and not bottom <= y1 <= top):
            obj["algorithm"] = "N/A"
            return
        elif dx == 0 or dy == 0:
            if dx == 0:
                if y1 > top: y1 = top
                elif y1 < bottom: y1 = bottom
                if y2 > top: y2 = top
                elif y2 < bottom: y2 = bottom
            else: #dy == 0
                if x1 < left: x1 = left
                elif x1 > right: x1 = right
                if x2 < left: x2 = left
                elif x2 > right: x2 = right

            obj["points"][0] = (x1, y1,)
            obj["points"][1] = (x2, y2,)
            return
        
        #计算四个p和q的值
        pq = []
        pq.append((-dx, x1 - left,))
        pq.append((dx, right - x1,))
        pq.append((-dy, y1 - bottom,))
        pq.append((dy, top - y1,))

        u = []
        maxu = [0,]
        minu = [1,]
        for pair in pq:
            u = pair[1] / pair[0]
            if pair[0] > 0:
                minu.append(u)
            else:
                maxu.append(u)

        #得出裁剪后的两个u值
        umax = max(maxu)
        umin = min(minu)
        if umin < umax: # 小数极大值大于大数极小值
            obj["algorithm"] = "N/A"
            return

        getx = lambda u: x1 + u * (x2 - x1)
        gety = lambda u: y1 + u * (y2 - y1)
        obj["points"][0] = (getx(umin), gety(umin),)
        obj["points"][1] = (getx(umax), gety(umax),)
            
    print("end:", opQueue)

def saveCanvas(opcode):
    global opQueue, img, save
    filename = opcode["path"]
    if filename[-4:] != ".bmp": filename += ".bmp"

    drawCommandTable={
        "DL": drawLine,
        "DP": drawPolygon,
        "DE": drawEllipse,
        "DC": drawCurve
    }
    img = Image.new("RGB", (now_width, now_height), 0xffffff)
    for opc in opQueue:
        drawCommandTable[opc["command"]](opc)
    
    print("saving img!")
    img.save(save+filename)

commandTable = {
    "RC": resetCanvas,
    "SC": saveCanvas,
    "T": translate,
    "R": rotate,
    "S": scale,
    "C": clip
}
    

def run(opcodes, dirSave):
    global opQueue, save

    print("file msg:", dirSave)
    save = dirSave

    #test
    for opc in opcodes:
        print(opc)
    
    for opc in opcodes:
        cmd = opc["command"]
        if cmd[0] == "D": #draw command
            opQueue.append(opc)
        else:
            commandTable[cmd](opc)
    
    print("run done.")
