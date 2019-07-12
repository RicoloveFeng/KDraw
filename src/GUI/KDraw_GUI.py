import sys
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QMainWindow, QWidget,QAction, QPushButton, QFrame, QApplication,QVBoxLayout, QLabel,QHBoxLayout, QColorDialog, QFileDialog, QDialog, QTableWidget, QTableWidgetItem, QAbstractItemView
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QImage, QColor, QMouseEvent, QKeyEvent
from PyQt5.QtCore import QPoint, Qt, pyqtSignal, QTimer
from copy import deepcopy
from scipy.special import comb
import math, time

#############################################
#       General Functions                   #
#############################################
def getBoxPoint(points: list) -> list:
    if points[0] == points[-1]: # polygon
        left = points[0].x()
        right = points[0].x()
        top = points[0].y()
        bottom = points[0].y()
        for p in points:
            if p.y() > top:
                top = p.y()
            elif p.y() < bottom:
                bottom = p.y()

            if p.x() > right:
                right = p.x()
            elif p.x() < left:
                left = p.x()
        return [QPoint(left, bottom), QPoint(right, top)]             
    else:
        return [points[0], points[-1]]

def setPixelColor(img: QImage, x: int, y: int, color: QColor):
    width = img.width()
    height = img.height()
    if 0 <= x < width and 0 <= y < height: 
        img.setPixelColor(x, y, color)

def tooClose(a: QPoint, b: QPoint) -> bool:
    return a.x() + a.y() - (b.x() + b.y()) <= 2

#############################################
#             Drawing Algorithms            #
#############################################
def drawNewLine(img: QImage, p1: QPoint, p2: QPoint, mode: str, color: QColor) -> QImage:
    x1 = p1.x()
    y1 = p1.y()
    x2 = p2.x()
    y2 = p2.y()
    pixels = QImage(img)
    if x1 == x2 and y1 == y2:
        setPixelColor(pixels, x1, y1, color)
        return pixels
    elif mode == "DDA":
        dx = x2 - x1
        dy = y2 - y1
        step = abs(dx) if abs(dx) >= abs(dy) else abs(dy)
        dx = dx / step
        dy = dy / step
        x = x1
        y = y1
        for _ in range(int(step)):
            setPixelColor(pixels, x, y, color)
            x = x + dx
            y = y + dy
    else: # mode == BSH
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
                setPixelColor(pixels, x, y, color)
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
                setPixelColor(pixels, x, y, color)
                if D >= 0:
                    x = x + xi
                    D = D - ddy
                D = D + ddx

        if abs(y2 - y1) < abs(x2 - x1):
            drawLow(x2,y2,x1,y1) if x1 > x2 else drawLow(x1,y1,x2,y2)
        else:
            drawHigh(x2,y2,x1,y1) if y1 > y2 else drawHigh(x1,y1,x2,y2)
    return pixels

def drawNewPolygon(img: QImage, points: list, mode: str, color: QColor) -> QImage:
    for i in range(len(points) - 1):
        img = drawNewLine(img, points[i], points[i+1], mode, color)
    return img

def drawNewEllipse(img: QImage, p1: QPoint, p2: QPoint, color: QColor) -> QImage:
    cx = (p1.x() + p2.x()) / 2
    cy = (p1.y() + p2.y()) / 2
    pixels = QImage(img)

    def drawEllipsePoint(x, y): # refer center at above
        setPixelColor(pixels, cx+x, cy+y, color)
        setPixelColor(pixels, cx-x, cy+y, color)
        setPixelColor(pixels, cx+x, cy-y, color)
        setPixelColor(pixels, cx-x, cy-y, color)
    rx = abs(p1.x()-p2.x()) / 2
    ry = abs(p1.y()-p2.y()) / 2
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

    return pixels

