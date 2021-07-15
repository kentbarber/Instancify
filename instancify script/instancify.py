import c4d
from c4d import gui

def state():
    selectedObject = doc.GetActiveObject()
    return selectedObject is not None

def CompareVecs(vec1, vec2):
    Threshold = 1e-3 #Similarity Threshold when comparing Point Positions to avoid precision Errors
    if abs(vec1.x - vec2.x) > Threshold or abs(vec1.y - vec2.y) > Threshold or abs(vec1.z - vec2.z) > Threshold:
        return False
    return True

def ComparePoly(poly1, poly2):
    if poly1.a != poly2.a or poly1.b != poly2.b or poly1.c != poly2.c or poly1.d != poly2.d:
        return False
    return True

def ComparePoints(toTest, reference):
    pointsTest = toTest.GetAllPoints()
    pointsReference = reference.GetAllPoints()
    if len(pointsTest) != len(pointsReference):
        return False
    
    for pIndex in range(len(pointsTest)):
        if not CompareVecs(pointsTest[pIndex], pointsReference[pIndex]):
            return False
        
    testTags = toTest.GetTags()
    refTags = reference.GetTags()
    for refTag in refTags:
        refType = refTag.GetType()
        if refTag.IsInstanceOf(c4d.Tvariable) and refType != c4d.Tpolygon and refType != c4d.Tpoint:
            foundMatching = False
            for testTag in testTags:
                if testTag.GetType() == refType:
                    foundMatching = True
                    if refType == c4d.Tuvw:
                        if testTag.GetDataCount() != refTag.GetDataCount():
                            break
                        
                        for dataIndex in range(testTag.GetDataCount()):
                            if testTag.GetSlow(dataIndex) != refTag.GetSlow(dataIndex):
                                foundMatching = False
                                break
                        break
                    else:
                        testData = testTag.GetAllHighlevelData()
                        refData = refTag.GetAllHighlevelData()
                        if len(testData) != len(refData):
                            break
                        
                        for dataIndex in range(len(testData)):
                            if testData[dataIndex] != refData[dataIndex]:
                                foundMatching = False
                                break
                        break
                    if testTag.GetData() != refTag.GetData():
                        foundMatching = False
            if not foundMatching:
                return False
        elif refType == c4d.Tphong:
            for testTag in testTags:
                if testTag.GetType() == refType:
                     if testTag.GetData() != refTag.GetData():
                        return False
    return True

def ComparePolygons(toTest, reference):
    polyCountTest = toTest.GetPolygonCount()
    polyCountRef = reference.GetPolygonCount()
    if polyCountTest != polyCountRef:
        return False
    
    polysTest = toTest.GetAllPolygons()
    polysReference = reference.GetAllPolygons()
    for pIndex in range(polyCountTest):
        if not ComparePoly(polysTest[pIndex], polysReference[pIndex]):
            return False
    return True

def CopyValue(bc, source, id):
    if source[id] is not None:
        bc[id] = source[id]

