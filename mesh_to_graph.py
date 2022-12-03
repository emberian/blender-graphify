# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass

import itertools

import bpy
import bmesh
from bmesh.types import BMesh
import mathutils
from bpy_extras import object_utils
from bpy.props import IntProperty

bl_info = {
    "name": "Graphify Cuboids",
    "author": "ember arlynx",
    "version": (1, 0),
    "blender": (3, 3, 0),
    "location": "View3D > Add > Mesh > Cuboid ; View3D > Select > Graphify",
    "description": "Adds a new Cuboid Object",
    "category": "Add Mesh",
}


@dataclass
class Graph:
    verts: set[int]
    edges: set[(int, int)]
    
def netgraph_for_mesh(m: bpy.types.Mesh) -> Graph:
    bm: BMesh = bmesh.new()
    bm.from_mesh(m)
    return Graph(set(f.index for f in bm.faces), 
                 set((f1.index, f2.index) for f1 in bm.faces
                    for e in f1.edges 
                    for f2 in e.link_faces
                    if f1.index!=f2.index))

def new_cuboid(a:int,b:int,c:int) -> BMesh:
    cb = bmesh.new()
    verts = bmesh.ops.create_cube(cb)
    sizes = (a,b,c)
    for axis in range(3):
        this_axis = [e for e in cb.edges if e.verts[0].co[axis] != e.verts[1].co[axis]]
        bmesh.ops.subdivide_edges(cb, edges=this_axis, cuts=sizes[axis]-1)
    bmesh.ops.scale(cb, vec=sizes, verts=cb.verts)
    return cb
    
def display(m):
    meshdata = bpy.data.meshes.new("mesh")
    m.to_mesh(meshdata)
    nobj = bpy.data.objects.new("Graphify Debug Display", meshdata)
    bpy.context.collection.objects.link(nobj)
    
class Graphify(bpy.types.Operator):
    bl_idname = "util.graphify"
    bl_label = "Compute face graph"
    
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            self.report({'INFO'}, f"{obj.name}: {netgraph_for_mesh(obj.data)}")
        bpy.ops.info.reports_display_update()
        return {'FINISHED'}

def graph_menu_button(self, context):
    self.layout.operator(Graphify.bl_idname, text="Graphify")

class AddCuboid(bpy.types.Operator, object_utils.AddObjectHelper):
    """Construct a torus mesh"""
    bl_idname = "mesh.primitive_cuboid_add"
    bl_label = "Add Cuboid"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    a: IntProperty(
        name="x segments",
        description="Number of segments for the x axis of the cuboid",
        min=1, max=256,
        default=10,
    )
    b: IntProperty(
        name="y segments",
        description="Number of segments for the y axis of the cuboid",
        min=1, max=256,
        default=3,
    )
    c: IntProperty(
        name="z segments",
        description="Number of segments for the z axis of the cuboid",
        min=1, max=256,
        default=1,
    )

    def draw(self, _context):
        layout = self.layout


        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.separator()
        
        layout.prop(self, "a")
        layout.prop(self, "b")
        layout.prop(self, "c")


    def invoke(self, context, _event):
        object_utils.object_add_grid_scale_apply_operator(self, context)
        return self.execute(context)

    def execute(self, context):
        cb = new_cuboid(self.a, self.b, self.c)
        
        mesh = bpy.data.meshes.new(f"Cuboid ({self.a}, {self.b}, {self.c})")
        cb.to_mesh(mesh)
        mesh.update()

        object_utils.object_data_add(context, mesh, operator=self)

        return {'FINISHED'}

def cuboid_button(self,context):
    self.layout.operator(AddCuboid.bl_idname, text="Cuboid")

classes = (
    AddCuboid,
    Graphify,
)

buttons = (
    (bpy.types.VIEW3D_MT_mesh_add, cuboid_button),
    (bpy.types.VIEW3D_MT_select_object, graph_menu_button),
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    for (menu, bt) in buttons:
        menu.append(bt)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    for (menu, bt) in buttons:
        menu.remove(bt)

if __name__ == "__main__":
    register()
