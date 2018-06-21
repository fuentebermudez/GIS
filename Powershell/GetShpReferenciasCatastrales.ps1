#************************************************************************************
#**          Extractor de parcelas catastrales en formato GML
#**  
#**  
#**  Author:	Miguel Angel de la Fuente
#**  Date:		30/05/2018
#**  Version:   1.1
#**  Target:    WFS catastral
#************************************************************************************
#**Input:
#**      
#**      txt:ReferenciasCatastrales
#**Output:
#**      GML: Rchivo GML con las geometr�as de las referencias catastrales refereridas
#**           en el txt de entrada.
#************************************************************************************


param (
    [Parameter(Mandatory=$True,Position=1)]
    [string]$pathFileReferencias
    
)

function getGMLParcelaCatastro([String]$ReferenciaCatastral){
    
    $uri=("http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx?service=wfs&version=2&request=storedqueries&STOREDQUERIE_ID=GetParcel&REFCAT="+ $ReferenciaCatastral  +"&srsname=EPSG::25830")
    try{
        [xml]$a=Invoke-WebRequest -Uri $uri
    }
    catch{
        
        Start-Sleep -Milliseconds 60000
        while($a -eq ""){
            Start-Sleep -Milliseconds 60000
            [xml]$a=Invoke-WebRequest -Uri $uri
        }
    }
    return $a
}

function getMunicipioRefCatastral($ReferenciaCatastral){
    [xml]$parcela=getValoresParcela($ReferenciaCatastral)
    $cp=$parcela.consulta_dnp.bico.bi.dt.loine.cp
    $cm=$parcela.consulta_dnp.bico.bi.dt.loine.cm

    
    $municipioNombre=$parcela.consulta_dnp.bico.bi.dt.nm
    $municipioProvincia=$parcela.consulta_dnp.bico.bi.dt.np
    while($cm.length -lt 3){
        $cm=("0"+$cm)
    }
    $codigoMunicipio=($cp+$cm)

    $salidaMunicipio=$codigoMunicipio + ";" + $municipioNombre +";" + $municipioProvincia
    return $salidaMunicipio
}

function getValoresParcela([String]$ReferenciaCatastral){
    $uri=("http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC?Provincia=&Municipio=&RC=" + $ReferenciaCatastral)
     
    try{
        [xml]$a=Invoke-WebRequest -Uri $uri
    }
    catch{
        
        Start-Sleep -Milliseconds 60000
        while($a -eq ""){
            Start-Sleep -Milliseconds 60000
            [xml]$a=Invoke-WebRequest -Uri $uri
        }
    }
    return $a

}


function getGMLParcelasCatastro([String] $pathFileReferencias, $pathArchivoSalida) {
    
    $referencias=get-content $pathFileReferencias
    $numReferencias=$referencias.count

    $DirectorioSalida=[System.IO.Path]::GetDirectoryName("$pathFileReferencias")

    $cabecera='<?xml version="1.0" encoding="ISO-8859-1"?>
    <!--Parcela Catastral de la D.G. del Catastro.-->
    <!--La precisión es la que corresponde nominalmente a la escala de captura de la cartografía-->
    <FeatureCollection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0" xmlns:gmd="http://www.isotc211.org/2005/gmd" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://inspire.ec.europa.eu/schemas/cp/4.0 http://inspire.ec.europa.eu/schemas/cp/4.0/CadastralParcels.xsd" xmlns="http://www.opengis.net/wfs/2.0" timeStamp="2018-05-29T14:55:52" numberMatched="1" numberReturned="1">'
    $pie="</FeatureCollection>"

    Add-Content -Path $pathArchivoSalida -value $cabecera
    $n=1
    foreach ($referencia in $referencias){
        Write-Progress -Activity "Obteniedo parcelas catastrales"  -Status 'Progress->' -PercentComplete (($n/$numReferencias)*100) -CurrentOperation Recorre_referencias;
        $referencia
    
    
        $a=getGMLParcelaCatastro($referencia,$fallos)
        $secEspera=get-random -Maximum 500 -Minimum 0
        Start-Sleep -Milliseconds $secEspera

        $feature=$a.FeatureCollection.InnerXml
        [xml]$featureXML=$feature

        $municipio=getMunicipioRefCatastral $referencia

        Add-Content -Path $pathArchivoSalida -value $feature
        add-content -path ($DirectorioSalida + "\logMerge.csv") -value ($referencia + ";" +$featureXML.member.CadastralParcel.nationalCadastralReference + ";" + $municipio)
        
        $n=$n+1

    }
    Add-Content -Path $pathArchivoSalida -value $pie

}

if([System.IO.File]::Exists($pathFileReferencias) -eq $True){

    
    $DirectorioSalida=[System.IO.Path]::GetDirectoryName("$pathFileReferencias")
    $PathArchivoMerge=$DirectorioSalida + "\Merge.gml"
    
    if([System.IO.File]::Exists($PathArchivoMerge)) {
        
        Remove-Item $PathArchivoMerge -ErrorAction Stop -Confirm
        write-host -BackgroundColor Green "El archivo " + $pathFileReferencias + " ha sido borrado." 
        
    }
    
    getGMLParcelasCatastro $pathFileReferencias $PathArchivoMerge
}
else{
    Write-Host -BackgroundColor Red "No se ha encontrado el archivo"
}