def StoreAndReset(current, reset = True):
    storedBc = c4d.BaseContainer()
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_REL_POSITION)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_REL_ROTATION)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_REL_SCALE)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_VISIBILITY_EDITOR)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_VISIBILITY_RENDER)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_USECOLOR)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_COLOR)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_XRAY)
    CopyValue(storedBc, current, c4d.ID_BASEOBJECT_GENERATOR_FLAG)
    CopyValue(storedBc, current, 440000062)
    if reset:
        current[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(0.0)
        current[c4d.ID_BASEOBJECT_REL_ROTATION] = c4d.Vector(0.0)
        current[c4d.ID_BASEOBJECT_REL_SCALE] = c4d.Vector(1.0)
        current[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
        current[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
        current[c4d.ID_BASEOBJECT_USECOLOR] = 0
        current[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(1.0)
        current[c4d.ID_BASEOBJECT_XRAY] = 0
        current[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = 1
        current[440000062] = 0
    return storedBc

def RestoreData(current, storedBc):
    for index, value in storedBc:
        current[index] = value
    
def CompareWithSelected(current, selected, first):
    if current is None and selected is None:
        return True
    if current is None and selected is not None:
        return False
    if current is not None and selected is None:
        return True
    if current == selected or current.IsInstanceOf(c4d.Oinstance):
        return False
    
    downCurrent = current.GetDown()
    downSelected = selected.GetDown()
    if not CompareWithSelected(downCurrent, downSelected, False):
        return False
    
    if not first:
        nextCurrent = current.GetNext()
        nextSelected = selected.GetNext()
        if not CompareWithSelected(nextCurrent, nextSelected, False):
            return False
        
    compareObject = selected
    
    if current.GetType() != selected.GetType():
        if selected.GetCache() is None:
             return False
        if selected.GetCache().GetType() != current.GetType():
            return False
        compareObject = selected.GetCache()
    
    if current.IsInstanceOf(c4d.Opoint):
        if not ComparePoints(current, compareObject):
            return False
        if current.IsInstanceOf(c4d.Opolygon):
            if not ComparePolygons(current, compareObject):
                return False
    else:
        # remember matrices before BC comparison
        storedBc = StoreAndReset(current)
        if current.GetDataInstance()!= selected.GetDataInstance():
            RestoreData(current, storedBc)
            return False
    
        RestoreData(current, storedBc)
     
    return True

def CopyTrack(instance, toReplace, id, subid):
    trackId = c4d.DescID(c4d.DescLevel(id, c4d.DTYPE_VECTOR, 0),
                    c4d.DescLevel(subid, c4d.DTYPE_REAL, 0))
    track = toReplace.FindCTrack(trackId)
    if track:
        newTrack = track.GetClone(c4d.COPYFLAGS_NONE)
        instance.InsertTrackSorted(newTrack)

def ReplaceWithInstance(doc, toReplace, selected, mode):
    instance = c4d.BaseObject(c4d.Oinstance)

    instance[c4d.INSTANCEOBJECT_LINK] = selected
    instance[c4d.INSTANCEOBJECT_RENDERINSTANCE_MODE] = mode
    doc.InsertObject(instance, toReplace.GetUp(), toReplace)
  
    instance.SetMl(toReplace.GetMl())
    instance.SetName(selected.GetName() + "_instance")
    instance.SetAllBits(toReplace.GetAllBits())

    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_X)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y)
    CopyTrack(instance, toReplace, c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Z)

    storedBc = StoreAndReset(toReplace, False)
    RestoreData(instance, storedBc)
    allTags = toReplace.GetTags()
    for tag in allTags:
        if not tag.IsInstanceOf(c4d.Tvariable) and not tag.IsInstanceOf(c4d.Tphong):
            instance.InsertTag(tag.GetClone(c4d.COPYFLAGS_NONE))
    
    if toReplace.GetDown():
        doc.AddUndo(c4d.UNDOTYPE_CHANGE, toReplace.GetDown())
        toReplace.GetDown().InsertUnder(instance)

    # the order of undo and transfer is important. Deleting before transfering goals is important for redo
    doc.AddUndo(c4d.UNDOTYPE_DELETEOBJ, toReplace);
    # transfer goal needs to happen before undo new
    toReplace.TransferGoal(instance, True)
    doc.AddUndo(c4d.UNDOTYPE_NEW, instance)

    toReplace.Remove()

def IterateScene(doc, current, selected, mode):
    while current is not None:
        down = current.GetDown()
        nextObj = current.GetNext()

        if down is not None:
            IterateScene(doc, down, selected, mode)
            
        if CompareWithSelected(current, selected, True):
            ReplaceWithInstance(doc, current, selected, mode)
            
        current = nextObj
    
# Main function
def main():
    selectedObject = doc.GetActiveObject()
    if selectedObject is None:
        return
    
    res = c4d.gui.QuestionDialog("Replace with Render Instances (Yes) ? Or Normal Instances (No) ?")
    mode = c4d.INSTANCEOBJECT_RENDERINSTANCE_MODE_NONE
    if res:
        mode = c4d.INSTANCEOBJECT_RENDERINSTANCE_MODE_SINGLEINSTANCE
    doc.StartUndo()
    storedBc = StoreAndReset(selectedObject)
    try:
        IterateScene(doc, doc.GetFirstObject(), selectedObject, mode)
    finally:
        RestoreData(selectedObject, storedBc)
        doc.EndUndo()
        c4d.EventAdd()
        
# Execute main()
if __name__=='__main__':
    main()