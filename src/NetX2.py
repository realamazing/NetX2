import configparser
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer
import sys
import string
import random
import datetime
import json
import re
import pickle
import os
from pympler.tracker import SummaryTracker
from pympler import muppy
import math
from filemanager import repair,SourcePath
repair()

from entryWidgets import EntryLine
from clickLabel import clickableLabel
from structure2 import Entity, Relationship
from nlu import nlp

tracker = SummaryTracker()

class Scene(QtWidgets.QGraphicsScene):
    def __init__(self,ui):
        super(Scene,self).__init__()
        self.ui = ui
        #bkgBrush = QBrush(QPixmap('NetX2/Resources/Icons/bkg2.jpg'))

        bkgBrush = QBrush(Qt.black)
        self.setBackgroundBrush(bkgBrush)
        self.selection = []
        self.sourceSelection = []
        self.destinationSelection = []
        self.accesoryPathsSelection = []
        self.setSceneRect(QRectF(-50000,-50000,100000,100000))

        self.nlp = nlp()

        self.entities = []
        self.relationships = []

        self.limitedView = False
        self.log = ['Started Net']
        #self.populate() # debug
    def populate(self):
        while len(self.entities) <= 1000:
            pos = QPoint(random.randint(0,100000),random.randint(0,100000))
            point = self.itemAt(pos,QTransform())
            if point == None:
                text = ''.join(random.choices(string.ascii_lowercase + string.digits + ' ', k = random.randint(2,5)))
                #text = ''
                item = self.addEntity(pos,text,0,0)
        for _ in range(1000):
            upper = random.randint(2,4)
            split = random.randint(2,upper)-1
            sel = random.sample(self.entities + self.relationships,k=upper)
            sources = sel[:split]
            destinations = sel[split:]
            if sources not in destinations and destinations not in sources:
                text = ''.join(random.choices(string.ascii_lowercase + string.digits + ' ', k = random.randint(0,4)))
                _type = random.randint(0,3)
                self.addRelationship(sources,destinations,text,_type)
    def status(self,s):
        if s != self.log[0]:
            self.log.insert(0,s)
        if len(self.log) > int(self.ui.config['settings']['logLength']):
            self.log.pop(-1)
        textList = list(self.log)
        textList[0] = f"<font color=\"red\">{textList[0]}</font>" # first 
            
        self.ui.statusText.setText(', '.join(textList))
    def updateInfo(self):
        filepath = self.ui.config['runtime']['filepath']
        quality = self.ui.config['settings']['screenshotquality']
        version = self.ui.config['releaseinfo']['version']
        info = [
            f'Ver: {version}',
            f'Entities: {len(self.entities)}',
            f'Relationships: {len(self.relationships)}',
            f'Savefile: "{filepath}"',
            f'Limited View: {self.limitedView}',
            f'Sel Length: {len(self.selection)}',
            f'Accesory Path Len: {len(self.accesoryPathsSelection)}',
            f'Theme: None',
            f'Screenshot Quality: {quality}',
            ]
        infroStr = '  |  '.join(info)
        self.ui.InfoText.setText(infroStr)
    def addEntity(self,pos,text,popularity=0,_type=0): # fundamental
        self.status(f"Created Entity: {text}")
        entity = Entity(text,popularity,_type)
        entity.setPos(pos)
        self.addItem(entity)
        self.entities.append(entity)
        entity.setStyle(_type,'none')
        self.updateInfo()
        return entity
    def addRelationship(self,sources,destinations,text='',_type=0): # fundamental
        self.status(f"Created Relationship: {[s.text for s in sources]}:{text}:{[d.text for d in destinations]}")
        relation = Relationship(sources,destinations,text,_type) #sources = ancestors, destination = children
        relation.stack()
        relation.sortDepth() # for saving
        self.addItem(relation)
        self.relationships.append(relation)
        relation.setStyle(_type,'none')
        self.updateInfo()
        return relation
    def deleteRelationship(self,relationship): # fundamental
        self.status(f"Deleted Relationship: {relationship.text}")
        tempChildren = relationship.children
        tempAncestors = relationship.ancestors
        relationship.setChildren([])
        relationship.setAncestors([])
        for item in tempChildren + tempAncestors:
            if type(item) == Relationship and item in self.relationships:
                if item in tempAncestors and relationship in item.destinations:
                    des = item.destinations
                    des.remove(relationship)
                    item.setDestinations(des)
                if item in tempChildren and relationship in item.sources:
                    chi = item.sources
                    chi.remove(relationship)
                    item.setSources(chi)
                if len(item.sources) < 1 or len(item.destinations) < 1:
                    self.deleteRelationship(item)
                elif item in tempChildren:
                    item.stack()
                else:
                    item.chainUpdate()
        self.relationships.remove(relationship)
        self.removeItem(relationship)
        self.updateInfo()
    def deleteEntity(self,entity): # fundamental
        self.status(f"Deleted Entity: {entity.text}")
        tempChildren = entity.children
        tempAncestors = entity.ancestors
        entity.setChildren([])
        entity.setAncestors([])
        for item in tempChildren + tempAncestors:
            if type(item) == Relationship and item in self.relationships:
                if item in tempAncestors and entity in item.destinations:
                    des = item.destinations
                    des.remove(entity)
                    item.setDestinations(des)
                if item in tempChildren and entity in item.sources:
                    chi = item.sources
                    chi.remove(entity)
                    item.setSources(chi)
                if len(item.sources) < 1 or len(item.destinations) < 1:
                    self.deleteRelationship(item)
                else:
                    item.chainUpdate()
        self.entities.remove(entity)
        self.removeItem(entity)
        self.updateInfo()
    def mergeRelationships(self):
        names = [i.text for i in self.selection]
        if len(set(names)) == 1 and len(self.selection) > 1 and [type(r) == Relationship for r in self.selection].count(False) == 0: # if all relationshits have the same name, selection is above one
            sources = []
            destinations = []
            for item in self.selection:
                for source in item.sources:
                    if source not in self.selection and source not in sources:
                        sources.append(source)
                for destination in item.destinations:
                    if destination not in self.selection and destination not in destinations:
                        destinations.append(destination)
            sel = sorted(self.selection,key=lambda x: x.depthPos,reverse= False)
            for item in sel:
                self.deleteRelationship(item)
            combined = self.addRelationship(sources,destinations,names[0],self.selection[0].type)
            self.clearSelection()           
            self.setSelected(combined,0)
            self.status('Merged Relationships')
        self.updateInfo()
    def splitRelationship(self):
        if len(self.selection) == 1 and type(self.selection[0]) == Relationship:
            relat = self.selection[0]
            sources = relat.sources
            destinations = relat.destinations
            self.clearSelection()
            self.deleteRelationship(relat)
            items = []
            for s in sources:
                for d in destinations:
                    i = self.addRelationship([s],[d],relat.text,relat.type)
                    items.append(i)
            for i in items:
                self.setSelected(i,0)
            self.status('Split Relationship')
        self.updateInfo()
    def flipRelationship(self):
        if [type(i)==Relationship for i in self.selection].count(False) == 0:# if all selections are relationships
            sel = sorted(self.selection,key=lambda z: z.depthPos,reverse=False)
            for item in sel:
                if item.arrowType not in ['none','undirect']:
                    sources = item.sources
                    destinations = item.destinations
                    item.setSources(destinations)
                    item.setDestinations(sources)
                    item.chainUpdate()
            if len(self.selection) == 1:
                self.clearTabs()
                self.setTabs(self.selection[0])
            self.status(f'Flipped Relationship" {item.text}')
        self.updateInfo()
    def assignSources(self):
        if [type(i)==Relationship for i in self.sourceSelection].count(False) == 0 and self.sourceSelection != [] and self.destinationSelection != []:# if all selections are relationships
            sel = []
            for item in self.sourceSelection:
                if item.arrowType in ['undirect','none']:
                    item.toDirect()
                sources = []
                [sources.append(x) for x in self.destinationSelection if x not in sources]
                item.setSources(sources)
                item.chainUpdate()
                sel.append(item)
            self.clearSelection()
            for item in sel:
                if item.arrowType in ['undirect','none']:
                    item.toInDirect()
                item.chainUpdate()
                self.setSelected(item,0)
                if item.arrowType in ['undirect','none']:
                    item.toInDirect()
        self.updateInfo()       
    def assignDestinations(self):
        if [type(i)==Relationship for i in self.sourceSelection].count(False) == 0 and self.sourceSelection != [] and self.destinationSelection != []:# if all selections are relationships
            sel = []
            for item in self.sourceSelection:
                if item.arrowType in ['undirect','none']:
                    item.toDirect()
                destinations = []
                [destinations.append(x) for x in self.destinationSelection if x not in destinations]
                item.setDestinations(destinations)
                sel.append(item)
            self.clearSelection()
            for item in sel:
                if item.arrowType in ['undirect','none']:
                    item.toInDirect()
                item.chainUpdate()
                self.setSelected(item,0) 
        self.updateInfo()  
    def disc(self): 
        try: # disconnect name text box
            self.ui.nameBox.disconnect()
        except:
            pass
        self.ui.mainView.setFocus() 
    def clearSelection(self):
        self.status(f"Cleared selection")
        temp = self.selection + self.accesoryPathsSelection # keep a list of normal selection and other
        self.selection = []
        self.sourceSelection = []
        self.destinationSelection = []
        self.accesoryPathsSelection = []
        for i in temp:
            if self.limitedView:
                i.setStyle(-1,'hidden')
                i.update()
            else:
                i.setStyle(-1,'none') # no selection same type
                i.update()
        self.disc()
        self.ui.nameBox.setText('')
        self.ui.entryLine.setText('')
        self.ui.entryLine.sourceLabel.setText('')
        self.ui.entryLine.destinationLabel.setText('')
        self.clearTabs()
        self.ui.detailView.items = self.entities + self.relationships
        self.ui.detailView.showItems() # detail view
        self.updateInfo()
    def findAcsendingPaths(self,source,destination,path=[],depth=0,depthMax=3):
        if depth >= depthMax:
            return []
        if type(source) == Entity:
            depth += 1
        path = path + [source]
        if source == destination:
            return [path]
        paths = []
        for ancestor in source.ancestors:
            if ancestor not in path:
                npath = self.findAcsendingPaths(ancestor,destination,path,depth)
                for p in npath:
                    paths.append(p)
        return paths
    def findDecendingPaths(self,source,destination,path=[],depth=0,depthMax=3):
        if depth >= depthMax:
            return []
        if type(source) == Entity:
            depth += 1
        path = path + [source]
        if source == destination:
            return [path]
        paths = []
        for child in source.children:
            if child not in path:
                npath = self.findDecendingPaths(child,destination,path,depth)
                for p in npath:
                    paths.append(p)
        return paths
    def setTabs(self,item):
        for child in item.children:
            q = clickableLabel(child.text,self.ui.childScrollContent,child,item)
            self.ui.childLayout.addWidget(q)
            q.clicked.connect(self.clearSelection)
            q.clicked.connect(self.setSelected)
        for ancestor in item.ancestors:
            q = clickableLabel(ancestor.text,self.ui.ancestorScrollContent,ancestor,item)
            self.ui.ancestorLayout.addWidget(q)
            q.clicked.connect(self.clearSelection)
            q.clicked.connect(self.setSelected)
    def clearTabs(self):
        for it in [i for i in self.ui.childScrollContent.children() if type(i) == clickableLabel]:
            self.ui.childLayout.removeWidget(it)
            it.deleteLater()
            it = None
        for it in [i for i in self.ui.ancestorScrollContent.children() if type(i) == clickableLabel]:
            self.ui.ancestorLayout.removeWidget(it)
            it.deleteLater()
            it = None        
    def setSelected(self,item,sd = 0):
        self.status(f"Set {item.text} Selected")
        if item not in self.selection:
            self.selection.append(item) # add to selection
            if self.sourceSelection == []:
                self.sourceSelection.append(item)
                item.setStyle(-1,'source')
            else:
                if sd == 0: # sd means if source or destination was intended
                    self.sourceSelection.append(item)
                    item.setStyle(-1,'source')
                else:
                    self.destinationSelection.append(item)
                    item.setStyle(-1,'destination')
            item.update()

            self.ui.nameBox.textEdited.connect(item.setText) # renaming

            self.ui.entryLine.sourceLabel.setText(f"{', '.join([j.text for j in self.sourceSelection])} ")
            self.ui.entryLine.destinationLabel.setText(f" {', '.join([j.text for j in self.destinationSelection])}")
            if len(self.selection) == 1: #if only one item is selected, show children and ancestors
                self.ui.nameBox.setText(self.selection[0].text)
                self.setTabs(item)
         
            elif len(self.selection) == 2: #if length of selection is 2 highlight path
                self.ui.nameBox.setText('')
                self.clearTabs()
                apaths = self.findAcsendingPaths(self.selection[0],self.selection[1])
                dpaths = self.findDecendingPaths(self.selection[0],self.selection[1]) 
                if dpaths != []:
                    for f in dpaths:
                        for i in f[1:-1]: #get rid of source and destination
                            self.accesoryPathsSelection.append(i)
                            i.setStyle(-1,'accD')
                            i.update()
                if apaths != []:
                    for f in apaths:
                        for i in f[1:-1]: #get rid of source and destination
                            self.accesoryPathsSelection.append(i)
                            i.setStyle(-1,'accU')
                            i.update()
            childs = [c for c in item.children if c not in self.selection]
            ancestors = [a for a in item.ancestors if a not in self.selection]
            for child in childs: # highlight the children
                self.accesoryPathsSelection.append(child)
                child.setStyle(-1,'accD')
                child.update()
            for ancestor in ancestors: # highlight the ancestors
                self.accesoryPathsSelection.append(ancestor)
                ancestor.setStyle(-1,'accU')
                ancestor.update()

            self.ui.detailView.items = self.selection
            self.ui.detailView.showItems() # detail view
        self.updateInfo()
    def toggleLimitedView(self):
        self.limitedView = not self.limitedView
        self.status(f"Set Limited View: {self.limitedView}")
        if self.limitedView: # if turned true
            for item in self.entities + self.relationships: # for all items
                if item not in self.selection + self.accesoryPathsSelection: # if item isnt in selection
                    item.setStyle(-1,'hidden')
                    item.update()
        else: # if turned off, set 
            for item in self.entities + self.relationships:
                if item in self.selection + self.accesoryPathsSelection:
                    item.setStyle(-1,-1) # dont change type, just select it to normal highlighting
                else:
                    item.setStyle(-1,'none')
                item.update()
        self.updateInfo()
    def returnEntity(self,text):
        matching = [e for e in self.entities if e.text == text]
        if len(matching) == 0:
            return None
        else:
            return matching
    def stringToNet(self):
        s = self.ui.entryLine.text()
        s = s.split(',')
        for sentence in s:
            if sentence != "":
                suspectedSelection = self.returnEntity(sentence)
                if suspectedSelection:
                    self.clearSelection()
                    for i in suspectedSelection:
                        self.setSelected(i,0)
                    return
                sentence = sentence.lower()
                if self.sourceSelection != [] and self.destinationSelection != []: # user has both a source and destination so make a straight relationship
                    text = sentence
                    sources = self.sourceSelection
                    destinations = self.destinationSelection
                    item = self.addRelationship(sources,destinations,text)
                else:
                    origin = self.ui.mainView.mapFromGlobal(QCursor().pos())
                    relativeOrigin = self.ui.mainView.mapToScene(origin)
                    if sentence == " ": # if empty just create raw entity
                        e = self.addEntity(relativeOrigin,"",_type=0)
                    else:
                        relationships,entitys = self.nlp.getPairs(sentence)
                        # need to pair entity and relationship with tree item
                        sceneEntitys = []
                        for n,i in enumerate(entitys):
                            items = [] # scene items to be attached
                            for text in self.nlp.toList(i,[]):
                                e = self.returnEntity(text)
                                if e == None: # if no entity exists, return a new one
                                    posTags = [j[1] for j in i.leaves()]
                                    if [j in posTags for j in ["NN","NNS","NNP"]].count(True) > 0:
                                        _type = 0
                                    else:
                                        _type = 1
                                    #_type = self.nlp.getType()
                                    e = self.addEntity(relativeOrigin,text,_type=_type)
                                else:
                                    e = e[0]
                                items.append(e)
                            sceneEntitys.append(items)
                        sceneRelats = []
                        for n,i in enumerate(relationships):
                            text = self.nlp.toList(i[1],[])[0]
                            if i[0] == []: # if there is no found source
                                sources = self.sourceSelection
                            else:
                                if i[0] in [r[1] for r in relationships]:
                                    sources = sceneRelats[[r[1] for r in relationships].index(i[0])]
                                elif i[0] in entitys:
                                    sources = sceneEntitys[entitys.index(i[0])]
                            if i[2] in [r[1] for r in relationships]:
                                destinations = sceneRelats[[r[1] for r in relationships].index(i[2])]
                            elif i[2] in entitys:
                                destinations = sceneEntitys[entitys.index(i[2])]
                            posTags = [j[1] for j in i[1]]
                            if "IN" in posTags:
                                _type = 0
                            else:
                                _type = 1
                            item = self.addRelationship(sources,destinations,text,_type)
                            sceneRelats.append([item])
                    #self.status(f"Created Mini Net of {len(sceneRelats + sceneEntitys)} Items")
        self.updateInfo()
    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        if event.button() == 1:
            item = self.itemAt(event.scenePos(),self.ui.mainView.transform())
            if item:
                if item not in self.selection:
                    if event.modifiers() == Qt.ControlModifier:
                        self.setSelected(item,1)
                    elif event.modifiers() == Qt.ShiftModifier:
                        self.setSelected(item,0)
                    else:
                        self.clearSelection()
                        self.setSelected(item,0)
            else: # cancel selection if no item was selected
                self.clearSelection()
        return 
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        mod = event.modifiers()
        if key == Qt.Key_Delete and self.selection != []: #delete
            temp = self.selection
            self.clearSelection()
            for i in temp:
                if type(i) == Entity:
                    self.deleteEntity(i)
                elif type(i) == Relationship:
                    self.deleteRelationship(i)
        if key == Qt.Key_Escape and self.selection != []:
            self.clearSelection()
        if (QKeyEvent.text(event) in ['1','2','3','4']) and self.selection != []: #change types
            for i in self.selection:
                if type(i) == Entity and int(QKeyEvent.text(event)) > 2:
                    pass
                else:
                    i.type = int(QKeyEvent.text(event))-1
                    i.setStyle(i.type,-1) # change to -1
                    i.buildPath()
                    i.findFont()
                    i.update()
                    if type(i) == Relationship:
                        for f in [x for x in i.sources if type(x) == Entity]:
                            f.updatePopularity()
            if len(self.selection) == 1:
                self.clearTabs()
                self.setTabs(self.selection[0])

        if key == Qt.Key_R and self.selection != []: # renaming
            self.status(f'Renaming {[j.text for j in self.selection]}')
            self.ui.nameBox.setFocus()
            for i in self.selection:
                self.ui.nameBox.textEdited.connect(i.setText)
                self.ui.nameBox.editingFinished.connect(self.disc)
        if (key == Qt.Key_E): # entry bar
            self.status(f'Awaiting Input')
            self.ui.entryLine.setFocus()
        if (key == Qt.Key_Q):
            if self.sourceSelection != [] and self.destinationSelection != []:
                item = self.addRelationship(self.sourceSelection,self.destinationSelection)
                self.clearSelection()
                self.setSelected(item,0)
        if (key==Qt.Key_P): # debug only
            tracker.print_diff()
            all_objects = muppy.get_objects()
            print(len(all_objects))
        return super().keyPressEvent(event)
