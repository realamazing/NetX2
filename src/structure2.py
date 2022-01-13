from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math
import json
import configparser

Filter = [.4,.7,.8,.9]

config = configparser.ConfigParser()
config.read('.config/config.ini')
with open(config['theme']['themefile'], "r") as jsonfile:
    style = json.load(jsonfile)['graph']
    jsonfile.close()

class Entity(QtWidgets.QGraphicsItem):
    def __init__(self,text,popularity = 1,_type = 0,selType = 'none'):
        super(Entity,self).__init__()
        #self.setCacheMode(self.DeviceCoordinateCache)
        self.setZValue(1)
        self.depthPos = 1
        self.text = text
        self.type = _type
        self.selType = selType
        self.popularity = popularity
        
        self.setRect(QRectF(-50,-50,100,100))
        
        self.setFlags(self.ItemIsMovable)

        self.children = [] #"destinations"
        self.ancestors = [] # "sources"

        self.buildPath()
        
        self.anim = QTimeLine()
        self.anim.setUpdateInterval(10)
        self.anim.setEasingCurve(QEasingCurve(0))
        self.anim.frameChanged.connect(self.rotation)
        self.anim.finished.connect(self.rotationFinished)

        self.setStyle(self.type,self.selType)
        
        self.font = QFont("Yu Gothic",5)
        self.pen = QPen()
        self.outlinePen = QPen()
        self.findFont()

        self.updatePopularity()
    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        for child in self.children:
            if self in child.sources:
                child.chainUpdate()
        for ancestor in self.ancestors:
            if self in ancestor.destinations:
                ancestor.chainUpdate()
        if self in self.scene().ui.detailView.items:
            self.scene().ui.detailView.showItems()
        return 
    def setText(self,text):
        self.text = text
        self.findFont()
        self.update()
    def shape(self) -> QtGui.QPainterPath:
        return self.path
    def boundingRect(self) -> QtCore.QRectF:
        r = QRectF(self.ellipseRect)
        r.adjust(-10,-10,10,10) # account for outlines
        return r
    def updatePopularity(self):
        childs = len([i for i in self.children if i.type != 3])

        a = .9 #rate
        b = 10 # max size

        self.popularity = -a**(childs+math.log(b)/math.log(a))+b

        self.zoomCutoff = (-.7)/(self.popularity+1)+1

        rect = QRectF(-50,-50,100,100) # default 100x100
        rect.adjust(-self.popularity*10,-self.popularity*10,self.popularity*10,self.popularity*10)

        self.prepareGeometryChange()
        self.setRect(rect)
        self.buildPath()
        self.findFont()
        for ancestor in self.ancestors:
            if type(ancestor) == Relationship:
                ancestor.buildPath() # account for increase in size in connecting relationships
    def setRect(self,rect):
        self.ellipseRect = rect
    def rect(self):
        return self.ellipseRect
    def inRect(self):
        if self.type == 0:
            rad = self.rect().width()/2
            rad = rad * math.sqrt(2)
            size = QSizeF(rad,rad)
            rect = QRectF(QPointF(0,0),size)
            rect.moveCenter(self.rect().center())
        else:
            rect = self.rect()
        return rect
    def attachmentPos(self):
        return self.scenePos()
    def findFont(self):
        step = 15
        self.font.setPointSize(step)
        while step > 1:
            r = QFontMetricsF(self.font).boundingRect(self.inRect(),Qt.AlignCenter|Qt.TextWordWrap,self.text)
            if (r.width() > self.inRect().size().width()) or (r.height() > self.inRect().size().height()):
                if int(self.font.pointSizeF()-step) > 0:
                    self.font.setPointSize(int(self.font.pointSizeF()-step))
            else: #minimum font
                self.font.setPointSize(int(self.font.pointSizeF()+step))
            step = step/1.25
    def setAncestors(self,ancestors):
        preAncestors = self.ancestors
        self.ancestors = []
        self.ancestors = [] + ancestors
        for ancestor in preAncestors: # for all of the items previous ancestors
            if ancestor not in self.ancestors: # if ancestor is not in new ancestors
                if self in ancestor.children: # and self is in ancestors children
                    ancestor.children.remove(self) # remove the link from that ancestor
            else: # if ancestor is in new selection
                if self not in ancestor.children: # if self isnt already a child
                    ancestor.children.append(self) # add self as child
            ancestor.buildPath() 
    def setChildren(self,children):
        preChildren = self.children
        self.children = []
        self.children = [] + children
        for child in preChildren:
            if child not in self.children:
                if self in child.ancestors:
                    child.ancestors.remove(self)
            else:
                if self not in child.ancestors:
                    child.ancestors.append(self)
            child.buildPath()
        self.updatePopularity()
    def setStyle(self,_type=-1,selType=-1):
        if selType == -1:
            selType = self.selType
        if _type == -1:
            _type = self.type
        if _type != -1:
            self.type = _type
            pen = QPen()
            col = QColor(style['entity'][_type][selType]['color'])
            pen.setColor(col)
            pen.setWidth(style['entity'][_type][selType]['weight'])
            pen.setDashPattern(style['entity'][_type][selType]['border'])
            self.pen = pen
        if selType != -1:
            self.selType = selType
            Open = QPen()
            Ocol = QColor(style['entity'][_type][selType]['Ocolor'])
            Open.setColor(Ocol)
            Open.setWidth(style['entity'][_type][selType]['Oweight'])
            Open.setDashPattern(style['entity'][_type][selType]['Oborder'])
            self.outlinePen = Open
        self.shape = style['entity'][_type][selType]['shape']
        if style['entity'][_type][selType]['anim']:
            self.buildPath()
            self.anim.stop()
            self.anim.setDuration(int(self.outlinePath.length()*100))
            self.anim.setFrameRange(0,int(self.outlinePath.length()*100))
            self.anim.start()
        else:
            self.anim.stop()
    def rotation(self,x):
        self.outlinePen.setDashOffset(x/100)
        self.update()
    def rotationFinished(self):
        self.anim.start() # loop
    def buildPath(self):
        self.path = QPainterPath()
        if self.shape == 'round':
            self.path.addEllipse(self.ellipseRect)
        elif self.shape == 'square':
            self.path.addRect(self.ellipseRect)
        self.outlinePath = QPainterPath(self.path)
    def paint(self, painter: QtGui.QPainter, option, widget) -> None:
        # ---------- draw outline -------
        painter.setPen(self.outlinePen)
        painter.drawPath(self.outlinePath)
        #---------- draw path -----------
        painter.setPen(self.pen)
        painter.setBrush(QBrush(Qt.black))
        painter.drawPath(self.path)
        if self.scene().ui.mainView.currZoom() < self.zoomCutoff:
            painter.setFont(self.font)
            painter.drawText(self.rect(),Qt.AlignCenter|Qt.TextWordWrap,self.text)
