#Author-TehDmitry
#Description-Create a BOM by hashtag

import adsk.core, adsk.fusion, traceback
import subprocess, os, platform
from shutil import copyfile

# Globals
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

addin_path = os.path.dirname(os.path.realpath(__file__)) 

defaultFilterStr = '#bom'


# global set of event handlers to keep them referenced for the duration of the command
handlers = []

def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return
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

            inputs.addStringValueInput('filterString', 'Filter String', defaultFilterStr)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class BOMCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cameraBackup = app.activeViewport.camera

            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            bom = BOM()
            for input in inputs:
                if input.id == 'filterString':
                    bom.filterString = input.value

            bom.extractBOM()
            args.isValidResult = True

            app.activeViewport.camera = cameraBackup

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        

        # Force the termination of the command.
        adsk.terminate()   


class BOM:
    def __init__(self):
        self._defaultFilterStr = defaultFilterStr

    #properties
    @property
    def filterString(self):
        return self._defaultFilterStr
    @filterString.setter
    def filterString(self, value):
        self._defaultFilterStr = value

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
        for occ in occs:
            comp = occ.component
            if self._defaultFilterStr in comp.name:

                jj = 0
                for bomI in bom:
                    if bomI['component'] == comp:
                        # Increment the instance count of the existing row.
                        bomI['instances'] += 1
                        break
                    jj += 1

                if jj == len(bom):
                    # Gather any BOM worthy values from the component
                    volume = 0
                    bodies = comp.bRepBodies
                    for bodyK in bodies:
                        if bodyK.isSolid:
                            volume += bodyK.volume
                    
                    if volume > 0:
                        # Add this component to the BOM
                        bom.append({
                            'component': comp,
                            'name': comp.name,
                            'instances': 1,
                            'volume': str(round(volume, 2)) 
                        })

        bom.sort(key=lambda x: x['name'], reverse=False)

        for bomItem in bom:
            takeImage(bomItem['component'], occs, dst_directory)
            Unisolate(visibleTopLevelComp)
        
        
        
        #ShowAll(occs)
      

        # Display the BOM
        # title = spacePadRight('Name', 25) + spacePadRight('Instances', 15) + 'Volume\n'
        # msg = title + '\n' + walkThrough(bom)
        
        output = open(filename, 'w')

        output.writelines(buildHtmlHeader(dst_directory, product.rootComponent.name))
        output.writelines(buildTable(bom, dst_directory))
        output.writelines(buildHtmlFooter())
        # output.writelines(msg)
        output.close()


        dialogResult = ui.messageBox('Hash BOM Extracted. Open file?', 'Teh Hash BOM', adsk.core.MessageBoxButtonTypes.OKCancelButtonType, adsk.core.MessageBoxIconTypes.InformationIconType)
        if dialogResult == adsk.core.DialogResults.DialogOK:
            openWithDefaultApplication(filename)




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

        if occurrence.assemblyContext.isReferencedComponent:
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
        
        if occurrence.assemblyContext.isReferencedComponent:

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




def buildTable(bom, imageDirectory):
    path, dir = os.path.split(imageDirectory)

    mStr = '<table  class="table table-striped table-hover">'
    mStr += '<thead><tr>'
    mStr += '<th scope="col">image</th>'
    mStr += '<th scope="col">name</th>'
    mStr += '<th scope="col">instances</th>'
    mStr += '<th scope="col">volume</th>'
    mStr += '</tr></thead> <tbody>'
    mStr += '\n'

    for item in bom:

#        name =  str(item['name'].decode('utf8'))
        name =  item['name'].encode().decode('windows-1251')

        mStr += '<tr>'
        mStr += '<td><img src="' +dir +'/'+ item['component'].id +'.png"></td>'
        mStr += '<td>'+  name +'</td>'
        mStr += '<td>'+  str(item['instances']) +'</td>'
        mStr += '<td>'+  str(item['volume']) +'</td>'
        mStr += '</tr>'
        mStr += '\n'

    mStr += ' </tbody></table>'
    return mStr

def buildHtmlHeader(dst_directory, name):
    copyfile(addin_path + '/resources/bootstrap.min.css', dst_directory + '/bootstrap.min.css')
    copyfile(addin_path + '/resources/bootstrap.min.js', dst_directory + '/bootstrap.min.js')
    copyfile(addin_path + '/resources/jquery-3.3.1.slim.min.js', dst_directory + '/jquery-3.3.1.slim.min.js')
    copyfile(addin_path + '/resources/popper.min.js', dst_directory + '/popper.min.js')

    path, dir = os.path.split(dst_directory)


    mStr = '<!doctype html> \
<html lang="en">\
  <head>\
    <!-- Required meta tags -->\
    <meta charset="utf-8">\
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">\
    <link rel="stylesheet" href="' +dir +'/bootstrap.min.css"> \
    <script src="' +dir +'/jquery-3.3.1.slim.min.js"></script>\
    <script src="' +dir +'/popper.min.js"></script>\
    <script src="' +dir +'/bootstrap.min.js"></script>\
    <title>Teh Hash BOM for '+name+'</title> \
  </head>\
  <body>\
      <div class="container"><div class="row"><div class="col"><h4>Teh Hash BOM for</h4><h1>'+name+'</h1>'
    return mStr

def buildHtmlFooter():
    mStr = '</div></div></div>\
    </body>\
</html>'
    return mStr    