class MainViewport(QtWidgets.QGraphicsView):
    def __init__(self,parent,scene,ui):
        super(MainViewport,self).__init__(parent=parent)
        self.ui = ui
        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setMouseTracking(False)
        self.setStyleSheet('border: solid 0px;')
        self.numScheduledScalings = 0
        self.oldPanPos = self.mapToScene(self.rect().center())

        self.zoomAnim = QTimeLine()
        self.zoomAnim.setFrameRange(0,100)
        self.zoomAnim.setCurveShape(QTimeLine.CurveShape.LinearCurve)
        self.zoomAnim.setUpdateInterval(5)
        self.zoomAnim.frameChanged.connect(self.smoothMove)

        self.wheelAnim = QTimeLine(2000)
        self.wheelAnim.setUpdateInterval(1)
        self.wheelAnim.valueChanged.connect(self.scalingTime)
        self.wheelAnim.finished.connect(self.animFinished)
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None: # pan
        if event.button() == 2:
            self.zoomAnim.stop()
            self.wheelAnim.stop()
            self.numScheduledScalings = 0
            self.oldPanPos = self.mapToScene(event.pos())
            return
        return super().mousePressEvent(event)
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)
        if event.buttons() == Qt.RightButton:
            self.numScheduledScalings = 0     
            self.newPanPos = self.mapToScene(event.pos())
            delta = self.newPanPos - self.oldPanPos
            delta = delta
            self.translate(delta.x(),delta.y())
            return
        return super().mouseMoveEvent(event)
    def currZoom(self):
        rect = self.sceneRect()
        viewRect = self.mapToScene(self.rect()).boundingRect()
        zoom = min(viewRect.width()/rect.width(),viewRect.height()/rect.height())
        return zoom
    def wheelEvent(self, event):
        if event.buttons() == Qt.RightButton:
            return
        self.zoomAnim.stop()
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)
        numDegrees = event.angleDelta().y()/120
        if abs(self.numScheduledScalings) < 20:
            self.numScheduledScalings += numDegrees*5
        self.oldPos = self.mapToScene(event.pos())
        self.eventPos = event.pos()
        self.wheelAnim.setCurrentTime(0)
        if self.wheelAnim.state() == 0:
            self.wheelAnim.start()
    def scalingTime(self,x):
        if self.numScheduledScalings != 0:
            factor = 1 + (self.numScheduledScalings*(1-x))/500
            self.scale(factor,factor)
            self.newPos = self.mapToScene(self.eventPos)
            delta = self.newPos - self.oldPos
            self.translate(delta.x(),delta.y())
            self.numScheduledScalings = self.numScheduledScalings*(1-x)
    def animFinished(self):
        self.numScheduledScalings = 0
    def showSelected(self):
        plx = []
        ply = []
        if self.scene().selection == []:
            return
        for i in self.scene().selection:
            boundingRect = i.boundingRect()
            boundingRect.translate(i.scenePos())
            plx.append(boundingRect.left())
            plx.append(boundingRect.right())
            ply.append(boundingRect.top())
            ply.append(boundingRect.bottom())
        x1= min(plx); x2 = max(plx)
        y1 = min(ply); y2 = max(ply)
        targRect = QRectF(x1,y1,x2-x1,y2-y1)
        targRect.adjust(-50,-50,50,50)
        sourceRect = self.mapToScene(self.rect()).boundingRect()
        
        d = self.zoomAnim.endFrame()
        w = max(targRect.width()/sourceRect.width(),targRect.height()/sourceRect.height())
        zoomThresh = .0001
        transThresh = 100
        dis = sourceRect.center() - targRect.center()
        if w < 1+zoomThresh and w > 1-zoomThresh and dis.manhattanLength() < transThresh:
            return
        self.panPath = QLineF(sourceRect.center(),targRect.center())
        self.zoom = math.exp(-(math.log(w)/d))
        self.prevFrame = 0
        if self.zoomAnim.state() == 2:
            self.zoomAnim.stop()
        self.zoomAnim.start()
    def smoothMove(self,x):
        diff = x-self.prevFrame # make up for skipped frames
        self.scale(self.zoom**diff,self.zoom**diff)
        self.centerOn(self.panPath.pointAt(x/100))
        self.prevFrame = x