def drawNewCurve(img: QImage, points: list, mode: str, color: QColor) -> QImage:
    pixels = QImage(img)
    if mode == "BZ":
        #18 sample points, 4 control points
        samples = 18
        cof = [1, 3, 3, 1]
        
        res = []
        for s in range(samples):
            t = s / (samples - 1)
            tinv = 1 - t
            x = 0.0
            y = 0.0
            for i in range(4):
                fac = cof[i] * t ** i * tinv ** (3 - i)
                x += points[i].x() * fac
                y += points[i].y() * fac  
            res.append(QPoint(int(round(x)), int(round(y))))
        
        for i in range(samples - 1):
            pixels = drawNewLine(pixels,res[i], res[i+1], "BSH", color)

    else: 
        #Using Clamped B-spline curve
        n = 3 # n+1 control points, n intervals
        k = 3 # order 3
        samples = 30
        res = []
        
        #calculate knot vector, n + k + 1 in total
        u = [0, 0, 0, 0.5, 1, 1, 1]

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
                x += points[i].x() * fac
                y += points[i].y() * fac  
            res.append(QPoint(int(round(x)), int(round(y))))

        for i in range(samples - 1):
            pixels = drawNewLine(pixels,res[i], res[i+1], "BSH", color)
    
    return pixels

