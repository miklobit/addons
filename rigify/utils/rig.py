#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy
import importlib
import importlib.util
import os

RIG_DIR = "rigs"  # Name of the directory where rig types are kept
METARIG_DIR = "metarigs"  # Name of the directory where metarigs are kept
TEMPLATE_DIR = "ui_templates"  # Name of the directory where ui templates are kept


outdated_types = {"pitchipoy.limbs.super_limb": "limbs.super_limb",
                  "pitchipoy.limbs.super_arm": "limbs.super_limb",
                  "pitchipoy.limbs.super_leg": "limbs.super_limb",
                  "pitchipoy.limbs.super_front_paw": "limbs.super_limb",
                  "pitchipoy.limbs.super_rear_paw": "limbs.super_limb",
                  "pitchipoy.limbs.super_finger": "limbs.super_finger",
                  "pitchipoy.super_torso_turbo": "spines.super_spine",
                  "pitchipoy.simple_tentacle": "limbs.simple_tentacle",
                  "pitchipoy.super_face": "faces.super_face",
                  "pitchipoy.super_palm": "limbs.super_palm",
                  "pitchipoy.super_copy": "basic.super_copy",
                  "pitchipoy.tentacle": "",
                  "palm": "limbs.super_palm",
                  "basic.copy": "basic.super_copy",
                  "biped.arm": "",
                  "biped.leg": "",
                  "finger": "",
                  "neck_short": "",
                  "misc.delta": "",
                  "spine": ""
                  }

def get_rigify_type(pose_bone):
    return pose_bone.rigify_type.replace(" ", "")

def is_rig_base_bone(obj, name):
    return bool(get_rigify_type(obj.pose.bones[name]))

def upgradeMetarigTypes(metarig, revert=False):
    """Replaces rigify_type properties from old versions with their current names

    :param revert: revert types to previous version (if old type available)
    """

    if revert:
        vals = list(outdated_types.values())
        rig_defs = {v: k for k, v in outdated_types.items() if vals.count(v) == 1}
    else:
        rig_defs = outdated_types

    for bone in metarig.pose.bones:
        rig_type = bone.rigify_type
        if rig_type in rig_defs:
            bone.rigify_type = rig_defs[rig_type]
            if 'leg' in rig_type:
                bone.rigfy_parameters.limb_type = 'leg'
            if 'arm' in rig_type:
                bone.rigfy_parameters.limb_type = 'arm'
            if 'paw' in rig_type:
                bone.rigfy_parameters.limb_type = 'paw'
            if rig_type == "basic.copy":
                bone.rigify_parameters.make_widget = False


#=============================================
# Misc
#=============================================

def get_resource(resource_name):
    """ Fetches a rig module by name, and returns it.
    """

    module = importlib.import_module(resource_name)
    importlib.reload(module)
    return module


def attach_persistent_script(obj, script):
    """Make sure the ui script always follows the rig around"""
    skip = False
    driver = None

    if not obj.animation_data:
        obj.animation_data_create()

    for fcurve in obj.animation_data.drivers:
        if fcurve.data_path == 'pass_index':
            driver = fcurve.driver
            for variable in driver.variables:
                if variable.name == script.name:
                    skip = True
                    break
            break

    if not skip:
        if not driver:
            fcurve = obj.driver_add("pass_index")
            driver = fcurve.driver

        variable = driver.variables.new()
        variable.name = script.name
        variable.targets[0].id_type = 'TEXT'
        variable.targets[0].id = script


def connected_children_names(obj, bone_name):
    """ Returns a list of bone names (in order) of the bones that form a single
        connected chain starting with the given bone as a parent.
        If there is a connected branch, the list stops there.
    """
    bone = obj.data.bones[bone_name]
    names = []

    while True:
        connects = 0
        con_name = ""

        for child in bone.children:
            if child.use_connect:
                connects += 1
                con_name = child.name

        if connects == 1:
            names += [con_name]
            bone = obj.data.bones[con_name]
        else:
            break

    return names


def has_connected_children(bone):
    """ Returns true/false whether a bone has connected children or not.
    """
    t = False
    for b in bone.children:
        t = t or b.use_connect
    return t


def _list_bone_names_depth_first_sorted_rec(result_list, bone):
    result_list.append(bone.name)

    for child in sorted(list(bone.children), key=lambda b: b.name):
        _list_bone_names_depth_first_sorted_rec(result_list, child)

def list_bone_names_depth_first_sorted(obj):
    """Returns a list of bone names in depth first name sorted order."""
    result_list = []

    for bone in sorted(list(obj.data.bones), key=lambda b: b.name):
        if bone.parent is None:
            _list_bone_names_depth_first_sorted_rec(result_list, bone)

    return result_list