class Relationship(QtWidgets.QGraphicsItem):
    def __init__(self,sources,destinations,text='',_type = 0, selType = 'none') -> None:
        super(Relationship,self).__init__()
        self.text = text
        self.type = _type
        self.selType = selType
        self.arrowType = 'direct'

        self.sources = sources #ancestors that belong to this relationship
        self.destinations = destinations #children that belong to this relationship

        self.children = [] # destinations *and* children that are not apart of this relationship
        self.ancestors = [] # sources *and* ancestors that are not apart of this ancestors

        self.font = QFont("Yu Gothic",5)
        self.pen = QPen()
        self.outlinePen = QPen()
        self.brush = QBrush()

        self.textRect = QRectF(-30,-30,60,30)
        self.findFont()

        self.sourcePaths = []
        self.destinationPaths = []

        self.depthPos = 0

        self.anim = QTimeLine()
        self.anim.setUpdateInterval(10)
        self.anim.setEasingCurve(QEasingCurve(0))
        self.anim.frameChanged.connect(self.rotation)
        self.anim.finished.connect(self.rotationFinished)

        if self.sources != [] or self.destinations != []:
            #self.setAncestors(self.sources)
            #self.setChildren(self.destinations)
            self.setSources(self.sources)
            self.setDestinations(self.destinations)
            self.buildPath()
    def sortDepth(self): #for saving
        d = min([e.depthPos for e in self.sources + self.destinations])
        d -= 1
        self.depthPos = d
    def stack(self):
        Zvals = [i.zValue() for i in self.ancestors]
        self.setZValue(min(Zvals) - 1)
        if self.arrowType not in ['undirect','none']:
            for i in self.children:
                if type(i) == Relationship and i.zValue() != 0:
                    i.stack()
    def attachmentPos(self):
        return self.anchorPoint
    def attachmentAngle(self):
        return self.anchorPointAngle
    def chainUpdate(self): # updates all dependents
        self.buildPath()
        for child in self.children:
            if type(child) == Relationship:
                if self in child.sources:
                    child.chainUpdate()
        for ancestor in self.ancestors:
            if type(ancestor) == Relationship:
                if self in ancestor.destinations:
                    ancestor.chainUpdate()
    def setSources(self,sources): # requires a buildPath after invocation
        # handle sources
        preSources = self.sources
        self.sources = []
        self.sources = [] + sources
        for source in preSources+self.sources: #  for all sources (new and old)
            if source not in self.sources: # if souce is not in new sources
                if source in self.ancestors: # and if source is in ancestors
                    self.ancestors.remove(source) # remove the source from ancestors
                if self in source.children: #furthermore, if self is in source children
                    source.children.remove(self) # remove self from children
            else: # if source is in new sources
                if source not in self.ancestors: # and source isnt already in ancestors
                    self.ancestors.append(source) # add to sources
                if self not in source.children: # furthermore, if self is not in source children
                    source.children.append(self) # add self
            if type(source) == Entity:
                source.updatePopularity()
            source.buildPath()
    def setDestinations(self,destinations): # requires a buildPath after invocation
        preDestinations = self.destinations
        self.destinations = []
        self.destinations = [] + destinations
        for destination in preDestinations + self.destinations:
            if destination not in self.destinations:
                if destination in self.children:
                    self.children.remove(destination)
                if self in destination.ancestors:
                    destination.ancestors.remove(self)
            else:
                if destination not in self.children:
                    self.children.append(destination)
                if self not in destination.ancestors:
                    destination.ancestors.append(self)
            if type(destination) == Entity:
                destination.updatePopularity()
            destination.buildPath()
    def setAncestors(self,ancestors): # requires a buildPath after invocation
        preAncestors = self.ancestors
        self.ancestors = []
        self.ancestors = [] + ancestors
        for ancestor in preAncestors + self.ancestors: # for all of the items previous ancestors
            if ancestor not in self.ancestors: # if ancestor is not in new ancestors
                if self in ancestor.children: # and self is in ancestors children
                    ancestor.children.remove(self) # remove the link from that ancestor
            else: # if ancestor is in new selection
                if self not in ancestor.children: # if self isnt already a child
                    ancestor.children.append(self) # add self as child
            if type(ancestor) == Entity:
                ancestor.updatePopularity()
            ancestor.buildPath() 
    def setChildren(self,children): # requires a buildPath after invocation
        preChildren = self.children
        self.children = []
        self.children = [] + children
        for child in preChildren + self.children:
            if child not in self.children:
                if self in child.ancestors:
                    child.ancestors.remove(self)
            else:
                if self not in child.ancestors:
                    child.ancestors.append(self)
            if type(child) == Entity:
                child.updatePopularity()
            child.buildPath()
    def buildPath(self):
        if len(self.sources) > 1 or len(self.destinations) > 1: #for relationships with multiple curves
            sm_p = QPointF(0,0)
            for source in self.sources:
                sm_p = sm_p + source.attachmentPos()
            sm_p = sm_p/len(self.sources) # average of all sources

            em_p = QPointF(0,0)
            for destination in self.destinations:
                em_p = em_p + destination.attachmentPos()
            em_p = em_p/len(self.destinations) # average of all end points

            self.centerLine = QLineF(sm_p,em_p)
            self.anchorPoint = self.centerLine.center()
            self.anchorPointAngle = self.centerLine.angle()

            self.sourcePaths = []
            for source in self.sources:
                s = source.attachmentPos()
                e = self.anchorPoint
                if type(source) == Relationship: #if path starts with relationship use cubic
                    c1 = QLineF.fromPolar(source.centerLine.length()/2,source.attachmentAngle()).p2() + s
                    c2 = QLineF.fromPolar(self.centerLine.length()/2,self.anchorPointAngle + 180).p2() + e
                    p = QPainterPath(s)
                    p.cubicTo(c1,c2,e)
                    p.translate(-self.anchorPoint)
                    self.sourcePaths.append(p)
                else: # if path starts with entity use quad
                    c1 = QLineF.fromPolar(self.centerLine.length()/2,self.anchorPointAngle + 180).p2() + e
                    p = QPainterPath(s)
                    p.quadTo(c1,e)
                    p.translate(-self.anchorPoint)
                    self.sourcePaths.append(p)
            self.destinationPaths = []
            for destination in self.destinations:
                s = self.anchorPoint
                e = destination.attachmentPos()
                if type(destination) == Relationship: #if path ends with relationship use cubic
                    c1 = QLineF.fromPolar(self.centerLine.length()/2,self.anchorPointAngle).p2() + s
                    c2 = QLineF.fromPolar(destination.centerLine.length()/2,destination.attachmentAngle()+180).p2() + e
                    p = QPainterPath(s)
                    p.cubicTo(c1,c2,e)
                    p.translate(-self.anchorPoint)
                    self.destinationPaths.append(p)
                else: # if path ends with entity use quad
                    s = self.anchorPoint
                    e = destination.attachmentPos()
                    c1 = QLineF.fromPolar(self.centerLine.length()/2,self.anchorPointAngle).p2() + s
                    p = QPainterPath(s)
                    p.quadTo(c1,e)
                    p.translate(-self.anchorPoint)
                    self.destinationPaths.append(p)
        else: #---------------------------------Simple Relationships-----------------------------------------------------------------
            s = self.sources[0].attachmentPos()
            e = self.destinations[0].attachmentPos()
            self.centerLine = QLineF(s,e)

            p = QPainterPath(s)

            if type(self.sources[0]) == Relationship and type(self.destinations[0]) == Relationship: # R - R
                c1 = QLineF.fromPolar(self.sources[0].centerLine.length()/2,self.sources[0].attachmentAngle()).p2() + self.sources[0].attachmentPos()
                c2 = QLineF.fromPolar(self.destinations[0].centerLine.length()/2,self.destinations[0].attachmentAngle() + 180).p2() + self.destinations[0].attachmentPos()
                p.cubicTo(c1,c2,e)
            elif type(self.sources[0]) == Entity and type(self.destinations[0]) == Relationship:    
                c1 = QLineF.fromPolar(self.destinations[0].centerLine.length()/2,self.destinations[0].attachmentAngle() + 180).p2() + self.destinations[0].attachmentPos()
                p.quadTo(c1,e)
            elif type(self.sources[0]) == Relationship and type(self.destinations[0]) == Entity:
                c1 = QLineF.fromPolar(self.sources[0].centerLine.length()/2,self.sources[0].attachmentAngle()).p2() + self.sources[0].attachmentPos()
                p.quadTo(c1,e)
            elif type(self.sources[0]) == Entity and type(self.destinations[0]) == Entity:
                c1 = self.centerLine.center()
                p.quadTo(c1,e)
            self.anchorPoint = p.pointAtPercent(.5)
            self.anchorPointAngle = p.angleAtPercent(.5)
            p.translate(-self.anchorPoint)
            self.sourcePaths = [p]
            self.destinationPaths = [p]
        # ----- combine ------
        self.setPos(self.anchorPoint)
        self.prepareGeometryChange()
        self.path = QPainterPath()
        ps = []
        for path in self.destinationPaths + self.sourcePaths:
            if path not in ps:
                self.path.addPath(path)
            ps.append(path)
        #------ arrow paths -----
        self.arrowPath = QPainterPath()
        if self.arrowType != 'none':
            for i,destination in enumerate(self.destinations):
                if type(destination) == Relationship:
                    rad = 0
                    arrowAngle = 15
                elif destination.shape == 'round': # if round
                    rad = destination.rect().width()/2
                    arrowAngle = 30
                else: # if square
                    angle = self.destinationPaths[i].angleAtPercent(.9) + 180
                    wid = destination.rect().width()/2
                    rad = min(abs(1/math.cos(math.radians(angle))),abs(1/math.sin(math.radians(angle)))) * wid
                    arrowAngle = 30
                t = self.destinationPaths[i].percentAtLength(self.destinationPaths[i].length()-rad)
                point = self.destinationPaths[i].pointAtPercent(t)
                angle = self.destinationPaths[i].angleAtPercent(t) + 180
                p1 = QLineF.fromPolar(20,angle+arrowAngle).p2() + point
                p2 = QLineF.fromPolar(20,angle-arrowAngle).p2() + point
                self.arrowPath.addPolygon(QPolygonF([point,p1,p2,point]))
            if self.arrowType == 'undirect':
                for i,source in enumerate(self.sources):
                    if type(source) == Relationship:
                        rad = 0
                        arrowAngle = 15
                    elif source.shape == 'round': # if round
                        rad = source.rect().width()/2
                        arrowAngle = 30
                    else: # if square
                        angle = self.sourcePaths[i].angleAtPercent(.1)
                        wid = source.rect().width()/2
                        rad = min(abs(1/math.cos(math.radians(angle))),abs(1/math.sin(math.radians(angle)))) * wid
                        arrowAngle = 30
                    t = self.sourcePaths[i].percentAtLength(rad)
                    point = self.sourcePaths[i].pointAtPercent(t)
                    angle = self.sourcePaths[i].angleAtPercent(t)
                    p1 = QLineF.fromPolar(20,angle+arrowAngle).p2() + point
                    p2 = QLineF.fromPolar(20,angle-arrowAngle).p2() + point
                    self.arrowPath.addPolygon(QPolygonF([point,p1,p2,point]))

        # ------ text path ------------
        p = QPainterPath(self.anchorPoint)

        textWidth = QFontMetricsF(self.font).boundingRect(self.text).width()
        offset = QPointF((self.textRect.width() - textWidth)/2,0)
        p.addText(self.textRect.bottomLeft() + offset,self.font,self.text)
        #p.addRect(self.textRect)

        angle = -self.anchorPointAngle
        if angle < -90 and angle > -270:
            angle += 180
        transform = QTransform()
        transform.translate(self.textRect.center().x(),self.textRect.bottom()-5)
        transform.rotate(angle,2)
        transform.translate(-self.textRect.center().x(),-self.textRect.bottom()-5)

        #self.textPath.translate(-self.anchorPoint)
        self.textPath = QPainterPath()
        self.textPath.addPath(transform.map(p))
        # ----- bounding path, includes all path (NOT FOR DRAWING) -----
        self.boundingPath = QPainterPath()
        self.boundingPath.addPath(self.path)
        self.boundingPath.addPath(self.arrowPath)
        self.boundingPath.addPath(self.textPath)
        #r = QRectF(self.textRect)
        #r.adjust(-5,-5,5,5)
        #self.boundingPath.addRect(r)
        self.outlinePath = QPainterPath(self.boundingPath)
    def findFont(self):
        step = 15
        self.font.setPointSize(step)
        while step > 1:
            #r = QFontMetricsF(self.font).boundingRect(self.textRect,Qt.AlignCenter|Qt.TextWordWrap,self.text)
            r = QFontMetricsF(self.font).boundingRect(self.text)
            if (r.width() > self.textRect.size().width()) or (r.height() > self.textRect.size().height()):
                if int(self.font.pointSizeF()-step) > 0:
                    self.font.setPointSize(int(self.font.pointSizeF()-step))
            else: #minimum font
                self.font.setPointSize(int(self.font.pointSizeF()+step))
            step = step/1.25
    def setStyle(self,_type=-1,selType=-1):
        if _type == -1:
            _type = self.type
        if selType == -1:
            selType = self.selType
        if _type != -1:
            self.type = _type
            pen = QPen()
            col = QColor(style['relationship'][_type][selType]['color'])
            pen.setColor(col)
            pen.setWidth(style['relationship'][_type][selType]['weight'])
            pen.setDashPattern(style['relationship'][_type][selType]['border'])
            self.brush = QBrush(col)
            self.pen = pen
        if selType != -1:
            self.selType = selType
            Open = QPen()
            Ocol = QColor(style['relationship'][_type][selType]['Ocolor'])
            Open.setColor(Ocol)
            Open.setWidth(style['relationship'][_type][selType]['Oweight'])
            Open.setDashPattern(style['relationship'][_type][selType]['Oborder'])
            self.outlinePen = Open

        newType = style['relationship'][_type][selType]['arrow']
        if self.arrowType in ['direct'] and newType in ['undirect','none']: # changing from direct to undirect
            self.toInDirect()
        elif self.arrowType in ['undirect','none'] and newType in ['direct']: # changing from undirect to direct
            self.toDirect()
        self.arrowType = newType
        # anim
        if style['relationship'][_type][selType]['anim']:
            self.buildPath()
            self.anim.stop()
            self.anim.setDuration(int(self.outlinePath.length()*100))
            self.anim.setFrameRange(0,int(self.outlinePath.length()*100))
            self.anim.start()
        else:
            self.anim.stop()
    def toInDirect(self):
        items = []
        for i in self.sources + self.destinations:
            if i not in items:
                items.append(i)
        items = []
        [items.append(x) for x in self.sources + self.destinations if x not in items]
        ancestors = []
        [ancestors.append(x) for x in self.ancestors + items if x not in ancestors]
        children = []
        [children.append(x) for x in self.children + items if x not in children]
        self.setAncestors(ancestors)
        self.setChildren(children)
        for item in self.sources + self.destinations:
            children = []
            [children.append(x) for x in item.children + [self] if x not in children]
            ancestors = []
            [ancestors.append(x) for x in item.ancestors + [self] if x not in ancestors]
            item.setChildren(children)
            item.setAncestors(ancestors)
    def toDirect(self):
        children = []
        [children.append(x) for x in self.children if x not in children + self.destinations + self.sources]
        ancestors = []
        [ancestors.append(x) for x in self.ancestors if x not in ancestors + self.destinations + self.sources]
        self.setAncestors(self.sources + ancestors)
        self.setChildren(self.destinations + children)
    def rotation(self,x):
        self.outlinePen.setDashOffset(-x/100)
        self.update()
    def rotationFinished(self): # loop
        self.anim.start()
    def setText(self,text):
        self.text = text
        self.findFont()
        self.buildPath()
        #self.setStyle(-1,)
    def boundingRect(self) -> QtCore.QRectF:
        #rect = self.shape().boundingRect()
        rect = self.boundingPath.boundingRect()
        rect.adjust(-5,-5,5,5)# account for outline path
        return rect
    def rect(self):
        return self.boundingRect()
    def shape(self) -> QtGui.QPainterPath:
        pen = QPen()
        pen.setWidth(15) # bigger than weight and outline weight
        stroker = QPainterPathStroker(pen)
        path = stroker.createStroke(self.boundingPath)
        return path
    def paint(self, painter: QtGui.QPainter, option, widget) -> None:
        #----- outline -------
        painter.setPen(self.outlinePen)
        painter.drawPath(self.outlinePath)
        # ------ bezeir curve ---------
        painter.setPen(self.pen)
        painter.drawPath(self.path)
        # ------- arrow path ------
        painter.setBrush(QBrush(Qt.black))
        painter.drawPath(self.arrowPath)
        # --------- text path
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.brush)
        if self.scene().ui.mainView.currZoom() < .3:
            painter.drawPath(self.textPath)