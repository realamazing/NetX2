from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from structure2 import Entity,Relationship
import json
import configparser

config = configparser.ConfigParser()
config.read('NetX2/Resources/config.ini')
with open(config['theme']['themefile'], "r") as jsonfile:
    style = json.load(jsonfile)['graph']
    jsonfile.close()

class clickableLabel(QtWidgets.QLabel):
    clicked = pyqtSignal(QtWidgets.QGraphicsItem)
    def __init__(self,text,parent,item,sourceItem):
        super().__init__(text=text,parent=parent)
        self.item = item
        self.sourceItem = sourceItem
        self.updateStyle()
    def updateStyle(self):
        if type(self.item) == Entity:
            _type = "entity"
            rad = "10px"
        else:
            _type = "relationship"
            rad = "0px"
        if type(self.sourceItem) == Relationship:
            if self.item in self.sourceItem.sources + self.sourceItem.destinations:
                borderType = "solid"
            else:
                borderType = "dashed"
        else:
            borderType = "solid"
        col = "color:" + style[_type][self.item.type]['none']['color'] + ";"
        border = "border:" + "1px " + borderType + style[_type][self.item.type]['none']['color'] + ";"
        borderrad = "border-radius:" + rad + ";"
        self.setStyleSheet(col + border + borderrad)
    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.clicked.emit(self.item)
        return super().mousePressEvent(ev)