#Author-TehDmitry
#Description-Create a BOM by hashtag

import adsk.core, adsk.fusion, traceback
import subprocess, os, platform
from shutil import copyfile
import time
import csv


# Globals
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

addin_path = os.path.dirname(os.path.realpath(__file__)) 

defaultBomFilterStr = '#bom'
defaultBeamFilterStr = '#beam'
defaultExportToCSVEnabbled = False
defaultRemoveTagsFromName = True


# global set of event handlers to keep them referenced for the duration of the command
handlers = []

def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        print('{:s} function took {:.3f} ms'.format(f.__name__, (time2-time1)*1000.0))

        return ret
    return wrap

def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return

        unitsMgr = app.activeProduct.unitsManager

        commandDefinitions = ui.commandDefinitions
        #check the command exists or not
        cmdDef = commandDefinitions.itemById('TehHashBOM')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('TehHashBOM',
                    'Teh Hash BOM',
                    'Create a BOM by hashtag',
                    './resources') # relative resource file path is specified

        onCommandCreated = BOMCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



class BoltCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class BOMCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = BOMCommandExecuteHandler()
            cmd.execute.add(onExecute)
            #onExecutePreview = BOMCommandExecuteHandler()
            #cmd.executePreview.add(onExecutePreview)
            onDestroy = BoltCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            #handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            #define the inputs
            inputs = cmd.commandInputs

            inputs.addImageCommandInput('image', '', 'resources/Icon_128.png')

            inputs.addStringValueInput('bomFilterString', 'BOM Filter Tag', defaultBomFilterStr)
            inputs.addStringValueInput('beamFilterString', 'Beam Filter Tag', defaultBeamFilterStr)
            inputs.addBoolValueInput('exportToCSV', 'Also export to CSV', True, "", defaultExportToCSVEnabbled)
            inputs.addBoolValueInput('removeTagsFromName', 'Remove Tags', True, "", defaultRemoveTagsFromName)


        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class BOMCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cameraBackup = app.activeViewport.camera

            
            command = args.firingEvent.sender
            inputs = command.commandInputs

            bom = BOM()
            for input in inputs:
                if input.id == 'bomFilterString':
                    bom.bomFilterString = input.value
                if input.id == 'beamFilterString':
                    bom.beamFilterString = input.value
                if input.id == 'exportToCSV':
                    bom.exportToCSV = input.value
                if input.id == 'removeTagsFromName':
                    bom.removeTagsFromName = input.value

            bom.extractBOM()
            args.isValidResult = True

            app.activeViewport.camera = cameraBackup

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        

        # Force the termination of the command.
        adsk.terminate()   

def frange(x, y, jump):
    while x <= y:
        yield x
        x += jump

def getRange(minPoint, maxPoint, tolerance):
    xlen = maxPoint - minPoint
    i = 0
    while i <= 1:
        yield minPoint + xlen * i
        # loop body
        i += tolerance   

# https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-ce341ee6-4490-11e5-b25b-f8b156d7cd97
def getPrincipalMomentsOfInertia(component):
    physicalProperties = component.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)

    # Get principal axes from physical properties
    # (retVal, xAxis0, yAxis0, zAxis0) = physicalProperties.getPrincipalAxes()   
    
    # Get the moments of inertia about the principal axes. Unit for returned values is kg/cm^2.
    # (retValA,i1A,i2A,i3A) = physicalProperties.getPrincipalMomentsOfInertia()
    return physicalProperties.getPrincipalMomentsOfInertia()


