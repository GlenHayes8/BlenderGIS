# -*- coding:Latin-1 -*-
import os
import bpy
import bmesh
import mathutils
from .shapefile import Writer as shpWriter
from .shapefile import POINTZ, POLYLINEZ, POLYGONZ

from bpy_extras.io_utils import ExportHelper #helper class defines filename and invoke() function which calls the file selector
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator


class EXPORT_SHP(Operator, ExportHelper):
	"""Export from ESRI shapefile file format (.shp)"""
	bl_idname = "export.shapefile"
	bl_description = 'export to ESRI shapefile file format (.shp)'
	bl_label = "Export SHP"
	bl_options = {"UNDO"}


	# ExportHelper class properties
	filename_ext = ".shp"
	filter_glob = StringProperty(
			default="*.shp",
			options={'HIDDEN'},
			)

	exportType = EnumProperty(
			name="Feature type",
			description="Select feature type",
			items=[ ('POINTZ', 'Point', ""),
			('POLYLINEZ', 'Line', ""),
			('POLYGONZ', 'Polygon', "")]
			)


	def draw(self, context):
		#Function used by blender to draw the panel.
		layout = self.layout
		layout.prop(self, 'exportType')

	def execute(self, context):
		filePath = self.filepath
		scn = bpy.context.scene
		#Get selected obj
		try:
			bpy.ops.object.mode_set(mode='OBJECT')
		except:
			pass
		objs = bpy.context.selected_objects
		if len(objs) == 0 or len(objs)>1:
			self.report({'INFO'}, "Selection is empty or too much object selected")
			print("Selection is empty or too much object selected")
			return {'FINISHED'}
		obj = objs[0]
		if obj.type != 'MESH':
			self.report({'INFO'}, "Selection isn't a mesh")
			print("Selection isn't a mesh")
			return {'FINISHED'}

		if "Georef X" in scn and "Georef Y" in scn:
			dx, dy = scn["Georef X"], scn["Georef Y"]
		else:
			dx, dy = (0, 0)

		bpy.ops.object.transform_apply(rotation=True, scale=True)
		mesh = obj.data
		loc = obj.location
		bm = bmesh.new()
		bm.from_mesh(mesh)

		if self.exportType == 'POINTZ':
			outShp = shpWriter(POINTZ)
			outShp.field('id','N','10')
			if len(bm.verts) == 0:
				self.report({'ERROR'}, "No vertice to export")
				print("No vertice to export")
				return {'FINISHED'}
			for id, vert in enumerate(bm.verts):
				#Extract coords & adjust values against object location & shift against georef deltas
				outShp.point(vert.co.x+loc.x+dx, vert.co.y+loc.y+dy, vert.co.z+loc.z)
				outShp.record(id)
			outShp.save(filePath)

		if self.exportType == 'POLYLINEZ':
			outShp = shpWriter(POLYLINEZ)
			outShp.field('id','N','10')
			if len(bm.edges) == 0:
				self.report({'ERROR'}, "No edge to export")
				print("No edge to export")
				return {'FINISHED'}
			for id, edge in enumerate(bm.edges):
				#Extract coords & adjust values against object location & shift against georef deltas
				line=[(vert.co.x+loc.x+dx, vert.co.y+loc.y+dy, vert.co.z+loc.z) for vert in edge.verts]
				outShp.line([line], shapeType=13)#cause shp feature can be multipart we need to enclose poly in a list
				outShp.record(id)
			outShp.save(filePath)
		
		if self.exportType == 'POLYGONZ':
			outShp = shpWriter(POLYGONZ)
			outShp.field('id','N','10')
			if len(bm.faces) == 0:
				self.report({'ERROR'}, "No face to export")
				print("No face to export")
				return {'FINISHED'}
			for id, face in enumerate(bm.faces):
				#Extract coords & adjust values against object location & shift against georef deltas
				poly=[(vert.co.x+loc.x+dx, vert.co.y+loc.y+dy, vert.co.z+loc.z) for vert in face.verts]
				poly.append(poly[0])#close poly
				poly.reverse()#In Blender face is up if points are in anticlockwise order, in shp face's up with clockwise order
				outShp.poly([poly], shapeType=15)#cause shp feature can be multipart we need to enclose poly in a list
				outShp.record(id)
			outShp.save(filePath)

		self.report({'INFO'}, "Export complete")
		print("Export complete")
		return {'FINISHED'}