def write_metarig(obj, layers=False, func_name="create", groups=False):
    """
    Write a metarig as a python script, this rig is to have all info needed for
    generating the real rig with rigify.
    """
    code = []

    code.append("import bpy\n\n")
    code.append("from mathutils import Color\n\n")

    code.append("def %s(obj):" % func_name)
    code.append("    # generated by rigify.utils.write_metarig")
    bpy.ops.object.mode_set(mode='EDIT')
    code.append("    bpy.ops.object.mode_set(mode='EDIT')")
    code.append("    arm = obj.data")

    arm = obj.data

    # Rigify bone group colors info
    if groups and len(arm.rigify_colors) > 0:
        code.append("\n    for i in range(" + str(len(arm.rigify_colors)) + "):")
        code.append("        arm.rigify_colors.add()\n")

        for i in range(len(arm.rigify_colors)):
            name = arm.rigify_colors[i].name
            active = arm.rigify_colors[i].active
            normal = arm.rigify_colors[i].normal
            select = arm.rigify_colors[i].select
            standard_colors_lock = arm.rigify_colors[i].standard_colors_lock
            code.append('    arm.rigify_colors[' + str(i) + '].name = "' + name + '"')
            code.append('    arm.rigify_colors[' + str(i) + '].active = Color(' + str(active[:]) + ')')
            code.append('    arm.rigify_colors[' + str(i) + '].normal = Color(' + str(normal[:]) + ')')
            code.append('    arm.rigify_colors[' + str(i) + '].select = Color(' + str(select[:]) + ')')
            code.append('    arm.rigify_colors[' + str(i) + '].standard_colors_lock = ' + str(standard_colors_lock))

    # Rigify layer layout info
    if layers and len(arm.rigify_layers) > 0:
        code.append("\n    for i in range(" + str(len(arm.rigify_layers)) + "):")
        code.append("        arm.rigify_layers.add()\n")

        for i in range(len(arm.rigify_layers)):
            name = arm.rigify_layers[i].name
            row = arm.rigify_layers[i].row
            selset = arm.rigify_layers[i].selset
            group = arm.rigify_layers[i].group
            code.append('    arm.rigify_layers[' + str(i) + '].name = "' + name + '"')
            code.append('    arm.rigify_layers[' + str(i) + '].row = ' + str(row))
            code.append('    arm.rigify_layers[' + str(i) + '].selset = ' + str(selset))
            code.append('    arm.rigify_layers[' + str(i) + '].group = ' + str(group))

    # write parents first
    bones = [(len(bone.parent_recursive), bone.name) for bone in arm.edit_bones]
    bones.sort(key=lambda item: item[0])
    bones = [item[1] for item in bones]

    code.append("\n    bones = {}\n")

    for bone_name in bones:
        bone = arm.edit_bones[bone_name]
        code.append("    bone = arm.edit_bones.new(%r)" % bone.name)
        code.append("    bone.head[:] = %.4f, %.4f, %.4f" % bone.head.to_tuple(4))
        code.append("    bone.tail[:] = %.4f, %.4f, %.4f" % bone.tail.to_tuple(4))
        code.append("    bone.roll = %.4f" % bone.roll)
        code.append("    bone.use_connect = %s" % str(bone.use_connect))
        if bone.parent:
            code.append("    bone.parent = arm.edit_bones[bones[%r]]" % bone.parent.name)
        code.append("    bones[%r] = bone.name" % bone.name)

    bpy.ops.object.mode_set(mode='OBJECT')
    code.append("")
    code.append("    bpy.ops.object.mode_set(mode='OBJECT')")

    # Rig type and other pose properties
    for bone_name in bones:
        pbone = obj.pose.bones[bone_name]

        code.append("    pbone = obj.pose.bones[bones[%r]]" % bone_name)
        code.append("    pbone.rigify_type = %r" % pbone.rigify_type)
        code.append("    pbone.lock_location = %s" % str(tuple(pbone.lock_location)))
        code.append("    pbone.lock_rotation = %s" % str(tuple(pbone.lock_rotation)))
        code.append("    pbone.lock_rotation_w = %s" % str(pbone.lock_rotation_w))
        code.append("    pbone.lock_scale = %s" % str(tuple(pbone.lock_scale)))
        code.append("    pbone.rotation_mode = %r" % pbone.rotation_mode)
        if layers:
            code.append("    pbone.bone.layers = %s" % str(list(pbone.bone.layers)))
        # Rig type parameters
        for param_name in pbone.rigify_parameters.keys():
            param = getattr(pbone.rigify_parameters, param_name, '')
            if str(type(param)) == "<class 'bpy_prop_array'>":
                param = list(param)
            if type(param) == str:
                param = '"' + param + '"'
            code.append("    try:")
            code.append("        pbone.rigify_parameters.%s = %s" % (param_name, str(param)))
            code.append("    except AttributeError:")
            code.append("        pass")

    code.append("\n    bpy.ops.object.mode_set(mode='EDIT')")
    code.append("    for bone in arm.edit_bones:")
    code.append("        bone.select = False")
    code.append("        bone.select_head = False")
    code.append("        bone.select_tail = False")

    code.append("    for b in bones:")
    code.append("        bone = arm.edit_bones[bones[b]]")
    code.append("        bone.select = True")
    code.append("        bone.select_head = True")
    code.append("        bone.select_tail = True")
    code.append("        arm.edit_bones.active = bone")

    # Set appropriate layers visible
    if layers:
        # Find what layers have bones on them
        active_layers = []
        for bone_name in bones:
            bone = obj.data.bones[bone_name]
            for i in range(len(bone.layers)):
                if bone.layers[i]:
                    if i not in active_layers:
                        active_layers.append(i)
        active_layers.sort()

        code.append("\n    arm.layers = [(x in " + str(active_layers) + ") for x in range(" + str(len(arm.layers)) + ")]")

    code.append("\n    return bones")

    code.append('\nif __name__ == "__main__":')
    code.append("    " + func_name + "(bpy.context.active_object)\n")

    return "\n".join(code)