class DetailViewport(QtWidgets.QGraphicsView):
    def __init__(self,parent,scene,ui):
        super(DetailViewport,self).__init__(parent=parent)
        self.setScene(scene)
        self.ui = ui
        self.setInteractive(False)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(False)
        self.setStyleSheet('border: solid 0px;')
        self.items = []
    def showItems(self):
        #self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        #self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)
        plx = []
        ply = []
        if self.items == []:
            return
        for i in self.items:
            boundingRect = i.boundingRect()
            boundingRect.translate(i.scenePos())
            plx.append(boundingRect.left())
            plx.append(boundingRect.right())
            ply.append(boundingRect.top())
            ply.append(boundingRect.bottom())
        x1= min(plx); x2 = max(plx)
        y1 = min(ply); y2 = max(ply)
        rect = QRectF(x1,y1,x2-x1,y2-y1)
        rect.adjust(-50,-50,50,50)
        self.fitInView(rect,1)
class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(SourcePath('res/main.ui'), self) # Load the .ui file
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint)
        self.setFocusPolicy(Qt.ClickFocus)

        self.config = configparser.ConfigParser()
        self.config.read('.config/config.ini')

        self.applyTheme()

        self.vLine3.setFixedWidth(1)
        self.vLine2.setFixedWidth(1)
        self.vLine.setFixedWidth(1)
        self.hLine.setFixedHeight(1)

        self.entryLine = EntryLine(self.entryBar,self)
        self.scene = Scene(self)
        self.mainView = MainViewport(self.MainContainer,self.scene,self) #make a viewport to see scene
        self.detailView = DetailViewport(self.DetailContainer,self.scene,self)

        self.entryLayout.insertWidget(1,self.entryLine)
        
        self.MainLayout.addWidget(self.mainView)
        self.DetailLayout.addWidget(self.detailView)

        self.childLayout.setAlignment(Qt.AlignTop)
        self.ancestorLayout.setAlignment(Qt.AlignTop)

        self.setFocus()

        self.Minimize.clicked.connect(self.minimize)
        self.Window.clicked.connect(self.windowed)
        self.Exit.clicked.connect(self.closeWin)
        self.Save.clicked.connect(self.saveT)
        self.SaveAs.clicked.connect(self.saveAs)
        self.Load.clicked.connect(lambda: self.load(''))
        self.newNet.clicked.connect(self.new)
        self.ScreenShot.clicked.connect(self.screenShot)
        self.CenterView.clicked.connect(self.mainView.showSelected)
        self.Hide.clicked.connect(lambda: self.scene.toggleLimitedView())
        self.Merge.clicked.connect(lambda: self.scene.mergeRelationships())
        self.Split.clicked.connect(lambda: self.scene.splitRelationship())
        self.Swap.clicked.connect(lambda: self.scene.flipRelationship())
        self.AssignSources.clicked.connect(lambda: self.scene.assignSources())
        self.AssignDestinations.clicked.connect(lambda: self.scene.assignDestinations())

        if self.config['runtime']['filepath'] != '': # if filepath is not empty, try loading last save
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.load(filename = self.config['runtime']['filepath']))
            timer.start(0) # wait until after event loop to load
    def applyTheme(self):
        with open(self.config['theme']['themefile'], "r") as jsonfile:
            theme = json.load(jsonfile)
            jsonfile.close()
        stylesheet = ""
        for key,value in theme['ui'].items():
            info = key.split('.')
            stylesheet = stylesheet + info[0] + "{" + info[1] + ":" + value + ";} "
        self.setStyleSheet(stylesheet)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
    def expandEntry(self):
        self.anim = QPropertyAnimation(self.entryBar,b'maximumHeight')
        self.anim.setDuration(150)
        self.anim.setStartValue(self.entryBar.maximumHeight())
        self.anim.setEndValue(30)
        self.anim.start()
    def collapseEntry(self):
        self.anim = QPropertyAnimation(self.entryBar,b'maximumHeight')
        self.anim.setDuration(150)
        self.anim.setStartValue(self.entryBar.maximumHeight())
        self.anim.setEndValue(20)
        self.anim.start()
    def windowed(self):
        if self.isMaximized():
            self.Window.setText("[]")
            self.showNormal()
        else:
            self.Window.setText("..")
            self.showMaximized()         
    def minimize(self):
        self.showMinimized()
    def closeWin(self):
        with open('.config/config.ini', 'w') as configfile:
            self.config.write(configfile)
        configfile.close()
        app.exit()
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None: # draggable window
        if self.Topbar.hasFocus():
            self.offset = event.pos()
        return super().mousePressEvent(event)
    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.Topbar.hasFocus():
            self.Window.setText("[]")
            self.showNormal()
            x=event.globalX()
            y=event.globalY()
            x_w = self.offset.x()
            y_w = self.offset.y()
            self.move(x-x_w, y-y_w)
        return super().mouseMoveEvent(event)
    def screenShot(self):
        viewRect = self.mainView.mapToScene(self.mainView.rect()).boundingRect()
        image = QImage(viewRect.size().toSize()*int(self.config['settings']['screenshotquality']),QImage.Format_ARGB32)
        #image = QImage(self.scene.sceneRect().size().toSize(),QImage.Format_ARGB32) # full sized picture
        image.fill(Qt.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing,True)
        self.scene.render(painter,target=QRectF(image.rect()),source=viewRect,mode=1)
        suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
        filename = "_".join(['screenshot', suffix]) # e.g. 'mylogfile_120508_171442
        path = self.config['settings']['screenshots']
        ext = self.config['settings']['screenshotsext']
        image.save(f'{path}{filename}{ext}')
        painter.end()
        self.scene.status(f'Saved Snapshot to: {path}{filename}{ext}')
    def new(self):
        self.config['runtime']['filepath'] = ''
        self.scene.clearSelection()
        self.Title.setText("NetX2")
        while self.scene.relationships != []:
            for relat in self.scene.relationships:
                self.scene.deleteRelationship(relat)
        while self.scene.entities != []:
            for entity in self.scene.entities:
                self.scene.deleteEntity(entity)
        self.scene.clear()
        self.scene.deleteLater()
        self.scene = Scene(self)
        self.mainView.setScene(self.scene)
        self.detailView.setScene(self.scene)
        self.scene.status(f'Created New Net')
    def saveT(self):
        if self.config['runtime']['filepath'] == '':
            self.saveAs()
        else:
            self.save()
    def saveAs(self):
        filename = QtWidgets.QFileDialog().getSaveFileName(None,'Save Net','nets//','NET File (*.net)')[0]
        if filename == '':
            return
        self.config['runtime']['filepath'] = filename
        self.save()
    def save(self):
        name = re.findall('/[^/]*$',self.config['runtime']['filepath'])[0][1:-4]
        self.Title.setText(f'{name} - NetX2')
        obj = {}
        obj['Entitys'] = []
        obj['Relationships'] = []
        entityDict = {}
        relationshipDict = {}
        for key,entity in enumerate(self.scene.entities):
            obj['Entitys'].append([entity.scenePos(),entity.text,entity.popularity,entity.type,key])
            entityDict[entity] = key
        self.scene.relationships.sort(key= lambda x: x.depthPos,reverse=True)
        for key, relat in enumerate(self.scene.relationships):
            relationshipDict[relat] = key
        for key, relationship in enumerate(self.scene.relationships):
            Rsources = [relationshipDict[i] for i in relationship.sources if type(i) == Relationship]
            Esources = [entityDict[i] for i in relationship.sources if type(i) == Entity]
            Rdestinations = [relationshipDict[i] for i in relationship.destinations if type(i) == Relationship]
            Edestinations = [entityDict[i] for i in relationship.destinations if type(i) == Entity]
            obj['Relationships'].append([[Rsources,Esources],[Rdestinations,Edestinations],relationship.text,relationship.type,key])
        n = self.config['runtime']['filepath']
        with open(n, 'wb') as f:
            pickle.dump(obj,f,pickle.HIGHEST_PROTOCOL)
        f.close()
        self.scene.updateInfo()
        self.scene.status(f'Saved Net to {n}')
    def load(self,filename=''):
        if filename == '':
            filename = QtWidgets.QFileDialog().getOpenFileName(None,'Load Net','nets//','NET File (*.net)')[0]
            if filename == '':
                return
        self.config['runtime']['filepath'] = filename
        name = re.findall('/[^/]*$',filename)[0][1:-4]
        self.Title.setText(f'{name} - NetX2')
        self.scene.clearSelection()

        self.scene.clear()
        self.scene.deleteLater()
        self.scene = Scene(self)
        self.mainView.setScene(self.scene)
        self.detailView.setScene(self.scene)
        with open(filename,'rb') as f:
            obj = pickle.load(f)
            entityDict = {}
            relationshipDict = {}
            for i in obj['Entitys']:
                entity = self.scene.addEntity(i[0],i[1],i[2],i[3])
                entity.buildPath()
                entityDict[i[4]] = entity
            for i in obj['Relationships']:
                Rsources = [relationshipDict[k] for k in i[0][0]]
                Esources = [entityDict[k] for k in i[0][1]]
                Rdestinations = [relationshipDict[k] for k in i[1][0]]
                Edestinations = [entityDict[k] for k in i[1][1]]

                relationship = self.scene.addRelationship(Rsources+Esources,Rdestinations+Edestinations,i[2],i[3])
                relationship.buildPath()
                relationshipDict[i[4]] = relationship
        f.close()
        self.scene.clearSelection()
        if self.scene.items() != []:
            plx = []
            ply = []
            for i in self.scene.items():
                boundingRect = i.boundingRect()
                boundingRect.translate(i.scenePos())
                plx.append(boundingRect.left())
                plx.append(boundingRect.right())
                ply.append(boundingRect.top())
                ply.append(boundingRect.bottom())
            x1= min(plx); x2 = max(plx)
            y1 = min(ply); y2 = max(ply)
            targRect = QRectF(x1,y1,x2-x1,y2-y1)
            targRect.adjust(-50,-50,50,50)
            self.mainView.fitInView(targRect,1)
            #self.detailView.showItems()
        self.scene.updateInfo()
        self.scene.status(f'Loaded Net from {filename}')
    def focusNextPrevChild(self, next: bool) -> bool: #make tab accesible
        return False
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    sys.exit(app.exec_())