class BOM:
    def __init__(self):
        self._bomFilterStr = defaultBomFilterStr
        self._beamFilterStr = defaultBeamFilterStr
        self._exportToCSV = defaultExportToCSVEnabbled
        self._removeTagsFromName = defaultRemoveTagsFromName

    #properties
    @property
    def bomFilterString(self):
        return self._bomFilterStr
    @bomFilterString.setter
    def bomFilterString(self, value):
        self._bomFilterStr = value

    @property
    def beamFilterString(self):
        return self._beamFilterStr
    @beamFilterString.setter
    def beamFilterString(self, value):
        self._beamFilterStr = value        

    @property
    def exportToCSV(self):
        return self._exportToCSV
    @exportToCSV.setter
    def exportToCSV(self, value):
        self._exportToCSV = value     

    @property
    def removeTagsFromName(self):
        return self._removeTagsFromName
    @removeTagsFromName.setter
    def removeTagsFromName(self, value):
        self._removeTagsFromName = value                


    @classmethod
    @timing
    def beautifyName(self, name):
        print(self._bomFilterStr)
        if self.removeTagsFromName:
            name = name.replace(str(self._bomFilterStr), "", 1)
            name = name.replace(str(self._beamFilterStr), "", 1)
        return name

    def addComponentToList(self, list, component, isBeam):
        # Gather any BOM worthy values from the component
        # volume = 0
        # bodies = component.bRepBodies
        # for bodyK in bodies:
        #     if bodyK.isSolid:
        #         volume += bodyK.volume

        volume = self.getVolume(component)                
        
        if volume > 0:
            convUnit = GetConvertUnit()
            boundingX = abs(round(convUnit * (component.boundingBox.maxPoint.x - component.boundingBox.minPoint.x), 1))
            boundingY = abs(round(convUnit * (component.boundingBox.maxPoint.y - component.boundingBox.minPoint.y), 1))
            boundingZ = abs(round(convUnit * (component.boundingBox.maxPoint.z - component.boundingBox.minPoint.z), 1))

            info = {
                'component': component,
                'name': self.beautifyName(component.name),
                'instances': 1,
                'volume': volume,
                'boundingX': boundingX,
                'boundingY': boundingY,
                'boundingZ': boundingZ,
                'is_profile': 0,
                'profile_length': 0,
                'profile_size': '',
                'profile_axis': -1,
                'i1': 0,
                'i2': 0,
                'i3': 0,
            }

            if isBeam:
                axisIndex = self.getLengthAxis(component)
                #axisIndex = -1
                if axisIndex < 0:
                    if boundingX > boundingY and boundingX > boundingZ:
                        axisIndex = 0
                    
                    if boundingY > boundingX and boundingY > boundingZ:
                        axisIndex = 1       
                
                    if boundingZ > boundingX and boundingZ > boundingY:
                        axisIndex = 2                    

                info['profile_axis'] = axisIndex

                if axisIndex == 0:
                    info['profile_length'] = boundingX
                    info['profile_size'] = '%g' % (max(boundingY, boundingZ)) + 'x' + '%g' % (min(boundingY, boundingZ))
                if axisIndex == 1:
                    info['profile_length'] = boundingY
                    info['profile_size'] = '%g' % (max(boundingX, boundingZ)) + 'x' + '%g' % (min(boundingX, boundingZ))
                if axisIndex == 2:
                    info['profile_length'] = boundingZ
                    info['profile_size'] = '%g' % (max(boundingY, boundingX)) + 'x' + '%g' % (min(boundingY, boundingX))

                if info['profile_length'] > 0:
                    info['is_profile'] = 1
                
                #(retValA,i1,i2,i3) = getPrincipalMomentsOfInertia(component)
                #info['name'] += ' ' + '%g' % i1 + ' ' + '%g' % i2 + ' ' + '%g' % i3 + ' ' 

            list.append(info)        


    @classmethod
    def collectInstance(self, list, component):
        instanceExistInList = False
        for listI in list:
            if listI['component'] == component:
                # Increment the instance count of the existing row.
                listI['instances'] += 1
                instanceExistInList = True
                break

        if not instanceExistInList:
            self.addComponentToList(list, component, False)


    @classmethod
    @timing
    def collectBeam(self, list, component):
        beamExistInList = False
        for listI in list:
            if self.componentsEquals( listI, component):
                # Increment the instance count of the existing row.
                listI['instances'] += 1
                beamExistInList = True
                break

        if not beamExistInList:
            self.addComponentToList(list, component, True)    

    @classmethod
    def getLengthAxis(self, component):   
        drawPoints = False

        tolerance = 0.1
        proximityTolerance = -1.0

        X_AXIS = adsk.core.Vector3D.create(1, 0, 0)
        Y_AXIS = adsk.core.Vector3D.create(0, 1, 0)
        Z_AXIS = adsk.core.Vector3D.create(0, 0, 1)

        nX_AXIS = adsk.core.Vector3D.create(-1, 0, 0)
        nY_AXIS = adsk.core.Vector3D.create(0, -1, 0)
        nZ_AXIS = adsk.core.Vector3D.create(0, 0, -1)

        hitFaces = [0, 0, 0] #x, y, z

        unHitPoints = [0, 0, 0] #x, y, z

        if drawPoints:
            sketches = component.sketches
            sketchXY = sketches.add(component.xYConstructionPlane)
            sketchYZ = sketches.add(component.yZConstructionPlane)
            sketchXZ = sketches.add(component.xZConstructionPlane)

            # Get sketch points
            sketchPointsXY = sketchXY.sketchPoints
            sketchPointsYZ = sketchYZ.sketchPoints
            sketchPointsXZ = sketchXZ.sketchPoints

        # findBRepUsingRay
        # https://forums.autodesk.com/t5/fusion-360-api-and-scripts/i-could-not-able-to-run-this-add-in/td-p/9428425
        
        #for x in frange(component.boundingBox.minPoint.x, component.boundingBox.maxPoint.x, (component.boundingBox.maxPoint.x - component.boundingBox.minPoint.x) * tolerance):
        for x in getRange(component.boundingBox.minPoint.x, component.boundingBox.maxPoint.x, tolerance):
            for y in getRange(component.boundingBox.minPoint.y, component.boundingBox.maxPoint.y, tolerance):
                point = adsk.core.Point3D.create(x, y, 0)
                if drawPoints:
                    sketchPoint = sketchPointsXY.add(point)

                hits = 0

                hit_faces = component.findBRepUsingRay(point, Z_AXIS, 0, proximityTolerance) # BRepBodyEntityType
                hitFaces[2] += hit_faces.count
                hits += hit_faces.count
                hit_faces = component.findBRepUsingRay(point, nZ_AXIS, 0, proximityTolerance) # BRepBodyEntityType
                hitFaces[2] += hit_faces.count                
                hits += hit_faces.count

                if hits == 0:
                    unHitPoints[2] += 1



        for x in getRange(component.boundingBox.minPoint.x, component.boundingBox.maxPoint.x, tolerance):
            for z in getRange(component.boundingBox.minPoint.z, component.boundingBox.maxPoint.z, tolerance):
                point = adsk.core.Point3D.create(x, 0, z)
                if drawPoints:
                    sketchPoint = sketchPointsXY.add(point)

                hits = 0

                hit_faces = component.findBRepUsingRay(point, Y_AXIS, 0, proximityTolerance) # BRepBodyEntityType
                hitFaces[1] += hit_faces.count
                hits += hit_faces.count
                hit_faces = component.findBRepUsingRay(point, nY_AXIS, 0, proximityTolerance) # BRepBodyEntityType
                hitFaces[1] += hit_faces.count
                hits += hit_faces.count

                if hits == 0:
                    unHitPoints[1] += 1

        for y in getRange(component.boundingBox.minPoint.y, component.boundingBox.maxPoint.y, tolerance):
            for z in getRange(component.boundingBox.minPoint.z, component.boundingBox.maxPoint.z, tolerance):
                point = adsk.core.Point3D.create(0, y, z)
                if drawPoints:
                    sketchPoint = sketchPointsXY.add(point)

                hits = 0

                hit_faces = component.findBRepUsingRay(point, X_AXIS, 0, proximityTolerance) # BRepBodyEntityType
                hitFaces[0] += hit_faces.count
                hits += hit_faces.count
                hit_faces = component.findBRepUsingRay(point, nX_AXIS, 0, proximityTolerance) # BRepBodyEntityType
                hitFaces[0] += hit_faces.count
                hits += hit_faces.count

                if hits == 0:
                    unHitPoints[0] += 1

        # if hitFaces[0] < hitFaces[1] and hitFaces[0] < hitFaces[2]:
        #     return 0
        
        # if hitFaces[1] < hitFaces[0] and hitFaces[1] < hitFaces[2]:
        #     return 1       
       
        # if hitFaces[2] < hitFaces[0] and hitFaces[2] < hitFaces[1]:
        #     return 2


        if unHitPoints[0] < unHitPoints[1] and unHitPoints[0] < unHitPoints[2]:
            return 0
        
        if unHitPoints[1] < unHitPoints[0] and unHitPoints[1] < unHitPoints[2]:
            return 1       
       
        if unHitPoints[2] < unHitPoints[0] and unHitPoints[2] < unHitPoints[1]:
            return 2

        return -1


    @classmethod
    # @timing
    def getVolume(self, component):   
        volume = 0
        bodies = component.bRepBodies
        for bodyK in bodies:
            if bodyK.isSolid:
                volume += bodyK.volume        
        return volume

    @classmethod
    # @timing
    def componentsEquals(self, listItem, componentB):

        componentA = listItem['component']

        if round(listItem['volume'], 2) != round(self.getVolume(componentB),2):
            return False
        
        # physicalPropertiesA = componentA.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)
        # physicalPropertiesB = componentB.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy)

        # # Get principal axes from physical properties
        # (retVal, xAxis0, yAxis0, zAxis0) = physicalPropertiesA.getPrincipalAxes()   
        
        # # Get the moments of inertia about the principal axes. Unit for returned values is kg/cm^2.
        # (retValA,i1A,i2A,i3A) = physicalPropertiesA.getPrincipalMomentsOfInertia()
        # (retValB,i1B,i2B,i3B) = physicalPropertiesB.getPrincipalMomentsOfInertia()

        if listItem['i1'] == 0:
            (retValA,i1A,i2A,i3A) = getPrincipalMomentsOfInertia(componentA)
            if not retValA:
                return False

            listItem['i1'] = i1A
            listItem['i2'] = i2A
            listItem['i3'] = i3A
            
        # (retValA,i1A,i2A,i3A) = getPrincipalMomentsOfInertia(componentA)
        (retValB,i1B,i2B,i3B) = getPrincipalMomentsOfInertia(componentB)

        if not retValB:
            return False

        return round(listItem['i1'],4) == round(i1B,4) and round(listItem['i2'],4) == round(i2B,4) and round(listItem['i3'],4) == round(i3B,4) 



    def extractBOM(self):
        global newComp
        # newComp = createNewComponent()
        #if newComp is None:
        #ui.messageBox('New component failed to create', 'New Component Failed')

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        title = 'Extract Hash BOM'
        if not design:
            ui.messageBox('No active design', title)
            return




        # Get all occurrences in the root component of the active design
        root = design.rootComponent
        occs = root.allOccurrences

        design.activateRootComponent()
        
        visibleTopLevelComp = []
        for occ in root.occurrences:
            if occ.isLightBulbOn:
                visibleTopLevelComp.append(occ)


        # Gather information about each unique component
        bom = []
        beams = []

        for occ in occs:
            comp = occ.component

            if self._beamFilterStr in comp.name:
                self.collectBeam(beams, comp)

            if self._bomFilterStr in comp.name:
                self.collectInstance(bom, comp)

                # instanceExistInBom = False
                # for bomI in bom:
                #     if bomI['component'] == comp:
                #         # Increment the instance count of the existing row.
                #         bomI['instances'] += 1
                #         instanceExistInBom = True
                #         break

                # if not instanceExistInBom:
                #     # Gather any BOM worthy values from the component
                #     volume = 0
                #     bodies = comp.bRepBodies
                #     for bodyK in bodies:
                #         if bodyK.isSolid:
                #             volume += bodyK.volume
                    
                #     if volume > 0:
                #         # Add this component to the BOM
                #         bom.append({
                #             'component': comp,
                #             'name': comp.name,
                #             'instances': 1,
                #             'volume': str(round(volume, 2)) 
                #         })

        if len(bom) == 0 and len(beams) == 0:
            ui.messageBox('No hash items found', 'Teh Hash BOM')
            return


        bom.sort(key=lambda x: x['name'], reverse=False)
        beams.sort(key=lambda x: x['name'], reverse=False)


        fileDialog = ui.createFileDialog()
        fileDialog.isMultiSelectEnabled = False
        fileDialog.title = " filename"
        fileDialog.filter = 'html (*.html)'
        fileDialog.initialFilename =  product.rootComponent.name
        fileDialog.filterIndex = 0
        dialogResult = fileDialog.showSave()
        if dialogResult == adsk.core.DialogResults.DialogOK:
            filename = fileDialog.filename
            path, file = os.path.split(filename)
            #path = os.path.dirname(filename)
            dst_directory = os.path.splitext(filename)[0] + '_files'
        else:
            return

        for bomItem in bom:
            takeImage(bomItem['component'], occs, dst_directory)
            Unisolate(visibleTopLevelComp)
        
        for bomItem in beams:
            takeImage(bomItem['component'], occs, dst_directory)
            Unisolate(visibleTopLevelComp)        
        
        #ShowAll(occs)
      

        # Display the BOM
        # title = spacePadRight('Name', 25) + spacePadRight('Instances', 15) + 'Volume\n'
        # msg = title + '\n' + walkThrough(bom)
        
        output = open(filename, 'w', encoding='utf-8')

        output.writelines(buildHtmlHeader(dst_directory, product.rootComponent.name))
        
        if len(bom) > 0:
            output.writelines(buildTable(bom, dst_directory, 'BOM'))
        
        if len(beams) > 0:
            output.writelines(buildTable(beams, dst_directory, 'Beam'))

        if self._exportToCSV:
            buildCSV(bom, os.path.splitext(filename)[0] + '_bom')
            buildCSV(beams, os.path.splitext(filename)[0] + '_beam')

        output.writelines(buildHtmlFooter(dst_directory))
        # output.writelines(msg)
        output.close()


        dialogResult = ui.messageBox('Hash BOM Extracted. Open file?', 'Teh Hash BOM', adsk.core.MessageBoxButtonTypes.OKCancelButtonType, adsk.core.MessageBoxIconTypes.InformationIconType)
        if dialogResult == adsk.core.DialogResults.DialogOK:
            openWithDefaultApplication(filename)


