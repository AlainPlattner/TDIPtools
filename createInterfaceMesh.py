import pygimli as pg
import numpy as np

def createInterfaceMesh(data, filename, delimiter='\t', **kwargs):
    """ Create a mesh with interfaces given by x and z coordinates in the 
    provided file 'filename'. This is for a single interface

    Besides the data and filename, also provide all the options for the 
    mesh. 

    For example:
    
    from pybert import tdip
    from createInterfaceMesh import *
    ip = tdip.TDIPdata('mydatafile.txt')
    mesh = createInterfaceMesh(data=ip.data, filename='myinterfacefile.txt', 
                               quality=33, area=-1, paraDX=0.05, 
                               paraMaxCellSize=0.5, paraDepth=2)
    pg.show(mesh)
    pg.wait()

    Last modified by aplattner-at-alumni.ethz.ch, May 12 2021
    
    """

    # Load coordinates of interface
    interf =  np.loadtxt(filename, delimiter)  

    # Create PLC from the interface coordinates
    intPoly = pg.meshtools.createPolygon(verts=interf, isClosed=False)
    
    # Create PLC for the world using info from data dn provided
    # options
    worldPoly = pg.meshtools.createParaMeshPLC(data.sensorPositions(), **kwargs)
    
    # Merge the two
    PLC = pg.meshtools.mergePLC([intPoly, worldPoly])

    # Create the mesh
    mesh = pg.meshtools.createMesh(PLC)
    mesh.createNeighbourInfos()

    return mesh






def createInterfacesMesh(data, filenames, delimiter='\t', **kwargs):
    """ Create a mesh with interfaces given by x and z coordinates in the 
    provided file 'filename'. This is for a list of filenames

    Besides the data and filenames, also provide all the options for the 
    mesh. 

    For example:
    
    from pybert import tdip
    from createInterfaceMesh import *
    ip = tdip.TDIPdata('mydatafile.txt')
    mesh = createInterfaceMesh(data=ip.data, filename=['interface1.txt','interface2.txt'], 
                               quality=33, area=-1, paraDX=0.05, 
                               paraMaxCellSize=0.5, paraDepth=2)
    pg.show(mesh)
    pg.wait()

    Last modified by aplattner-at-alumni.ethz.ch, May 12 2021
    
    """

    # Load coordinates of interfaces
    for i in range(0,len(filenames)):
        interf =  np.loadtxt(filenames[i], delimiter=delimiter)  
        
        # Create PLC from the interface coordinates
        intPoly = pg.meshtools.createPolygon(verts=interf, isClosed=False)

        # Append the newly created PLC to the already existing ones
        if i==0:
            intPolys = intPoly
        else:
            intPolys = pg.meshtools.mergePLC([intPolys, intPoly])
            
    # Create PLC for the world using info from data dn provided
    # options
    worldPoly = pg.meshtools.createParaMeshPLC(data.sensorPositions(), **kwargs)
    
    # Merge the PLC
    PLC = pg.meshtools.mergePLC([intPolys, worldPoly])

    # Create the mesh
    mesh = pg.meshtools.createMesh(PLC)
    mesh.createNeighbourInfos()

    return mesh
