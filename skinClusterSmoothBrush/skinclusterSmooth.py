# smooth SkinClusterWeights
from maya.api import OpenMaya as om
from maya import cmds
from maya import mel

sel = cmds.ls(sl=1)[0]
skc = cmds.ls(cmds.listHistory(sel), type='skinCluster')


def nameToDagPath(name):
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDagPath(0)


# flood mode
if skc:
    skc = skc[0]
    connectedVertices = []
    vtxIt = om.MItMeshVertex(nameToDagPath(sel))
    while not vtxIt.isDone():
        connectedVertices.append(vtxIt.getConnectedVertices())
        vtxIt.next()

    numJoints = len(cmds.skinCluster(skc, q=1, inf=1))

    newWeightsArray = []
    for vtx, neighbours in enumerate(connectedVertices):
        influenceWeights = []
        for ji in range(numJoints):
            mainWeight = cmds.getAttr('{}.weightList[{}].weights[{}]'.format(skc, vtx, ji))
            for nv in neighbours:
                mainWeight += cmds.getAttr('{}.weightList[{}].weights[{}]'.format(skc, nv, ji))
            influenceWeights.append(mainWeight / (len(neighbours) + 1))

        newWeightsArray.append(influenceWeights)

    for vtx, newWeights in enumerate(newWeightsArray):
        for inf, weight in enumerate(newWeights):
            cmds.setAttr('{}.weightList[{}].weights[{}]'.format(skc, vtx, inf), weight)

# paint Mode
vtxIt = None
numJoints = 0


def linearInterpolation(startPoint, startValue,
                        endPoint, endValue, currentValue):
    interPolation = startPoint + (currentValue - startValue) * (
                (endPoint - startPoint) / (endValue - startValue))
    return interPolation


def smoothSkinWeightsSetup():
    global sel
    global skc
    global vtxIt
    global numJoints
    sel = cmds.ls(sl=1)[0]
    skc = cmds.ls(cmds.listHistory(sel), type='skinCluster')
    vtxIt = om.MItMeshVertex(nameToDagPath(sel))
    numJoints = len(cmds.skinCluster(skc, q=1, inf=1))
    if skc:
        skc = skc[0]


def smoothVertexWeight(index, val):
    vtxIt.setIndex(index)
    neighbours = vtxIt.getConnectedVertices()
    for ji in range(numJoints):
        oldWeight = cmds.getAttr('{}.weightList[{}].weights[{}]'.format(skc, index, ji))
        mainWeight = oldWeight
        for nv in neighbours:
            mainWeight += cmds.getAttr('{}.weightList[{}].weights[{}]'.format(skc, nv, ji))
        averagedWeight = mainWeight / (len(neighbours) + 1)
        brushValue = linearInterpolation(oldWeight, 0, averagedWeight, 1, val)
        cmds.setAttr('{}.weightList[{}].weights[{}]'.format(skc, index, ji), brushValue)


# set the init mel script
mel.eval('''
global proc string smoothSkinWeightsCtx(string $context){
    python ("smoothSkinWeightsSetup()");
    return $context;
}
global proc string smoothSkinWeightsInit(string $name)
{
	return ("-dt worldV -n local");
}
global proc smoothSkinWeightsFinish( int $slot ){
}
global proc smoothSkinWeights(int $slot, int $index, float $val, float $Dx, float $Dy, float $Dz, float $Nx, float $Ny, float $Nz)
{
    python ("smoothVertexWeight(\"+$index+\", \"+ $val +\")\");
}'''
         )
if skc:
    cmds.ScriptPaintTool()
    cmds.artUserPaintCtx(cmds.currentCtx(),
                         e=True,
                         tsc='smoothSkinWeightsCtx',
                         ic='smoothSkinWeightsInit',
                         fc='smoothSkinWeightsFinish',
                         svc='smoothSkinWeights',
                         )