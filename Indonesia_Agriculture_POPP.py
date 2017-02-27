# Notices:
# Copyright 2017 United States Government as represented by the Administrator of the 
# National Aeronautics and Space Administration. All Rights Reserved.
 
# Disclaimers
# No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF ANY KIND, 
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT 
# THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR FREEDOM FROM INFRINGEMENT, ANY 
# WARRANTY THAT THE SUBJECT SOFTWARE WILL BE ERROR FREE, OR ANY WARRANTY THAT DOCUMENTATION, 
# IF PROVIDED, WILL CONFORM TO THE SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, 
# CONSTITUTE AN ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS, 
# RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS RESULTING FROM 
# USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY DISCLAIMS ALL WARRANTIES AND 
# LIABILITIES REGARDING THIRD-PARTY SOFTWARE, IF PRESENT IN THE ORIGINAL SOFTWARE, AND 
# DISTRIBUTES IT "AS IS."
 
# Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST THE UNITED STATES 
# GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY PRIOR RECIPIENT.  IF 
# RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS IN ANY LIABILITIES, DEMANDS, DAMAGES, 
# EXPENSES OR LOSSES ARISING FROM SUCH USE, INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, 
# OR RESULTING FROM, RECIPIENT'S USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND 
# HOLD HARMLESS THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS 
# ANY PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.  RECIPIENT'S SOLE REMEDY FOR ANY SUCH 
# MATTER SHALL BE THE IMMEDIATE, UNILATERAL TERMINATION OF THIS AGREEMENT.


#Indonesia Agriculture
#March 2 2016
#Python code to:
    #Convert vectors to rasters
    #reclassify rasters
    #Reproject rasters  to WGS 1984
    #Convert rasters to same size based on cell size
    #Clip rasters to region of interest (polygon)
    #Convert those rasters into ASCII format
##Allow users to enter their own data


import arcpy
import os

try:
    arcpy.env.workspace = raw_input("What is the workspace path? ")
    arcpy.env.overwriteOutput = True
    #Set temporary output folder to put transformed rasters into -  this folder should include add rasters to be converted later
    outFolder = raw_input("What is the name of the output folder? ")

    #Make sure "Spatial Analyst" extension is on

    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        print "No Spatial Analyst extension, turn on Spatial Analyst"
    

    #Add vectors to be converted  to TRINARY (+) rasters
            #these should be coded 1 for presence, 0 for absence, -999 for background

    vectors = arcpy.ListFeatureClasses("*", "ALL")
    print vectors
    shp = raw_input("What is the name of the shapefile to clip raster and shapefile to? ")

    for vector in vectors:
        print vector
        #union raster to shape file
        combo = "un_" + vector[:-10]
        print combo
        arcpy.Union_analysis([shp, vector], combo) 
        
        #turn vectors into raster
        raster = "%s_raster" %(vector[:1])
        union = combo + ".shp"
        field = raw_input("What is the field you want to convert to raster? ")
        arcpy.FeatureToRaster_conversion(union, field, raster)
        print "A new raster called %s has been created" %raster

        arcpy.Delete_management(union)
        arcpy.Delete_management(combo)
        mask_raster = arcpy.sa.ExtractByMask(raster, shp)
        outName = os.path.join(outFolder, "mask_" + vector[:3])
        mask_raster.save(outName)
        print mask_raster

        print "Now reclassify the rasters"
        print " "

        #reclassify rasters
        reclassField = "VALUE"
        remapVal = input("What are the remap values? ")
        #remapVal = ([[1,0],[2,1],["NODATA", -999]])
        #these should be minimum 0,1,-999 (may choose 1-xx for more nuanced features)

        remap = arcpy.sa.RemapValue(remapVal)
        outReclassify = arcpy.sa.Reclassify(mask_raster, reclassField, remap, "DATA")
        outName = os.path.join(outFolder, "rc_" + vector[:6])

        outReclassify.save(outName + ".tif")
        arcpy.Delete_management(raster)
        arcpy.Delete_management(mask_raster)

        print "A classified file called %s has been created" %("rc_" + vector[:5])
        print " "
        print " "

    ###Now go through old resample code to make these vectors like others
    #make sure shapefile has same projection

    refcode = input("What is the spatial reference code? ")
    spatref = arcpy.SpatialReference(refcode)
    arcpy.DefineProjection_management(shp, spatref)

    #Add rasters to be converted
    arcpy.env.workspace = outFolder
    outFolder = raw_input("What is the name of the final output folder? ")
    rasters = arcpy.ListRasters("*","ALL")

    print rasters

    #Add in raster with smallest cell size
    input_raster = raw_input("What is the full path of the raster to clip all raster to? ")

   
    for raster in rasters:  
        print raster[:-4]

        #make all rasters the same projection (WGS 1984 UTM 50 N)
        proj_raster = raster[:6] + "_WGS"    
        arcpy.ProjectRaster_management(raster, proj_raster, spatref)
        print "%s has been reprojected" %raster

        #Convert rasters to the raster with the smallest cell size
        desc = arcpy.Describe(input_raster)
        cellsize = desc.meanCellWidth
        resize_raster = proj_raster[1:-5] + "_resize"
        arcpy.Resample_management(proj_raster, resize_raster, cellsize)

        arcpy.Delete_management(proj_raster)

        print "%s has been resized" %raster

        #Clip rasters to region of interest (polygon)
        mask_raster = arcpy.sa.ExtractByMask(resize_raster, shp)

        arcpy.Delete_management(resize_raster)

        print "mask complete"
        outMask = os.path.join(outFolder, raster)
        mask_raster.save(outMask)
        print "mask saved"
        
        #Convert raster to ASCII file
        outAsc= outFolder + "\%s.asc" %(raster[:6])
        arcpy.RasterToASCII_conversion(mask_raster, outAsc)

        arcpy.Delete_management(mask_raster)
        print "A new ASCII file called %s has been created" %(outAsc)
    print "Ready for MAXENT!"


except Exception as e:
    print "Error: " + str(e) #prints python-realted errors
    print arcpy.GetMessages() #prints arcpy-related errors
    arcpy.AddError(e) #adds errors to ArcGIS custom tool
