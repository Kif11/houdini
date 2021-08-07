import pdg
from pdg.processor import PyProcessor
from pdg import (envVar, strData, intData, floatData, resultData, hasStrData, hasIntData, hasFloatData, hasResultData, resultDataIndex, findResultData, findDirectResultData, floatDataArray, intDataArray, strDataArray, findData, findDirectData, input, workItem, kwargs)


class kif_generate_blender_script(PyProcessor):

    @classmethod
    def templateName(cls):
        return 'generate_blender_scripts_beaty_template'

    @classmethod
    def templateBody(cls):
        return """{
            "name": "generate_blender_scripts_beaty_template",
            "dataType": "GenericData",
            "parameters": [
                {
                    "name": "out_script",
                    "label": "Output Script",
                    "type": "String",
                    "value": "D:/Houdini/bombaybeach/tmp/scene_.py",
                    "tags": "['script_callback_language']"
                },
                {
                    "name": "render_out",
                    "label": "Render Output",
                    "type": "String",
                    "value": "D:/Houdini/bombaybeach/render/ruins/ruins_.png",
                    "tags": "['script_callback_language']"
                },
                {
                    "name": "env_map",
                    "label": "Environment Map",
                    "type": "String",
                    "value": "D:/Houdini/bombaybeach/img/oberer_kuhberg_1k.exr",
                    "tags": "['script_callback_language']"
                },
                {
                    "name": "render_samples",
                    "label": "Render Samples",
                    "type": "Integer",
                    "value": 128,
                    "tags": "['script_callback_language']"
                },
                {
                    "name": "resolutionx",
                    "label": "Resolution",
                    "type": "Float",
                    "value": 400.0,
                    "tags": "['script_callback_language']"
                },
                {
                    "name": "resolutiony",
                    "label": "Resolution",
                    "type": "Float",
                    "value": 400.0,
                    "tags": "['script_callback_language']"
                },
                {
                    "name": "wireframe",
                    "label": "Wireframe",
                    "type": "Integer",
                    "value": 0,
                    "tags": "['script_callback_language']"
                },
                {
                    "name": "uv_grid",
                    "label": "UV Grid",
                    "type": "Integer",
                    "value": 1,
                    "tags": "['script_callback_language']"
                }
            ]
        }"""

    def onAddInternalDependencies(self, dependency_holder, internal_items, is_static):
        return pdg.result.Success

    def onGenerate(self, item_holder, upstream_items, generation_type):
        for upstream_item in upstream_items:
            new_item = item_holder.addWorkItem(parent=upstream_item)
            
            in_geo = new_item.expectedInputResultData[0].path
            render_out = self['render_out'].evaluateString(new_item)
            out_script = self['out_script'].evaluateString(new_item)
            env_map = self['env_map'].evaluateString(new_item)
            render_samples = self['render_samples'].evaluateInt(new_item)
            res = self['resolution'].evaluate(new_item)
            
            render_wireframe = "False"
            wireframe = self['wireframe'].evaluateInt(new_item)
            
            if (wireframe > 0):
                render_wireframe = "True"
                
            uv_grid = "False"
            wireframe = self['uv_grid'].evaluateInt(new_item)
            
            if (uv_grid > 0):
                uv_grid = "True"
        
            with open(out_script, 'w') as f: 
                    f.write('''\
        import bpy
        import mathutils
        
        def local_translate(obj, direction):
            direction = direction.copy()
            direction.rotate(obj.matrix_world)
            obj.location += direction
        
        # Select objects by type
        for o in bpy.context.scene.objects:
            if o.type == "MESH" or o.type == "LIGHT":
                o.select_set(True)
            else:
                o.select_set(False)
        
        # Call the operator only once
        bpy.ops.object.delete()
        
        filepath = r"{in_geo}"
        bpy.ops.import_scene.obj(filepath=filepath)
        
        render_wireframe = {render_wireframe}
        uv_grid = {uv_grid}
        
        if (render_wireframe):
            selected = bpy.context.selected_objects[0]
        
            bpy.context.view_layer.objects.active = selected
        
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.mark_freestyle_edge(clear=False)
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.data.scenes["Scene"].render.use_freestyle = True
            bpy.data.scenes["Scene"].render.line_thickness = 0.2
        
            bpy.context.scene.view_layers["View Layer"].freestyle_settings.linesets["LineSet"].select_edge_mark = True
        
        if (uv_grid):
            # Set UV grid material
            mat = bpy.data.materials.new(name="New_Mat")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            tnode = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tnode.image = bpy.data.images.load("D:/Houdini/bombaybeach/img/uv_grid.png")
            mat.node_tree.links.new(bsdf.inputs["Base Color"], tnode.outputs["Color"])
        
            mnode = mat.node_tree.nodes.new("ShaderNodeMapping")
            mnode.inputs["Scale"].default_value = (5, 5, 5)
            mat.node_tree.links.new(mnode.outputs["Vector"], tnode.inputs["Vector"])
        
            cnode = mat.node_tree.nodes.new("ShaderNodeTexCoord")
            mat.node_tree.links.new(cnode.outputs["UV"], mnode.inputs["Vector"])
        
            selected = bpy.context.selected_objects[0]
            bpy.context.view_layer.objects.active = selected
        
            ob = bpy.context.view_layer.objects.active
        
            # Assign it to object
            if ob.data.materials:
                ob.data.materials[0] = mat
            else:
                ob.data.materials.append(mat)
            
        # Make ground
        plane = bpy.ops.mesh.primitive_plane_add()
        bpy.context.active_object.scale = (100, 100, 100)
        
        # Configure ligth
        # bpy.ops.object.light_add(type="SUN")
        # bpy.context.active_object.rotation_euler = (0.5, 0, 0.5)
        
        # Create environmental map
        world = bpy.context.scene.world
        world.use_nodes = True
        
        enode = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeTexEnvironment")
        bnode = bpy.context.scene.world.node_tree.nodes["Background"]
        enode.image = bpy.data.images.load("{env_map}")
        bpy.context.scene.world.node_tree.links.new(enode.outputs["Color"], bnode.inputs["Color"])
        
        env_map_ratation = 120
        mnode = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeMapping")
        mnode.inputs["Rotation"].default_value = (0,0,3.14159 * env_map_ratation / 180)
        bpy.context.scene.world.node_tree.links.new(mnode.outputs["Vector"], enode.inputs["Vector"])
        
        cnode = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeTexCoord")
        bpy.context.scene.world.node_tree.links.new(cnode.outputs["Generated"], mnode.inputs["Vector"])
        
        # Camera
        camera = bpy.data.objects["Camera"]
        local_translate(camera, mathutils.Vector((0, 0, 11)))
        
        # Configure render
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.render.resolution_x = {res_x}
        bpy.context.scene.render.resolution_y = {res_y}
        bpy.context.scene.render.filepath = "{render_out}"
        bpy.context.scene.cycles.samples = {render_samples}
        bpy.context.scene.cycles.device = "GPU"
        
        bpy.ops.render.render(write_still = True)
            '''.format(
                in_geo=in_geo,
                render_out=render_out,
                res_x=res[0],
                res_y=res[1],
                env_map=env_map,
                render_samples=render_samples,
                render_wireframe=render_wireframe,
                uv_grid=uv_grid
            ))
            
            new_item.addResultData(out_script, 'file/python', 0)
        return pdg.result.Success

    def onRegenerate(self, item_holder, existing_items, upstream_items, generation_type):
        return pdg.result.Success
    def onCookTask(self, work_item):
        # Called when an in process work item needs to cook. In process work items
        # are created by passing the  flag when constructing the item in
        # the Generate callback
        #
        # self              -   A reference to the current pdg.Node instance
        # work_item         -   The work item being cooked by this callback
        return pdg.result.Success


def registerTypes(type_registry):
    type_registry.registerNode(kif_generate_blender_script, pdg.nodeType.Processor, static_gen=True, label='Generate Blender Script', category='Custom')