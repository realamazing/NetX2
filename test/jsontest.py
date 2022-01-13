import json

from nltk.util import pr

with open("Tests/test.json", "r") as jsonfile:
    style = json.load(jsonfile)
    jsonfile.close()

stylesheet = ""
for key,value in style['ui'].items():
    info = key.split('.')
    stylesheet = stylesheet + "#" + info[0] + "{" + info[1] + ":" + value + ";} "
    print(info,value)
print(stylesheet)