def GetConvertUnit():
    #unitsMgr = _des.unitsManager
    unitsMgr = app.activeProduct.unitsManager
    defLenUnit = unitsMgr.defaultLengthUnits
    return unitsMgr.convert(1, unitsMgr.internalUnits, defLenUnit)


def openWithDefaultApplication(filename):
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', filename))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(filename)
    else:                                   # linux variants
        subprocess.call(('xdg-open', filename))


def Unisolate(occs):
    for occ in occs:
        occ.isLightBulbOn = True

def HideAll(occs):
    for occ in occs:
        comp = occ.component
        comp.isBodiesFolderLightBulbOn = False

def ShowAll(occs):
    for occ in occs:
        comp = occ.component
        #comp.isBodiesFolderLightBulbOn = True


def takeImage(component, occs, path):

    #HideAll(occs)

    cameraTarget = False
    occurrence = False

    for occ in occs:
        comp = occ.component

        if comp == component and not cameraTarget:
            cameraTarget = adsk.core.Point3D.create(occ.transform.translation.x, occ.transform.translation.y, occ.transform.translation.z)
            #comp.isBodiesFolderLightBulbOn = True
            occurrence = occ
        
            

    if cameraTarget:

        if occurrence.assemblyContext and occurrence.assemblyContext.isReferencedComponent:
            occurrence.assemblyContext.isIsolated = True
            
            hiddenChildren = []
            for childOccurrence in occurrence.assemblyContext.component.allOccurrences:
                hiddenChild = childOccurrence.component

                if hiddenChild != component and hiddenChild.isBodiesFolderLightBulbOn:
                    hiddenChildren.append(hiddenChild)
                    hiddenChild.isBodiesFolderLightBulbOn = False

        else:
            occurrence.isIsolated = True

        viewport = app.activeViewport
        camera = viewport.camera

        camera.target = cameraTarget
        camera.isFitView = True
        camera.isSmoothTransition = False
        app.activeViewport.camera = camera
        
        app.activeViewport.refresh()
        adsk.doEvents()

        success = app.activeViewport.saveAsImageFile(path + '/' + component.id  + '.png', 128, 128)
        if not success:
            ui.messageBox('Failed saving viewport image.')
        
        if occurrence.assemblyContext and occurrence.assemblyContext.isReferencedComponent:

            occurrence.assemblyContext.isIsolated = False  

            for hiddenChild in hiddenChildren:
                hiddenChild.isBodiesFolderLightBulbOn = True            

        else:
            occurrence.isIsolated = False