def drawBox(img: QImage, points: list) -> QImage:
    x1 = points[0].x()
    y1 = points[0].y()
    x2 = points[1].x()
    y2 = points[1].y()
    if x1 == x2 or y1 == y2:
        return img
    
    flag = 0
    color = Qt.black
    pixels = QImage(img)

    def nextStep(flag):
        flag = (flag + 1) % 6
        if flag < 3:
            color = Qt.black
        else:
            color = Qt.white
        return flag, color
    
    for x in range(x1, x2, (x2 - x1)//abs(x2 - x1)):
        setPixelColor(pixels, x, y1, color)
        setPixelColor(pixels, x, y2, color)
        flag, color  = nextStep(flag)
    
    for y in range(y1, y2, (y2 - y1)//abs(y2 - y1)):
        setPixelColor(pixels, x1, y, color)
        setPixelColor(pixels, x2, y, color)
        flag, color  = nextStep(flag)
    
    return pixels

def drawDot(img: QImage, point: QPoint) -> QImage:
    pixels = QImage(img)
    x = point.x()
    y = point.y()

    setPixelColor(pixels, x+1, y+1, Qt.black)
    setPixelColor(pixels, x+1, y-1, Qt.black)
    setPixelColor(pixels, x-1, y+1, Qt.black)
    setPixelColor(pixels, x-1, y-1, Qt.black)

    setPixelColor(pixels, x+2, y, Qt.black)
    setPixelColor(pixels, x-2, y, Qt.black)
    setPixelColor(pixels, x, y+2, Qt.black)
    setPixelColor(pixels, x, y-2, Qt.black)
    setPixelColor(pixels, x+1, y, Qt.white)
    setPixelColor(pixels, x-1, y, Qt.white)
    setPixelColor(pixels, x, y+1, Qt.white)
    setPixelColor(pixels, x, y-1, Qt.white)
    setPixelColor(pixels, x, y, Qt.white)

    return pixels

#############################################
#          Operation Commands               #
#############################################
def translate(points: list, dx: int, dy: int) -> list:
    newPoints = []
    for p in points:
        newPoints.append(QPoint(p.x()+dx, p.y()+dy))
    return newPoints

def rotate(points: list, rp: QPoint, bp: QPoint, tp: QPoint):
    # step1, calculate rotate angle
    _bpx = bp.x() - rp.x()
    _bpy = bp.y() - rp.y()
    _tpx = tp.x() - rp.x()
    _tpy = tp.y() - rp.y()

    def getAngle(x, y):
        if x == 0:
            if y >= 0:
                return math.pi/2
            else: return 3*math.pi/2
        else:
            theta = math.atan(y/x)
            if x < 0:
                theta += math.pi
            return theta

    rb = getAngle(_bpx, _bpy)
    rt = getAngle(_tpx, _tpy)

    r = rt - rb

    #rotate it!
    xr = rp.x()
    yr = rp.y()
    newPoints = []
    for p in points:
        x = p.x()
        y = p.y()
        newX = xr + (x - xr) * math.cos(r) - (y - yr) * math.sin(r)
        newY = yr + (x - xr) * math.sin(r) + (y - yr) * math.cos(r)
        newPoints.append(QPoint(newX, newY))
    return newPoints

def scale(points: list, fp: QPoint, s: float) -> list:
    newPoints = []
    xf = fp.x()
    yf = fp.y()
    for p in points:
        newX = p.x() * s + xf * (1 - s)
        newY = p.y() * s + yf * (1 - s)
        newPoints.append(QPoint(newX, newY))
    return newPoints
        
def clip(cmds: list, p1: QPoint, p2:QPoint, mode: str) -> list:
    if p1.x() > p2.x():
        right = p1.x()
        left = p2.x()
    else:
        right = p2.x()
        left = p1.x()
    
    if p1.y() > p2.y():
        top = p1.y()
        bottom = p2.y()
    else:
        top = p2.y()
        bottom = p1.y()

    newcmds = []

    for cmd in cmds:
        if cmd["name"] == "DL":
            #get points info
            x1 = cmd["points"][0].x()
            y1 = cmd["points"][0].y()
            x2 = cmd["points"][1].x()
            y2 = cmd["points"][1].y()

            # clip
            if mode == "CC":
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
                        cmd["mode"] = "N/A"
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
                cmd["points"][0] = QPoint(x1, y1)
                cmd["points"][1] = QPoint(x2, y2)
            else: # mode == "CL"
                dx = x2 - x1
                dy = y2 - y1
                #处理平行的直线
                if (dx == 0 and not left <= x1 <= right) or (dy == 0 and not bottom <= y1 <= top):
                    cmd["mode"] = "N/A"

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

                    cmd["points"][0] = QPoint(x1, y1)
                    cmd["points"][1] = QPoint(x2, y2)

                else:
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
                        cmd["mode"] = "N/A"
                    
                    else:
                        getx = lambda u: x1 + u * (x2 - x1)
                        gety = lambda u: y1 + u * (y2 - y1)
                        cmd["points"][0] = QPoint(getx(umin), gety(umin))
                        cmd["points"][1] = QPoint(getx(umax), gety(umax))

        #handle N/A lines
        if cmd["name"] == "DL" and cmd["mode"] == "N/A":
            pass
        else:
            newcmds.append(cmd)
    return newcmds
                

#############################################
#             GUI: Picker                   #
#############################################
class primitivePicker(QDialog):
    selecting = pyqtSignal(int)

    def __init__(self, cmds, isRotate):
        super().__init__()
        self.resize(600,300)
        self.move(300, 300)
        self.setWindowTitle("Choose primitive...")

        columnCount = 4 # id name color control_point
        columnName = ['ID', 'Primitive Type', 'Color', 'Control Points']

        self.isRotate = isRotate
        self.picker = QTableWidget()
        self.picker.setColumnCount(columnCount) 
        self.picker.setRowCount(len(cmds))
        self.picker.setHorizontalHeaderLabels(columnName)
        self.picker.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.picker.setSelectionMode(QAbstractItemView.SingleSelection)

        for row in range(len(cmds)):
            cmd = cmds[row]
            name = ""
            if cmd["name"] == "DL":
                name = "Line"
            elif cmd["name"] == "DP":
                name = "Polygon"
            elif cmd["name"] == "DE":
                name = "Ellipse"
            elif cmd["name"] == "DC":
                name = "Curve"
            
            points = []
            for p in cmd["points"]:
                points.append((p.x(), p.y()))
                if len(points) == 4: break
            dots = "..." if len(cmd["points"]) > 4 else ""

            self.picker.setItem(row, 0, QTableWidgetItem(str(cmd["id"])))
            self.picker.setItem(row, 1, QTableWidgetItem(name))
            self.picker.setItem(row, 2, QTableWidgetItem(cmd["color"].name()))
            self.picker.setItem(row, 3, QTableWidgetItem(str(points) + dots))

        self.picker.resizeColumnsToContents()
        self.picker.resizeRowsToContents()

        self.confirm = QPushButton("OK", self)
        self.confirm.clicked.connect(self.onDoubleClick)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.picker) 
        self.layout.addWidget(self.confirm)
        self.setLayout(self.layout) 

        self.picker.clicked.connect(self.onClick)
        self.picker.doubleClicked.connect(self.onDoubleClick)

    def onClick(self):
        selection = []
        for currentQTableWidgetItem in self.picker.selectedItems():
            selection.append((currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text()))
        
        self.result = int(selection[0][2])
        self.selecting.emit(self.result)

    def onDoubleClick(self):
        if self.picker.selectedItems():
            selection = []
            for currentQTableWidgetItem in self.picker.selectedItems():
                selection.append((currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text()))
            
            self.result = int(selection[0][2])
            if self.isRotate and selection[1][2] == 'Ellipse':
                QMessageBox.information(self,"提示", "不允许对椭圆进行旋转操作！", QMessageBox.Yes)
            else: self.accept()

    def getResult(self):
        return self.result


#############################################
#             GUI: Main Window              #
#############################################
class PainterMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init()
    
    def init(self):
        self.setWindowIcon(QIcon("paint.ico"))

        self.posIndicator = QLabel("Coord",self)
        self.posIndicator.move(50,50)
        self.posIndicator.setFixedWidth(100)

        self.height = 600
        self.width = 800
        self.color = QColor(0, 0, 0)
        
        self.resize(self.width, self.height)
        self.move(300, 300)
        self.img = QImage(self.width, self.height, QImage.Format_RGB32)
        self.img.fill(Qt.white)
        self.tmpimg = QImage(self.img)

        self.idCount = 0

        self.status = "NONE"
        self.points = []
        self.mousePos = []
        self.cmds = []
        self.box = []
        self.dot = []
        self.choosing = {}

        menubar = self.menuBar()

        resetCanvasAction = QAction("&resetCanvas",self)
        resetCanvasAction.triggered.connect(self.resetCanvas)
        saveCanvasAction = QAction("&saveCanvas",self)
        saveCanvasAction.triggered.connect(self.saveCanvas)

        canvasMenu = menubar.addMenu("&Canvas")
        canvasMenu.addAction(resetCanvasAction)
        canvasMenu.addAction(saveCanvasAction)

        drawNewLineDDA = QAction("&DDA",self)
        drawNewLineDDA.name = "DLDDA"
        drawNewLineDDA.triggered.connect(self.DRAW)

        drawNewLineBresenham = QAction("&Bresenham",self)
        drawNewLineBresenham.name = "DLBSH"
        drawNewLineBresenham.triggered.connect(self.DRAW)

        drawPolygonDDA = QAction("&DDA",self)
        drawPolygonDDA.name = "DPDDA"
        drawPolygonDDA.triggered.connect(self.DRAW)

        drawPolygonBresenham = QAction("&Bresenham",self)
        drawPolygonBresenham.name = "DPBSH"
        drawPolygonBresenham.triggered.connect(self.DRAW)

        drawEllipse = QAction("&Ellipse",self)
        drawEllipse.name = "DE"
        drawEllipse.triggered.connect(self.DRAW)

        drawCurveBezier = QAction("&Bezier",self)
        drawCurveBezier.name = "DCBZ"
        drawCurveBezier.triggered.connect(self.DRAW)

        drawCurveBspline = QAction("&B-spline",self)
        drawCurveBspline.name = "DCBS"
        drawCurveBspline.triggered.connect(self.DRAW) 

        drawMenu = menubar.addMenu("&Drawing")
        drawNewLineMenu = drawMenu.addMenu("&Line")
        drawNewLineMenu.addAction(drawNewLineDDA)
        drawNewLineMenu.addAction(drawNewLineBresenham)
        drawPolygonMenu = drawMenu.addMenu("&Polygon")
        drawPolygonMenu.addAction(drawPolygonDDA)
        drawPolygonMenu.addAction(drawPolygonBresenham)
        drawMenu.addAction(drawEllipse)
        drawCurveMenu = drawMenu.addMenu("&Curve")
        drawCurveMenu.addAction(drawCurveBezier)
        drawCurveMenu.addAction(drawCurveBspline)

        oprTranslate = QAction("&Translate", self)
        oprTranslate.name = "T"
        oprTranslate.triggered.connect(self.OPR)
        
        oprRotate = QAction("&Rotate", self)
        oprRotate.name = "R"
        oprRotate.triggered.connect(self.OPR)

        oprScale = QAction("&Scale", self)
        oprScale.name = "S"
        oprScale.triggered.connect(self.OPR)

        oprClipCohen = QAction("&Cohen-Sutherland", self)
        oprClipCohen.name = "CC"
        oprClipCohen.triggered.connect(self.CLIP)

        oprClipLiang = QAction("&Liang-Barsky", self)
        oprClipLiang.name = "CL"
        oprClipLiang.triggered.connect(self.CLIP)
        
        oprMenu = menubar.addMenu("&Operations")
        oprMenu.addAction(oprTranslate)
        oprMenu.addAction(oprRotate)
        oprMenu.addAction(oprScale)
        oprClipMenu = oprMenu.addMenu("&Clip")
        oprClipMenu.addAction(oprClipCohen)
        oprClipMenu.addAction(oprClipLiang)

        pickColor = QAction("&Color", self)
        pickColor.triggered.connect(self.pickColor)

        menubar.addAction(pickColor)


    def mousePressEvent(self, e):
        self.posIndicator.setText("{},{}".format(e.x(),e.y()))
        if e.button() == Qt.LeftButton:
            self.pressHandler(e.pos())

    def mouseMoveEvent(self, e):
        self.posIndicator.setText("{},{}".format(e.x(),e.y()))
        self.moveHandler(e.pos())

    def mouseReleaseEvent(self, e):
        self.posIndicator.setText("{},{}".format(e.x(),e.y()))
        if e.button() == Qt.LeftButton:
            self.releaseHandler(e.pos())

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Shift:
            self.shift = True

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Shift:
            self.shift = False

    def resetCanvas(self):
        width, wok = QInputDialog.getInt(self, '重置画布', '输入画布宽度：', 800, 100, 1000)
        if wok:
            height, hok = QInputDialog.getInt(self, '重置画布', '输入画布高度：', 600, 100, 1000)
            if hok:
                self.height = height
                self.width = width
                
                self.resize(self.width, self.height)
                self.img = QImage(self.width, self.height, QImage.Format_RGB32)
                self.img.fill(Qt.white)
                self.tmpimg = QImage(self.img)

                self.status = "NONE"
                self.points = []
                self.cmds = []


    def saveCanvas(self):
        fname, _ = QFileDialog.getSaveFileName(self, '保存文件', '', '位图 (*.bmp)')
        if fname:
            self.img.save(fname)
    
    def DRAW(self):
        if self.status == "NONE":
            self.status = self.sender().name
            self.points = []
            #start drawing, waiting mouse event...

    def OPR(self):
        if self.status != "NONE":
            return

        if self.cmds:
            isRotate = "R" == self.sender().name
            self.pt = primitivePicker(self.cmds, isRotate)
            self.pt.selecting.connect(self.updateSelecting)
            if self.pt.exec_():
                for cmd in self.cmds:
                    if cmd["id"] == self.pt.getResult():
                        self.choosing = cmd
                        break
                self.status = self.sender().name
                #start operating, waiting mouse event...
            else:
                self.box = []
                self.draw()
        else:
            QMessageBox.information(self,"提示", "当前没有可供操作的图元！", QMessageBox.Yes)

    def updateSelecting(self, id):
        for cmd in self.cmds:
            if cmd["id"] == id:
                self.box = getBoxPoint(cmd["points"])
                self.draw()
                break

    def CLIP(self):
        if self.status == "NONE":
            self.status = self.sender().name

    def pickColor(self):
        self.color = QColorDialog.getColor()

    def pressHandler(self, pos):
        #draw
        if self.status in ["DLDDA", "DLBSH", "DE"]:
            self.points.append(pos)
        elif self.status in ["DPDDA", "DPBSH"]:
            if self.points: # have previous point
                self.tmpimg = drawNewLine(self.img, self.points[-1], pos, self.status[2:], self.color)
                self.update()
            else:
                self.points.append(pos)
        elif self.status in ["DCBZ", "DCBS"]:
            if len(self.points) == 0: # first press
                self.points.append(pos)
            if len(self.points) == 2: # first control point
                self.cmds = self.cmds[:-1]
                self.draw()
                self.tmpimg = drawNewCurve(self.img, [self.points[0], pos, pos, self.points[-1]], self.status[2:], self.color)
                self.update()
            if len(self.points) == 3: # second control point
                self.cmds = self.cmds[:-1]
                self.draw()
                self.tmpimg = drawNewCurve(self.img, [self.points[0], self.points[1], pos, self.points[-1]], self.status[2:], self.color)
                self.update()

        #opr
        elif self.status in ["T", "R", "S", "CC", "CL"]:
            self.mousePos = pos
            if self.status not in ["CC", "CL"]:
                self.points = self.choosing["points"]

    def moveHandler(self, pos):
        #draw
        if self.status in ["DLDDA", "DPDDA"]:
            self.tmpimg = drawNewLine(self.img, self.points[-1], pos, "DDA", self.color)
        elif self.status in ["DLBSH", "DPBSH"]:
            self.tmpimg = drawNewLine(self.img, self.points[-1], pos, "BSH", self.color)
        elif self.status in ["DE"]:
            self.tmpimg = drawNewEllipse(self.img, self.points[-1], pos, self.color)
        elif self.status in ["DCBZ","DCBS"]:
            if len(self.points) == 1: # two point curve would fall back to line
                self.tmpimg = drawNewLine(self.img, self.points[-1], pos, "BSH", self.color)
            elif len(self.points) == 2:
                self.tmpimg = drawNewCurve(self.img, [self.points[0], pos, pos, self.points[-1]], self.status[2:], self.color)
            elif len(self.points) == 3:
                self.tmpimg = drawNewCurve(self.img, [self.points[0], self.points[1], pos, self.points[-1]], self.status[2:], self.color)
        
        # opr
        elif self.status == "T":
            dx = pos.x() - self.mousePos.x()
            dy = pos.y() - self.mousePos.y()
            self.choosing["points"] = translate(self.points, dx, dy)
            self.box = getBoxPoint(self.choosing["points"])
            self.draw()
        elif self.status == "R":
            if self.dot:
                self.box = []
                self.choosing["points"] = rotate(self.points, self.dot[0], self.mousePos, pos) # rotate center, base point, target point
                self.draw()
        elif self.status in ["CC", "CL"]:
            self.box = [self.mousePos, pos]
            self.draw()

        self.update()

    def releaseHandler(self, pos):
        
        if self.status == "NONE":
            return

        # draw() would be called after all ifs

        #opr
        if self.status == "T":
            if pos == self.mousePos: # can drag at anytime if not clicking
                self.status = "NONE"
                self.box = []

        elif self.status == "R":
            if not self.dot:
                self.dot = [pos]
            else:
                self.status = "NONE"
                self.dot = []
                self.box = []
        
        elif self.status == "S":
            def scaling(value):
                self.choosing["points"] = scale(self.points, self.mousePos, value)
                self.box = getBoxPoint(self.choosing["points"])
                self.draw()

            def resetScale():
                self.choosing["points"] = self.points

            def confirmScale():
                self.box = []
                self.dot = []
                self.status = "NONE"
                self.draw()

            self.dot = [pos]
            self.getScale = QInputDialog()
            self.getScale.setLabelText("输入缩放倍数(0.1 ~ 5.0):")
            self.getScale.setWindowTitle("倍数选择")
            self.getScale.setCancelButtonText("取消")
            self.getScale.setOkButtonText("确定")
            self.getScale.setInputMode(QInputDialog.DoubleInput)
            self.getScale.setDoubleMinimum(0.1)
            self.getScale.setDoubleMaximum(5.0)
            self.getScale.setDoubleValue(1.0)
            self.getScale.setDoubleStep(0.1)
            self.getScale.doubleValueChanged.connect(scaling)
            self.getScale.accepted.connect(confirmScale)
            self.getScale.rejected.connect(resetScale)
            self.getScale.show()

        elif self.status in ["CC", "CL"]:
            self.cmds = clip(self.cmds, self.mousePos, pos, self.status)
            self.box = []
            self.status = "NONE"

        #draw
        elif self.status[:2] == "DL":
            self.status = "NONE"
            if pos != self.points[0]:
                self.points.append(pos)
                self.cmds.append({
                    "name":"DL", 
                    "id": self.idCount,
                    "mode": self.status[2:], # DDA or BSH
                    "points": deepcopy(self.points), 
                    "color": self.color
                })
                self.idCount += 1
        
        elif self.status[:2] == "DP":
            # close the polygon if double clicked or points closed
            if pos == self.points[-1] or tooClose(pos, self.points[0]): 
                if len(self.points) != 1: #in case of single point
                    self.cmds = self.cmds[:-1] # pop the temp polygon
                self.status = "NONE"
                self.points.append(self.points[0]) # close it
                self.cmds.append({
                    "name": "DP",
                    "id": self.idCount,
                    "mode": self.status[2:],
                    "points": deepcopy(self.points),
                    "color": self.color
                })
                self.idCount += 1
            # add a temp draw command if not closed yet
            else:
                if len(self.points) != 1: #in case of single point
                    self.cmds = self.cmds[:-1] # pop the temp polygon
                self.points.append(pos)
                self.cmds.append({
                    "name": "DP",
                    "mode": self.status[2:],
                    "points": deepcopy(self.points),
                    "color": self.color,
                })
        elif self.status == "DE":
            self.status = "NONE"
            if pos != self.points[0]:
                self.points.append(pos)
                self.cmds.append({
                    "name": "DE",
                    "id": self.idCount,
                    "points": deepcopy(self.points),
                    "color": self.color,
                })
                self.idCount += 1
        elif self.status[:2] == "DC":
            if len(self.points) == 1:
                if pos != self.points[0]:
                    self.points.append(pos)
                    self.cmds.append({
                        "name": "DC",
                        "mode": self.status[2:],
                        "points": [self.points[0]]+[pos]*3,
                        "color": self.color,
                    })
                else:
                    self.status = "NONE"
            elif len(self.points) == 2:
                self.points = [self.points[0], pos, self.points[1]]
                self.cmds.append({
                    "name": "DC",
                    "mode": self.status[2:],
                    "points": self.points[:1] + [pos]*2 + self.points[-1:],
                    "color": self.color
                })
            # this is the only case that adds a draw cmd
            elif len(self.points) == 3:
                self.points = self.points[:2] + [pos] + self.points[-1:]
                self.cmds.append({
                    "name": "DC",
                    "id": self.idCount,
                    "mode": self.status[2:],
                    "points": self.points,
                    "color": self.color
                })
                self.idCount += 1
                self.status = "NONE"

        self.draw()
            
    def draw(self):
        self.img.fill(Qt.white) # reset the canvas and draw all components
        for cmd in self.cmds:
            name = cmd["name"]
            if name == "DL":
                self.img = drawNewLine(self.img, cmd["points"][0], cmd["points"][1], cmd["mode"], cmd["color"])
            elif name == "DP":
                self.img = drawNewPolygon(self.img, cmd["points"], cmd["mode"], cmd["color"])
            elif name == "DE":
                self.img = drawNewEllipse(self.img, cmd["points"][0], cmd["points"][1], cmd["color"])
            elif name == "DC":
                self.img = drawNewCurve(self.img, cmd["points"], cmd["mode"], cmd["color"])

        if self.box:
            self.img = drawBox(self.img, self.box)
        if self.dot:
            self.img = drawDot(self.img, self.dot[0]) # recv QPoint

        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.status in ["NONE", "T", "S", "R", "CC", "CL"]:
            qp.drawImage(0, 0, self.img)
        else:
            qp.drawImage(0, 0, self.tmpimg)
        qp.end()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pm = PainterMain()
    pm.setWindowTitle("KDraw GUI")
    pm.show()

    sys.exit(app.exec_())