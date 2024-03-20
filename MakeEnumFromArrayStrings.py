#TODO write a description for this script
#@author ashkitten
#@category Strings
#@keybinding 
#@menupath 
#@toolbar 

from ghidra.program.model.data import EnumDataType
import re
import itertools as it

listing = currentProgram.getListing()
root = listing.getDataContaining(currentLocation.getAddress())
rootAddress = root.getMinAddress()
offset = currentLocation.getAddress().subtract(rootAddress)

print(root, rootAddress, offset)

if root is None:
    printerr("No data at location")
    exit()

if not root.isArray():
    printerr("Data at location isn't an array")
    exit()

if root.getNumComponents() < 1:
    printerr("Array has no components")
    exit()

def findStringComponents(data, offset):
    index = data.getComponentIndex()
    if index == -1:
        index = 0
    name = data.getFieldName() or ("field" + str(index) + "_" + hex(data.getParentOffset()))
    parent = data.getParent()
    if parent is None:
        name = ""
    elif parent.isArray():
        name = "[]"

    indexPath = [data.getComponentIndex()]
    if parent is None or parent.isArray():
        indexPath = []

    if data.hasStringValue():
        return [(name, [indexPath])]
    elif data.isPointer():
        pointerData = listing.getDataAt(data.getValue())
        if pointerData is not None:
            return [
                ("->" + name + path, indexPaths[:-1] + [indexPath + indexPaths[-1], []])
                for (path, indexPaths) in findStringComponents(pointerData, 0)
            ]
        else:
            return []
    elif data.isStructure() or data.isArray():
        children = []
        if offset > 0:
            child = data.getComponentContaining(offset)
            children = [(child, offset - child.getParentOffset())]
        else:
            children = [
                (data.getComponent(i), 0)
                for i in range(data.getNumComponents())
            ]
        return [
            (
                ("." if data.isStructure() else "") + name + path,
                indexPaths[:-1] + [indexPath + indexPaths[-1]]
            )
            for (child, offset) in children
            for (path, indexPaths) in findStringComponents(child, offset)
        ]
    else:
        return []

paths = dict(findStringComponents(root, offset))
print(paths)
choice = askChoice("Choose String", "Please choose the correct string to use for naming enum items.", paths.keys(), paths.keys()[0])

name = askString("Enum Name", "Please choose a name for the enum", root.getFieldName())
enum = EnumDataType(name, currentProgram.getDefaultPointerSize())

for i in range(root.getNumComponents()):
    component = root.getComponent(i)
    for path in paths[choice]:
        for offset in path:
            component = component.getComponent(offset)
        if component is not None and component.isPointer():
            component = listing.getDataAt(component.getValue())
        elif component is not None and component.hasStringValue():
            enum.add(str(i) + ' \"' + component.getValue() + '"', i)

dataTypeManager = currentProgram.getDataTypeManager()
dataTypeManager.addDataType(enum, None)
