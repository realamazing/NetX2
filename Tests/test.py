from os import path
from pickle import TRUE
import re
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem,QGraphicsScene,QGraphicsView, QStyleOptionGraphicsItem, QWidget
import numpy as np
import math
import pickle
import string
import random
import string

def pixmapFromItem(item):
    #pixmap = QPixmap(item.boundingRect().size().toSize())
    pixmap = QPixmap(100,100)
    pixmap.scaled(item.bb.size().width(),item.bb.size().height(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setPen(Qt.white)
    painter.setFont(item.font)
    opt = QStyleOptionGraphicsItem()
    #painter.setRenderHint(QPainter.Antialiasing)
    d = item.bb
   # d.adjust(-10,-10,10,10)
    #painter.translate(25,0)
    painter.drawText(d,Qt.AlignCenter|Qt.TextWrapAnywhere,item.text)
    #item.paint(painter,opt,QWidget())
    return pixmap

class glowEffect(QtWidgets.QGraphicsEffect):
    def __init__(self,item) -> None:
        super().__init__()
        self.color = QColor(255,255,255,255)
        self.extent = 4
        self.strength = 4
        self.blurRadius = 5
        self.item = item
    def setColor(self,value):
        self.color = value
    def setStrength(self,value):
        self.strength = value
        self.extent = math.ceil(value)
    def setBlurRadius(self,value):
        self.blurRadius = value
    def boundingRectFor(self, rect: QtCore.QRectF) -> QtCore.QRectF:
        return QRectF(
            rect.left() - self.extent,
            rect.top() - self.extent,
            rect.width() + 2 * self.extent,
            rect.height() + 2 * self.extent)
    def draw(self, painter: QtGui.QPainter) -> None:
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        source = self.sourcePixmap(Qt.LogicalCoordinates,mode=0)[0]
        #source = source.scaled(2, 2, Qt.IgnoreAspectRatio, Qt.SmoothTransformation);
        offset = self.sourcePixmap(Qt.LogicalCoordinates,mode=0)[1]
        #colorize = QtWidgets.QGraphicsColorizeEffect()
        glow = QPixmap()
        #colorize.setColor(self.color)
        #colorize.setStrength(self.strength)
        #glow = self.applyEffectToPixmap(source,colorize,0)

        blur = QtWidgets.QGraphicsBlurEffect()
        blur.setBlurRadius(self.blurRadius)
        glow = self.applyEffectToPixmap(glow,blur,self.extent)
        
        for _ in range(self.strength):
            painter.drawPixmap(offset - QPoint(self.extent,self.extent), glow)
        painter.drawPath(self.item.path)
        self.drawSource(painter)
    def applyEffectToPixmap(self,src,effect,extent):
        scene = QtWidgets.QGraphicsScene()
        item = QtWidgets.QGraphicsPixmapItem()
        item.setPixmap(src)
        item.setGraphicsEffect(effect)
        scene.addItem(item)
        size = src.size() + QSize(extent*2,extent*2)
        res = QPixmap(size.width(),size.height())
        res.fill(Qt.transparent)
        ptr = QPainter(res)
        scene.render(ptr,QRectF(),QRectF(-extent,-extent,size.width(),size.height()))
        return res

class rect(QGraphicsItem):
    def __init__(self) -> None:
        super().__init__()
        #self.setCacheMode(self.ItemCoordinateCache)
        self.text = ''.join(random.choices(string.ascii_uppercase + string.digits + ' ', k = random.randint(1,1)))
        self.font = QFont('Arial',5,0)
        self.path = QPainterPath()


        rect = QRectF(0,0,20,20)

        self.textpath = QPainterPath(QPointF(0,0))
        self.textpath.addText(rect.bottomLeft(),self.font,self.text)

        transform = QTransform()
        transform.translate(rect.center().x(),rect.center().y())
        transform.rotate(45,2)
        transform.translate(-rect.center().x(),-rect.center().y())

        #self.path.addPolygon(transform.map(QPolygonF(rect)))
        #self.path.addPolygon(QPolygonF(rect))
        self.path.addPath(transform.map(self.textpath))


        #self.path.addText(QPointF(0,0),self.font,self.text)
        self.bb = self.path.boundingRect()

        self.outline = QPainterPathStroker(QPen(Qt.red))
        self.outline.setWidth(.5)
        self.outlinePath = self.outline.createStroke(self.path)


        #self.bb.adjust(-10,-10,10,10)
        #self.textRect = QRectF(-30,-30,60,30)
        #self.bb = QFontMetricsF(self.font).boundingRect(self.textRect,Qt.AlignCenter|Qt.TextWordWrap,self.text)
        #self.bb = QRectF(-30,-30,60,30)
        #self.bb = QRectF(0,0,50,50)
        #print(self.bb)
        #self.bb.setBottomLeft(QPointF(0,0))
        
        #self.bb = QRectF(0,0,10,10)
        self.setPos(np.random.randint(0,1000),np.random.randint(0,1000))
        #self.piximap = pixmapFromItem(self)

        



        """
        self.path = QPainterPath(QPointF(0,0))
        self.path.quadTo(QPointF(10,2),QPointF(20,0))
        self.path.addEllipse(-10,-10,20,20)

        rect = QRectF(10,0,20,20)
        self.textpath = QPainterPath(QPointF(0,0))
        self.textpath.addText(rect.bottomLeft(),QFont("Yu Gothic",3),'test')

        transform = QTransform()
        transform.translate(rect.center().x(),rect.center().y())
        transform.rotate(45,2)
        transform.translate(-rect.center().x(),-rect.center().y())

        
        self.path.addPolygon(transform.map(QPolygonF(rect)))
        #self.path.addPolygon(QPolygonF(rect))
        self.path.addPath(transform.map(self.textpath))

        #self.path.addRect(QRectF(0,0,10,10))
        #self.path.addText(QPointF(0,0),QFont("Yu Gothic",5),'test')
        point = QPointF(20,0)
        p1 = QPointF(13,7)
        p2 = QPointF(14,-7)
        self.arrowPath = QPainterPath()
        self.arrowPath.addPolygon(QPolygonF([point,p1,p2]))
        self.arrowPath.closeSubpath()

        p = QPainterPath()
        p.addPath(self.path)
        p.addPath(self.arrowPath)
        self.combinedPath = p
        """
        #self.glow = glowEffect(self)
        #self.glow.setStrength(2)
        #self.glow.setBlurRadius(2)
        #self.setGraphicsEffect(self.glow)
        #self.glow.setEnabled(False)


    def mousePressEvent(self, event) -> None:
        self.setPos(np.random.randint(0,1000),np.random.randint(0,1000))
        return super().mousePressEvent(event)
    def boundingRect(self) -> QtCore.QRectF:
        return self.bb
    def paint(self, painter: QtGui.QPainter, option , widget) -> None:
        #print(f'{self.text}: paint event called')
        painter.setFont(self.font)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawPath(self.path)

        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.red)
        painter.drawPath(self.outlinePath)
        #painter.drawRect(self.boundingRect())
        
        #painter.drawPath(self.arrowPath)
        #text = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10000))
        #painter.drawText(QRectF(0,0,1000,1000),Qt.AlignCenter|Qt.TextWrapAnywhere,text)
        #painter.drawText(self.bb,Qt.AlignCenter|Qt.TextWrapAnywhere,self.text)
       # d = self.bb
        #d.adjust(-10,-10,10,10)
        #j = QRectF(0,0,50,50)
        #painter.drawPixmap(j,self.piximap,self.bb)
        #painter.drawRect(j)

class drawer(QGraphicsItem):
    def __init__(self,scene) -> None:
        super().__init__()
        self.scene = scene
        self.font = QFont('Yu Gothic',10)
    def boundingRect(self) -> QtCore.QRectF:
        return self.scene.sceneRect()
    def paint(self, painter: QtGui.QPainter, option, widget) -> None:
        painter.setFont(self.font)
        for entity in self.scene.entities:
            #QRectF().setTopLeft()
            painter.translate(entity.scenePos())
            painter.drawText(entity.bb,Qt.AlignCenter|Qt.TextWrapAnywhere,entity.text)
            painter.translate(-entity.scenePos())
class Scene(QtWidgets.QGraphicsScene):
    def __init__(self,ui):
        super(Scene,self).__init__()
        self.ui = ui
        #self.setBackgroundBrush(QBrush(Qt.black))
        self.selection = []
        self.sourceSelection = []
        self.destinationSelection = []
        self.setSceneRect(QRectF(0,0,1000,1000))
        self.addRect(self.sceneRect(),Qt.white)

        self.entities = []
        for _ in range(10000):
            j = rect()
            self.entities.append(j)
            self.addItem(j)

        #self.drawer = drawer(self)
        #self.addItem(self.drawer)

    
class MainViewport(QtWidgets.QGraphicsView):
    def __init__(self,parent,scene,ui):
        super(MainViewport,self).__init__(parent=parent)
        self.ui = ui
        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(False)
        self.setStyleSheet('border: solid 0px;')
        self.setRenderHint(QtGui.QPainter.Antialiasing,True)
        self.numScheduledScalings = 0
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == 2:
            self.oldPos = self.mapToScene(event.pos())
        return super().mousePressEvent(event)
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.buttons() == Qt.RightButton:       
            self.newPos = self.mapToScene(event.pos())
            delta = self.newPos - self.oldPos
            delta = delta
            self.translate(delta.x(),delta.y())
        return super().mouseMoveEvent(event)
    def wheelEvent(self, event):
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)
        numDegrees = event.angleDelta().y() / 8
        numSteps = numDegrees / 15
        self.numScheduledScalings += numSteps
        if self.numScheduledScalings * numSteps < 0:
            self.numScheduledScalings = numSteps
        self.eventPos = event.pos()
        self.oldPos = self.mapToScene(self.eventPos)

        anim = QTimeLine(350,self)
        anim.setUpdateInterval(20)
        anim.valueChanged.connect(self.scalingTime)
        anim.finished.connect(self.animFinished)
        anim.start()
    def scalingTime(self,x):
        factor = 1 + self.numScheduledScalings / 300
        self.scale(factor,factor)
        self.newPos = self.mapToScene(self.eventPos)
        delta = self.newPos - self.oldPos
        self.translate(delta.x(),delta.y())
    def animFinished(self):
        if self.numScheduledScalings > 0:
            self.numScheduledScalings -= 1
        else:
            self.numScheduledScalings += 1
class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('NetX2/Resources/main.ui', self) # Load the .ui file
        self.scene = Scene(self)
        self.mainView = MainViewport(self.MainContainer,self.scene,self) #make a viewport to see scene

        self.MainLayout.addWidget(self.mainView)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    sys.exit(app.exec_())