#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#************************************************************************************
#**          Generador de mapas tematicos de transportes para INECO
#**  
#**  
#**  Author:	Miguel Angel de la Fuente
#**  Date:		27/04/2018
#**  Version:   1.1
#**  Target:    ArcMap 10.4
#************************************************************************************
#**Input:
#**      shp:zonificaciones
#**      csv:Viajes/dia Origen destino
#**Output:
#**      pdf: Mapa temático en funcion de si una region es origen o destino y del
#**           numero de viajes/dia entre destino/origen.
#************************************************************************************
"""
import arcpy
import pythonaddins
import os
import csv
import logging
import time

csv.register_dialect('unixpwd', delimiter=';', quoting=csv.QUOTE_NONE)
#Tratamiento csv

class TipoViaje(object):
    values = ['OrigenDestino','DestinoOrigen']

    class __metaclass__(type):
        def __getattr__(self, name):
            return self.values.index(name)
    

def codigosRegiones(csvViajes):
    
    with open(csvViajes,'rb') as fin:
        codigos=[]
        n=0
        for row in csv.reader(fin,'unixpwd'):
            if n!=0:
                codigos.append(str(row[0]))
            n=n+1
    return set(codigos)

def sumaViajesOrigen(codZona):
    
    with open(csvViajes,'rb') as fin:
        
        headerline = fin.next()
        total = 0
        for row in csv.reader(fin,'unixpwd'):
            
            #if str(row[0])=='ast_02':
            if str(row[0])==codZona:
                total += int(row[3])
        return total

def obetenDestinos(codZona):
    
    with open(csvViajes,'rb') as fin:
        
        headerline = fin.next()
        destinos=[]
        for row in csv.reader(fin,'unixpwd'):
            
            if str(row[0])==codZona:
                destinos.append(str(row[1]))
        return destinos

def obtenNumViajesDestino(ID_Origen,ID_Destino):
    
    with open(csvViajes,'rb') as fin:
        
        headerline = fin.next()
        destino=0
        for row in csv.reader(fin,'unixpwd'):
            
            if str(row[0])==ID_Origen and str(row[1])==ID_Destino:
                destino=row[3]
                break
        return destino

def creaCadenaBusquedaDestinos(codZonaOrigen):

    destinos=obetenDestinos(codZonaOrigen)
    where='"ID" IN ('
    n=1
    for destino in destinos:
        
        if n<len(destinos):
            where=where + "'" + destino + "',"
        else:
            where=where + "'" + destino + "')"

        n=n+1
    return where


def creaOrigen(codZona,nombreLyr,mxd):
    queryString = '"ID" = \'' + codZona + '\''
    
    origen=arcpy.MakeFeatureLayer_management(zonificacion, nombreLyr, queryString)
    origen=arcpy.mapping.ListLayers(mxd, nombreLyr)[0]
    return origen
    

def creaDestino(codZonaOrigen,nombreLyr,mxd):
    
    condBusquedadestinos=creaCadenaBusquedaDestinos(codZonaOrigen)
   
    destino=arcpy.MakeFeatureLayer_management(zonificacion, nombreLyr, condBusquedadestinos)
    destino=arcpy.mapping.ListLayers(mxd, nombreLyr)[0]
    
    return destino

def creaLocalizacion(codZonaOrigen,nombreLyr,mxd):
    condBusquedadestinos=creaCadenaBusquedaDestinos(codZonaOrigen)
    Localizacion=arcpy.MakeFeatureLayer_management(zonificacion, nombreLyr, condBusquedadestinos)
    Localizacion= arcpy.mapping.ListLayers(mxd, "Localizacion")[0]
    return Localizacion



def deleteOrigen():
    arcpy.Delete_management("Origen")



def ActualizaViajesOrigen(codZonaOrigen,origen):
    fields = ['Viajes']
    with arcpy.da.UpdateCursor(origen, fields) as cursor:
        
        for row in cursor:
            totalViajesOrigen=sumaViajesOrigen(codZonaOrigen)
            row[0] = totalViajesOrigen

            try:
                cursor.updateRow(row)
            except:
                print(totalViajesOrigen)

def ActualizaViajesDestino(ID_Origen,destino):
    fields2 = ['ID','Viajes']
    with arcpy.da.UpdateCursor(destino, fields2) as cursor:
        
        for row in cursor:
            NumViajesDestino=obtenNumViajesDestino(ID_Origen,row[0])
            row[1] = int(NumViajesDestino)

            cursor.updateRow(row)

def ReseteaViajes(lyr):
    fields2 = ['ID','Viajes']
    with arcpy.da.UpdateCursor(lyr, fields2) as cursor:
        
        for row in cursor:
            NumViajesDestino=0
            row[1] = int(NumViajesDestino)

            cursor.updateRow(row)

def ObtenNombreRegion(ID_Zona,lyrZonificacion):
    
    fields3 = ['ID','Nombre']
    NombreRegion=""
    with arcpy.da.SearchCursor(lyrZonificacion, fields3) as cursor:
        
        for row in cursor:
            if row[0]==ID_Zona:
                NombreRegion=row[1]
                return NombreRegion


def printDimensionesExtension(Extension):
    print(Extension.XMax)
    print(Extension.XMin)
    print(Extension.YMax)
    print(Extension.YMin)

def MergeaExtensiones(lyrsExtents,Margen):
    xmax=0
    
    for lyr in lyrsExtents:

        if xmax==0:
            xmax=lyr.XMax+Margen
            ymax=lyr.YMax+Margen
            xmin=lyr.XMin-Margen
            ymin=lyr.YMin-Margen

        if lyr.XMax>xmax:
            xmax=lyr.XMax+Margen
            
        if lyr.YMax>ymax:
            ymax=lyr.YMax+Margen
           
        if lyr.XMin<xmin:
            xmin=lyr.XMin-Margen
            
        if lyr.YMin<ymin:
            ymin=lyr.YMin-Margen
            

    ExtensionMergeada=arcpy.Extent(xmin,ymin,xmax,ymax)
    
    return ExtensionMergeada

def borraCapasEntrada():
    

    #arcpy.Delete_management("destino")
    #arcpy.Delete_management("origen")
    arcpy.Delete_management("zonificacion")
    arcpy.Delete_management("Zona de destino de los viajes")
    arcpy.Delete_management("Zona de origen de los viajes")
    arcpy.Delete_management("Num. viajes")
    

def actualizaTituloLayout(Titulo,mxd):
        for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):
        
            elm.text = Titulo
            elm.elementWidth=6.0

def mergeExtensionOrigenDestino(dataFrame,lyrDestino,lyrOrigen):
        extents=[]
        extentDestino=lyrDestino.getExtent()
        extentOrigen=lyrOrigen.getExtent()
        extents.append(extentDestino)
        extents.append(extentOrigen)
        
        extentOrigenDestino=MergeaExtensiones(extents,1000)
        
        dataFrame.extent=extentOrigenDestino

        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()

def aplicaEstilos(destino,origen,df,SimbologiaOrigen,SimbologiaDestino):
        if destino.supports("SHOWLABELS"):
            lc=destino.labelClasses[0]
            lc.expression='[Nombre] + \" \" +  vbCrLf + [Viajes] + \" Viaj./dia \"'
            lc.name="BulletOrigen8"

        if origen.supports("SHOWLABELS"):
            lc=origen.labelClasses[0]
            lc.expression='\"<CLR Magenta=\'0\' Yellow=\'0\' Cyan=\'0\' Black=\'0\'><BOL> \" +[Nombre] + \" \" +  vbCrLf + [Viajes] + \" Viaj/dia \" + \"</BOL></CLR>\" '
            lc.name="Bullet Leader"
            
        arcpy.mapping.UpdateLayer(df, origen, SimbologiaOrigen, True)
        arcpy.mapping.UpdateLayer(df, destino, SimbologiaDestino, True)

        destino.showLabels=True
        origen.showLabels=True

        reclasificaSimbologia(destino)

        origen.transparency=30
        destino.transparency=30

def iluminaLayoutLocalizacion(codZonaOrigen,lyrSimbologiaLocalizacion,mxd):
    mxd = arcpy.mapping.MapDocument('current')
    df = arcpy.mapping.ListDataFrames(mxd,"LocalizacionGeneral")[0]
    mxd.activeView=df
    
    try:
        arcpy.Delete_management("Localizacion")
    except:
         print ("Capa borrada")

    SimbologiaLocalizacion=arcpy.mapping.Layer(lyrSimbologiaLocalizacion)    
    localizacionGeneral=creaLocalizacion(codZonaOrigen,"Localizacion",mxd)
    #localizacionGeneral= arcpy.mapping.ListLayers(mxd, "Localizacion")[0]
    arcpy.mapping.UpdateLayer(df, localizacionGeneral, SimbologiaLocalizacion, True)

def reclasificaSimbologia(lyr):
    if lyr.symbologyType == "GRADUATED_COLORS":
        lyr.symbology.reclassify()

def setOrdenLeyenda(mxd):
    leyenda=arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")[0]
    leyenda.autoAdd=True

    Capa3=arcpy.mapping.ListLayers(mxd, "zonificacion")[0]
    Capa1=arcpy.mapping.ListLayers(mxd, "zona*")[0]
    try:
        Capa2=arcpy.mapping.ListLayers(mxd, "Origen")[0]
    except:
        Capa2=arcpy.mapping.ListLayers(mxd, "Destino*")[0]
    
    Capa1.name="Zona de destino de los viajes"
    Capa2.name="Numero Viajes"
    Capa3.name="Capa3"

    arcpy.RefreshTOC()

    arcpy.mapping.AddLayer(df, Capa1, "TOP")
    arcpy.mapping.AddLayer(df, Capa2, "BOTTOM")
    arcpy.mapping.AddLayer(df, Capa3, "BOTTOM")

    Capa3.visible=False
    Capa2.visible=False
    Capa1.visible=False

    leyenda.autoAdd=True

def aplicaEstilosLeyenda(mxd,leyenda):
        Leyenda=arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")[0]
        LeyendaZonificacionLyr=arcpy.mapping.ListLayers(mxd, "zonifica*")[0]
        estiloLeyendItemZonificacion=arcpy.mapping.ListStyleItems("USER_STYLE", "Legend Items", "*Zon*2")[0]
        leyenda.updateItem(LeyendaZonificacionLyr, estiloLeyendItemZonificacion)

        LeyendaNumViajesLyr=arcpy.mapping.ListLayers(mxd, "Num*")[0]
        estiloLeyendNumViajes=arcpy.mapping.ListStyleItems("USER_STYLE", "Legend Items", "LayerNameDesc")[0]
        leyenda.updateItem(LeyendaNumViajesLyr, estiloLeyendNumViajes)

def creaMarco():
    mxd = arcpy.mapping.MapDocument('current')
    df = arcpy.mapping.ListDataFrames(mxd,"LocalizacionGeneral")[0]
    localizacion = arcpy.mapping.ListLayers(mxd, "Localizacion", df)[0]
    
    extent=localizacion.getExtent()

    array = arcpy.Array([arcpy.Point(extent.XMin,extent.YMin),
                     arcpy.Point(extent.XMax,extent.YMin),
                     arcpy.Point(extent.XMax,extent.YMax),
                     arcpy.Point(extent.XMin,extent.YMax)
                     ])
    polygon = arcpy.Polygon(array)

    # Open an InsertCursor and insert the new geometry
    Marco=arcpy.CreateFeatureclass_management("D:\\Miguel\\BOSLAN\\INECO\\DATOS\\GIS FEVE\\vizcaya\\zonificacion", "Marco.shp", "POLYGON")
     
    cursor = arcpy.da.InsertCursor(Marco, ['SHAPE@'])
    cursor.insertRow([polygon])
    del cursor
    arcpy.Delete_management("Marco")
    arcpy.Delete_management("D:\\Miguel\\BOSLAN\\INECO\\DATOS\\GIS FEVE\\vizcaya\\zonificacion\\marco.shp")

    # Delete cursor object
    
    
    
    

def MapaTematico(codZonaOrigen,lyrZonificacion,lyrSimbologiaOrigen,lyrSimbologiaDestino,lyrSimbologiaLocalizacion,TipoViaje):
    
    #mxd = arcpy.mapping.MapDocument("D:\Miguel\BOSLAN\INECO\INECO\INECO_3.mxd")
    mxd = arcpy.mapping.MapDocument('current')
    df = arcpy.mapping.ListDataFrames(mxd,"Layers")[0]
    mxd.activeView=df

    leyenda=arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")[0]
    leyenda.title="Leyenda"
    leyenda.autoAdd=False
            
    SimbologiaOrigen = arcpy.mapping.Layer(lyrSimbologiaOrigen)
    SimbologiaDestino = arcpy.mapping.Layer(lyrSimbologiaDestino)

    leyenda.autoAdd=True
    arcpy.mapping.AddLayer(df, zonificacion,"TOP")
    leyenda.autoAdd=False

    try:
        arcpy.AddField_management(zonificacion, "Viajes", "LONG", field_length = 50)
    except:
        print ("El campo viajes ya existe")

    
    leyenda.autoAdd=True
    if tv=="DestinoOrigen":
        destino=creaDestino(codZonaOrigen,"Num. viajes",mxd)
        origen=creaOrigen(codZonaOrigen,"Zona de destino de los viajes",mxd)
        
        
    else:
        destino=creaDestino(codZonaOrigen,"Num. viajes",mxd)
        origen=creaOrigen(codZonaOrigen,"Zona de origen de los viajes",mxd)
        
        
    
    leyenda.autoAdd=False

    ActualizaViajesOrigen(codZonaOrigen,origen)
    ActualizaViajesDestino(codZonaOrigen,destino)

    aplicaEstilos(destino,origen,df,SimbologiaOrigen,SimbologiaDestino)
    
    iluminaLayoutLocalizacion(codZonaOrigen,lyrSimbologiaLocalizacion,mxd)

    #setOrdenLeyenda(mxd)
    aplicaEstilosLeyenda(mxd,leyenda)
    
    mergeExtensionOrigenDestino(df,origen,destino)

    NombreRegion=ObtenNombreRegion(codZonaOrigen,zonificacion)

    actualizaTituloLayout(NombreRegion,mxd)

    mxd.activeView=df
    print(time.ctime())
    try:
        arcpy.mapping.ExportToPDF(mxd, "D:\Miguel\BOSLAN\INECO\DATOS\SALIDA" + "\\" + codZonaOrigen + "_" + NombreRegion + ".pdf" , data_frame="PAGE_LAYOUT")
    except:
        print("No se ha podido imprimir:" +codZonaOrigen + "_" + NombreRegion )
    print(time.ctime())
    ReseteaViajes(zonificacion)

    borraCapasEntrada()
    


#MAIN
arcpy.SetLogHistory(False)

csvViajes="D:\\Miguel\\BOSLAN\\INECO\DATOS\\OrigenDestinoCercaniasVal.csv"
#csvViajes="D:\\Miguel\\BOSLAN\\INECO\DATOS\\OrigenDestinoCarreteraVal.csv"

pathZonificacion="D:\\Miguel\\BOSLAN\INECO\\DATOS\\GIS FEVE\\Valencia\zonificacion\\"
lyrZonificacion=pathZonificacion+"zonificacion.lyr"
lyrSimbologiaOrigen=pathZonificacion+"SimbologiaOrigen_4.lyr"
lyrSimbologiaDestino=pathZonificacion+"SimbologiaDestino_4.lyr"
lyrSimbologiaLocalizacion=pathZonificacion+"zonificacionLocalizacion.lyr"

zonificacion = arcpy.mapping.Layer(lyrZonificacion)

codigos=codigosRegiones(csvViajes)
#tv=TipoViaje.values[TipoViaje.DestinoOrigen]
tv=TipoViaje.values[TipoViaje.OrigenDestino]

for codigo in codigos:

    MapaTematico(codigo,zonificacion,lyrSimbologiaOrigen,lyrSimbologiaDestino,lyrSimbologiaLocalizacion,tv)