def spacePadRight(value, length):
    pad = ''
    if type(value) is str:
        paddingLength = length - len(value) + 1
    else:
        paddingLength = length - value + 1
    while paddingLength > 0:
        pad += ' '
        paddingLength -= 1

    return str(value) + pad

def walkThrough(bom):
    mStr = ''
    for item in bom:
        mStr += spacePadRight(item['name'], 25) + str(spacePadRight(item['instances'], 15)) + str(item['volume']) + '\n'
    return mStr



def buildCSV(bom, fileName):
    with open(fileName + '.csv', 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
        writer.writerow(['name', 'instances', 'volume', 'boundingX', 'boundingY', 'boundingZ', 'is_profile', 'profile_size', 'profile_length'])
        for item in bom:
            name =  item['name']
            writer.writerow([name, item['instances'], item['volume'], item['boundingX'], item['boundingY'], item['boundingZ'], item['is_profile'], item['profile_size'], item['profile_length']])

def buildTable(bom, imageDirectory, tableName):
    path, dir = os.path.split(imageDirectory)

    mStr = '<script type="text/javascript">'
    mStr += 'var generated' + tableName + 'Table = ['

    # mStr = '<h1>'+tableName+'</h1>'
    # mStr += '<table  class="table table-striped table-hover">'
    # mStr += '<thead><tr>'
    # mStr += '<th scope="col">image</th>'
    # mStr += '<th scope="col">name</th>'
    # mStr += '<th scope="col">instances</th>'
    # mStr += '<th scope="col">volume</th>'
    # mStr += '<th scope="col">size</th>'
    # mStr += '<th scope="col">length</th>'
    # mStr += '<th scope="col">total length</th>'
    # mStr += '</tr></thead> <tbody>'
    # mStr += '\n'
    mStr += '\n'
    for item in bom:

        mStr += '{'
        mStr += 'id: "' + item['component'].id + '",'
        mStr += 'name: "' + item['name'] + '",'
        mStr += 'image: "' + dir +'/'+ item['component'].id +'.png' + '",'
        mStr += 'instances: ' + '%g' % item['instances'] + ','
        mStr += 'volume: ' + '%g' % (item['volume']) + ','
        mStr += 'boundingX: ' + '%g' % (item['boundingX']) + ','
        mStr += 'boundingY: ' + '%g' % (item['boundingY']) + ','
        mStr += 'boundingZ: ' + '%g' % (item['boundingZ']) + ','
        mStr += 'is_profile: ' + '%g' %(item['is_profile']) + ','
        mStr += 'profile_axis: ' + '%g' % (item['profile_axis']) + ','
        mStr += 'profile_size: "' + str(item['profile_size']) + '",'
        mStr += 'profile_length: ' + '%g' % (item['profile_length']) + ''
        mStr += '},'
        mStr += '\n'

        # mStr += '<tr>'
        # mStr += '<td><img src="' +dir +'/'+ item['component'].id +'.png"></td>'
        # mStr += '<td>'+  name + '<br>' + '%g' % (item['boundingX']) + 'x'+'%g' % (item['boundingY']) + 'x'+'%g' % (item['boundingZ']) + '</td>'
        # mStr += '<td>'+  '%g' % item['instances'] +'</td>'
        # mStr += '<td>'+  '%g' % (item['volume']) +'</td>'
        # mStr += '<td>'+  str(item['profile_size']) +'</td>'
        # if item['profile_length']:
        #     mStr += '<td>'+  '%g' % (item['profile_length']) +'</td>'
        #     mStr += '<td>'+  '%g' % (item['profile_length'] * item['instances']) +'</td>'
        # else:
        #     mStr += '<td>-</td>'
        #     mStr += '<td>-</td>'
       
        # mStr += '</tr>'
        # mStr += '\n'

    mStr += ']; </script>'
    return mStr

def buildHtmlHeader(dst_directory, name):
    # copyfile(addin_path + '/resources/bootstrap.min.css', dst_directory + '/bootstrap.min.css')
    # copyfile(addin_path + '/resources/bootstrap.min.js', dst_directory + '/bootstrap.min.js')
    # copyfile(addin_path + '/resources/jquery-3.3.1.slim.min.js', dst_directory + '/jquery-3.3.1.slim.min.js')
    # copyfile(addin_path + '/resources/popper.min.js', dst_directory + '/popper.min.js')

    copyfile(addin_path + '/resources/vue/css/chunk-vendors.css', dst_directory + '/chunk-vendors.css')
    copyfile(addin_path + '/resources/vue/js/app.min.js', dst_directory + '/app.min.js')
    copyfile(addin_path + '/resources/vue/js/chunk-vendors.min.js', dst_directory + '/chunk-vendors.min.js')
    copyfile(addin_path + '/resources/Icon_128.png', dst_directory + '/Icon_128.png')

    copyfile(addin_path + '/resources/fonts/materialdesignicons.css', dst_directory + '/materialdesignicons.css')
    copyfile(addin_path + '/resources/fonts/materialdesignicons-webfont.woff2', dst_directory + '/materialdesignicons-webfont.woff2')
    copyfile(addin_path + '/resources/fonts/roboto-latin-700.woff2', dst_directory + '/roboto-latin-700.woff2')
    copyfile(addin_path + '/resources/fonts/roboto-latin-400.woff2', dst_directory + '/roboto-latin-400.woff2')
    copyfile(addin_path + '/resources/fonts/roboto-latin-500.woff2', dst_directory + '/roboto-latin-500.woff2')

    path, dir = os.path.split(dst_directory)


    mStr = '<!doctype html> \
<html lang="en">\
  <head>\
    <!-- Required meta tags -->\
    <meta charset="utf-8">\
    <meta name="viewport" content="width=device-width,initial-scale=1"> \
    <link rel="stylesheet" href="' +dir +'/chunk-vendors.css"> \
        <style type="text/css">\
        /* MaterialDesignIcons.com */\
            @font-face {\
            font-family: "Material Design Icons";\
            src:  url("' +dir +'/materialdesignicons-webfont.woff2") format("woff2");\
            font-weight: normal;\
            font-style: normal;\
        }\
        @font-face {\
            font-family: \'Roboto\';\
            font-style: normal;\
            font-weight: 400;\
            font-display: swap;\
            src: url(' +dir +'/roboto-latin-400.woff2) format(\'woff2\');\
        }\
        @font-face {\
            font-family: \'Roboto\';\
            font-style: normal;\
            font-weight: 500;\
            font-display: swap;\
            src: url(' +dir +'/roboto-latin-400.woff2) format(\'woff2\');\
        }\
    </style>\
    <link rel="stylesheet" href="' +dir +'/materialdesignicons.css">\
    <title>'+name+' from Teh Hash BOM</title> \
  </head>\
  <body>\
      <noscript><strong>We\'re sorry but teh_hash_bom doesn\'t work properly without JavaScript enabled. Please enable it to continue.</strong></noscript>\
          <div id="app"></div><script type="text/javascript">var asset_dirrectory="' +dir +'";</script>'
    return mStr

def buildHtmlFooter(dst_directory):
    path, dir = os.path.split(dst_directory)

    mStr = '<script src="' +dir +'/chunk-vendors.min.js"></script><script src="' +dir +'/app.min.js"></script>\
    </body>\
</html>'
    return mStr    