from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import string
import difflib
import json
import configparser

config = configparser.ConfigParser()
config.read('.config/config.ini')
with open(config['theme']['themefile'], "r") as jsonfile:
    style = json.load(jsonfile)['entryline']
    jsonfile.close()

class EntryLine(QtWidgets.QLineEdit):
    def __init__(self,parent,ui):
        super(EntryLine,self).__init__(parent=parent)
        self.ui = ui
        self.numSuggestions = int(ui.config['settings']['maxsuggestionlength'])
        self.setFocusPolicy(Qt.ClickFocus)

        self.setPlaceholderText('. . .')
        self.setAlignment(Qt.AlignHCenter)
        self.setStyleSheet('QLineEdit {'+ style['textBck'] + '}')

        self.sourceDormant = style['sourceDormant']
        self.sourceActive = style['sourceActive']
        self.textDormant = style['textDormant']
        self.textActive = style['textActive']
        self.destinationDormant = style['destinationDormant']
        self.destinationActive = style['destinationActive']

        self.Hlayout = QtWidgets.QHBoxLayout(self)
        self.Hlayout.setContentsMargins(0,0,0,0)

        self.sourceLabel = QtWidgets.QLabel('')
        self.sourceLabel.setParent(self)
        self.sourceLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Fixed)
        self.sourceLabel.move(-1, 2)
        self.sourceLabel.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.sourceLabel.setStyleSheet(self.sourceDormant)
        self.sourceLabel.setAlignment(Qt.AlignRight)

        self.textLabel = QtWidgets.QLabel('. . .')
        self.textLabel.setParent(self)
        self.textLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Fixed)
        self.textLabel.move(-1, 2)
        self.textLabel.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.textLabel.setStyleSheet(self.textDormant)
        self.textLabel.setAlignment(Qt.AlignHCenter)

        self.destinationLabel = QtWidgets.QLabel('')
        self.destinationLabel.setParent(self)
        self.destinationLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Fixed)
        self.destinationLabel.move(-1, 2)
        self.destinationLabel.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.destinationLabel.setStyleSheet(self.destinationDormant)
        self.destinationLabel.setAlignment(Qt.AlignLeft)

        self.Hlayout.addWidget(self.sourceLabel)
        self.Hlayout.addWidget(self.textLabel)
        self.Hlayout.addWidget(self.destinationLabel)

        self.currtext = QtWidgets.QLineEdit()

        self.currString = ''
        self.currOption = 0
        self.sortedList = []
        self.labels = []
        
    def updateLabels(self):
        for i in self.labels:
            i.updateHighlight()
    def clearLabels(self):
        for i in self.labels:
            i.deleteLater()
        self.labels = []
    def sortAlgorithm(self,z,text):
        d = difflib.SequenceMatcher(None, z, text).ratio()
        return d
    def findClosest(self, text):
        names = [f.text for f in self.ui.scene.entities]
        values = [self.sortAlgorithm(z,text) for z in names]
        sortingDict = {}
        for name,val in zip(names,values):
            sortingDict[name] = val
        newNames = []
        for name,val in zip(names,values):
            if val > .1:
                newNames.append(name)
        self.sortedList = sorted(newNames, key=lambda z: sortingDict[z], reverse=True)[0:self.numSuggestions]
        for n,i in enumerate(self.sortedList):
            label = listLabel(self,self.ui.ContextFrame,i,None,n)
            self.ui.listLayout.insertWidget(0,label)
            self.labels.append(label)
    def edit(self, text):
        self.textLabel.setText(text)
        self.clearLabels()
        self.currOption = 0
        if self.currtext.text() != '':
            self.findClosest(self.currtext.text())
    def focusInEvent(self, a0: QtGui.QFocusEvent) -> None:
        self.textEdited.connect(self.edit)
        self.textLabel.setText('')
        self.textLabel.setStyleSheet(self.textActive)
        self.sourceLabel.setStyleSheet(self.sourceActive)
        self.destinationLabel.setStyleSheet(self.destinationActive)
        self.ui.expandEntry()
        return super().focusInEvent(a0)
    def focusOutEvent(self, a0: QtGui.QFocusEvent) -> None:
        self.ui.scene.stringToNet()
        self.ui.mainView.setFocus()
        self.ui.collapseEntry()
        self.disconnect()
        self.setText('')
        self.currtext.setText('')
        self.textLabel.setText('. . .')
        self.textLabel.setStyleSheet(self.textDormant)
        self.sourceLabel.setStyleSheet(self.sourceDormant)
        self.destinationLabel.setStyleSheet(self.destinationDormant)
        self.clearLabels()
        return super().focusOutEvent(a0)
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key_Return:
            self.ui.mainView.setFocus()
        if key == Qt.Key_Escape:
            self.setText('')
            self.ui.mainView.setFocus()
        if key == Qt.Key_Up:
            if self.currOption < min(self.numSuggestions,len(self.sortedList))-1:
                self.currOption += 1
                self.updateLabels()
        if key == Qt.Key_Down:
            if self.currOption > 0:
                self.currOption -= 1
                self.updateLabels()
        if event.text() in string.ascii_letters:
            self.currString += event.text()
        if key == Qt.Key_Backspace or key == Qt.Key_Delete:
            self.currString = self.currString[:-1]
        if key == Qt.Key_Space:
            self.currtext.setText('')
            return super().keyPressEvent(event)
        if key == Qt.Key_Tab:
            if len(self.sortedList) > 0 and self.currtext.text() != '':
                old = self.currtext.text()
                new = self.sortedList[self.currOption]

                textString = new.join(self.text().rsplit(old, 1))
                self.setText(textString)
                self.textLabel.setText(textString)
                self.currtext.setText('')
                self.clearLabels()

        QtWidgets.QApplication.sendEvent(self.currtext,event)
        return super().keyPressEvent(event)
    def resizeEvent(self, event):
        self.textLabel.setFixedHeight(self.height())
        self.sourceLabel.setFixedHeight(self.height())
        self.destinationLabel.setFixedHeight(self.height())
        super().resizeEvent(event)
    def focusNextPrevChild(self, next: bool) -> bool: # make tab accesible
        return False
class listLabel(QtWidgets.QLabel):
    def __init__(self,source,parent,text,entity,_id):
        super(listLabel,self).__init__(parent=parent)
        self.parent = parent
        self.source = source
        self.setText(text)
        self.id = _id
        #self.setFixedWidth(100)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Fixed)
        self.setAlignment(Qt.AlignHCenter)
        self.listDormant = 'font: 8pt "Yu Gothic"; color: rgba(255,0,0,100); background-color: rgba(0, 0, 0, 0);'
        self.listActive = 'font: 8pt "Yu Gothic"; color: rgba(255,0,0,233); background-color: rgba(0, 0, 0, 0);'
        self.updateHighlight()
    def updateHighlight(self):
        if self.source.currOption == self.id:
            self.setStyleSheet(self.listActive)
        else:
            self.setStyleSheet(self.listDormant)