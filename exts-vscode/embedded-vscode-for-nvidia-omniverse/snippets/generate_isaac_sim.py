import json
import inspect
from types import FunctionType

from pxr import Sdf

def args_annotations(method):
    signature = inspect.signature(method)

    args = []
    annotations = []
    return_val = signature.return_annotation
    return_val = class_fullname(return_val) if return_val != type(inspect.Signature.empty) else "None"
    return_val = "" if return_val in ["inspect._empty", "None"] else return_val

    for parameter in signature.parameters.values():
        if parameter.name in ["self", "args", "kwargs"]:
            continue
        # arg
        if type(parameter.default) == type(inspect.Parameter.empty):
            args.append("{}={}".format(parameter.name, parameter.name))
        else:
            default_value = parameter.default
            if type(parameter.default) is str:
                default_value = '"{}"'.format(parameter.default)
            elif type(parameter.default) is Sdf.Path:
                if parameter.default == Sdf.Path.emptyPath:
                    default_value = "Sdf.Path.emptyPath"
                else:
                    default_value = 'Sdf.Path("{}")'.format(parameter.default)
            elif inspect.isclass(parameter.default):
                default_value = class_fullname(parameter.default)
            args.append("{}={}".format(parameter.name, default_value))
        # annotation
        if parameter.annotation == inspect.Parameter.empty:
            annotations.append("")
        else:
            annotations.append(class_fullname(parameter.annotation))

    return args, annotations, return_val

def class_fullname(c):
    try:
        module = c.__module__
        if module == 'builtins':
            return c.__name__
        return module + '.' + c.__name__
    except:
        return str(c)

def get_class(klass, object_name):

    class_name = klass.__qualname__
    args, annotations, _ = args_annotations(klass.__init__)

    # build snippet
    arguments_as_string = ')'
    if args:
        arguments_as_string = ''
    
    spaces = len(object_name) + 3 + len(class_name) + 1
    for i, arg, annotation in zip(range(len(args)), args, annotations):
        k = 0 if not i else 1
        is_last = i >= len(args) - 1
        if annotation:
            arguments_as_string += " " * k * spaces + "{}{}".format(arg, ")  # {}".format(annotation) if is_last else ",  # {}\n".format(annotation))
        else:
            arguments_as_string += " " * k * spaces + "{}{}".format(arg, ")" if is_last else ",\n")

    try:
        description = klass.__doc__.replace("\n    ", "\n")
        if description.startswith("\n"):
            description = description[1:]
        if description.endswith("\n"):
            description = description[:-1]
        while "  " in description:
            description = description.replace("  ", " ")
    except Exception as e:
        description = None
    if not description:
        description = ""
    snippet = '{} = {}({}'.format(object_name, class_name, arguments_as_string) + "\n"

    return {
        "title": class_name,
        "description": description,
        "snippet": snippet
    }

def get_methods(klass, object_name):
    method_names = sorted([x for x, y in klass.__dict__.items() if type(y) == FunctionType and not x.startswith("__")])

    snippets = []

    for method_name in method_names:
        if method_name.startswith("_") or method_name.startswith("__"):
            continue

        args, annotations, return_val = args_annotations(klass.__dict__[method_name])

        # build snippet
        arguments_as_string = ')'
        if args:
            arguments_as_string = ''
        
        return_var_name = ""
        if method_name.startswith("get_"):
            return_var_name = method_name[4:] + " = "
        spaces = len(return_var_name) + len(object_name) + 1 + len(method_name) + 1
        
        for i, arg, annotation in zip(range(len(args)), args, annotations):
            k = 0 if not i else 1
            is_last = i >= len(args) - 1
            if annotation:
                arguments_as_string += " " * k * spaces + "{}{}".format(arg, ")  # {}".format(annotation) if is_last else ",  # {}\n".format(annotation))
            else:
                arguments_as_string += " " * k * spaces + "{}{}".format(arg, ")" if is_last else ",\n")

        try:
            description = klass.__dict__[method_name].__doc__.replace("\n    ", "\n")
            while "    " in description:
                description = description.replace("    ", "  ")
            if description.startswith("\n"):
                description = description[1:]
            if description.endswith("\n"):
                description = description[:-1]
            if description.endswith("\n "):
                description = description[:-2]
        except Exception as e:
            description = None
        if not description:
            description = ""
        
        if return_var_name:
            snippet = '{}{}.{}({}'.format(return_var_name, object_name, method_name, arguments_as_string) + "\n"
        else:
            snippet = '{}.{}({}'.format(object_name, method_name, arguments_as_string) + "\n"

        snippets.append({
                "title": method_name,
                "description": description,
                "snippet": snippet
            })
        
    return snippets

def get_functions(module, module_name, exclude_functions=[]):
    functions = inspect.getmembers(module, inspect.isfunction)

    snippets = []

    for function in functions:
        function_name = function[0]
        if function_name.startswith("_") or function_name.startswith("__"):
            continue
        if function_name in exclude_functions:
            continue

        args, annotations, return_val = args_annotations(function[1])

         # build snippet
        arguments_as_string = ')'
        if args:
            arguments_as_string = ''
        
        return_var_name = ""
        if return_val:
            return_var_name = "value = "
        spaces = len(return_var_name) + len(module_name) + 1 + len(function_name) + 1
        
        for i, arg, annotation in zip(range(len(args)), args, annotations):
            k = 0 if not i else 1
            is_last = i >= len(args) - 1
            if annotation:
                arguments_as_string += " " * k * spaces + "{}{}".format(arg, ")  # {}".format(annotation) if is_last else ",  # {}\n".format(annotation))
            else:
                arguments_as_string += " " * k * spaces + "{}{}".format(arg, ")" if is_last else ",\n")

        try:
            description = function[1].__doc__.replace("\n    ", "\n")
            while "    " in description:
                description = description.replace("    ", "  ")
            if description.startswith("\n"):
                description = description[1:]
            if description.endswith("\n"):
                description = description[:-1]
            if description.endswith("\n "):
                description = description[:-2]
        except Exception as e:
            description = None
        if not description:
            description = ""
        
        if return_var_name:
            snippet = '{}{}.{}({}'.format(return_var_name, module_name, function_name, arguments_as_string) + "\n"
        else:
            snippet = '{}.{}({}'.format(module_name, function_name, arguments_as_string) + "\n"

        snippets.append({
                "title": function_name,
                "description": description,
                "snippet": snippet
            })
        
    return snippets


from omni.isaac.core.articulations import Articulation, ArticulationGripper, ArticulationSubset, ArticulationView
from omni.isaac.core.controllers import ArticulationController, BaseController, BaseGripperController
from omni.isaac.core.loggers import DataLogger
from omni.isaac.core.materials import OmniGlass, OmniPBR, ParticleMaterial, ParticleMaterialView, PhysicsMaterial, PreviewSurface, VisualMaterial
from omni.isaac.core.objects import DynamicCapsule, DynamicCone, DynamicCuboid, DynamicCylinder, DynamicSphere
from omni.isaac.core.objects import FixedCapsule, FixedCone, FixedCuboid, FixedCylinder, FixedSphere, GroundPlane
from omni.isaac.core.objects import VisualCapsule, VisualCone, VisualCuboid, VisualCylinder, VisualSphere
from omni.isaac.core.physics_context import PhysicsContext
from omni.isaac.core.prims import BaseSensor, ClothPrim, ClothPrimView, GeometryPrim, GeometryPrimView, ParticleSystem, ParticleSystemView, RigidContactView, RigidPrim, RigidPrimView, XFormPrim, XFormPrimView
from omni.isaac.core.robots import Robot, RobotView
from omni.isaac.core.scenes import Scene, SceneRegistry
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.core.world import World
from omni.isaac.core.tasks import BaseTask, FollowTarget, PickPlace, Stacking

from omni.isaac.core.prims._impl.single_prim_wrapper import _SinglePrimWrapper

import omni.isaac.core.utils.bounds as utils_bounds
import omni.isaac.core.utils.carb as utils_carb
import omni.isaac.core.utils.collisions as utils_collisions
import omni.isaac.core.utils.constants as utils_constants
import omni.isaac.core.utils.distance_metrics as utils_distance_metrics
import omni.isaac.core.utils.extensions as utils_extensions
import omni.isaac.core.utils.math as utils_math
import omni.isaac.core.utils.mesh as utils_mesh
import omni.isaac.core.utils.nucleus as utils_nucleus
import omni.isaac.core.utils.numpy as utils_numpy
import omni.isaac.core.utils.physics as utils_physics
import omni.isaac.core.utils.prims as utils_prims
import omni.isaac.core.utils.random as utils_random
import omni.isaac.core.utils.render_product as utils_render_product
import omni.isaac.core.utils.rotations as utils_rotations
import omni.isaac.core.utils.semantics as utils_semantics
import omni.isaac.core.utils.stage as utils_stage
import omni.isaac.core.utils.string as utils_string
import omni.isaac.core.utils.transformations as utils_transformations
import omni.isaac.core.utils.torch as utils_torch
import omni.isaac.core.utils.types as utils_types
import omni.isaac.core.utils.viewports as utils_viewports
import omni.isaac.core.utils.xforms as utils_xforms

# from omni.isaac.dynamic_control import _dynamic_control
# _dynamic_control_interface = _dynamic_control.acquire_dynamic_control_interface()

from omni.isaac.ui import ui_utils

from omni.isaac.kit import SimulationApp



# core 
snippets = []

# articulations
subsnippets = []

s0 = get_class(Articulation, "articulation")
s1 = get_methods(Articulation, "articulation")
s2 = get_methods(_SinglePrimWrapper, "articulation")
subsnippets.append({"title": "Articulation", "snippets": [s0] + s1 + s2})

s0 = get_class(ArticulationGripper, "articulation_gripper")
s1 = get_methods(ArticulationGripper, "articulation_gripper")
subsnippets.append({"title": "ArticulationGripper", "snippets": [s0] + s1})

s0 = get_class(ArticulationSubset, "articulation_subset")
s1 = get_methods(ArticulationSubset, "articulation_subset")
subsnippets.append({"title": "ArticulationSubset", "snippets": [s0] + s1})

s0 = get_class(ArticulationView, "articulation_view")
s1 = get_methods(ArticulationView, "articulation_view")
s2 = get_methods(XFormPrimView, "articulation_view")
subsnippets.append({"title": "ArticulationView", "snippets": [s0] + s1 + s2})

snippets.append({"title": "Articulations", "snippets": subsnippets})

# controllers
subsnippets = []

s0 = get_class(ArticulationController, "articulation_controller")
s1 = get_methods(ArticulationController, "articulation_controller")
subsnippets.append({"title": "ArticulationController", "snippets": [s0] + s1})

s0 = get_class(BaseController, "base_controller")
s1 = get_methods(BaseController, "base_controller")
subsnippets.append({"title": "BaseController", "snippets": [s0] + s1})

s0 = get_class(BaseGripperController, "base_gripper_controller")
s1 = get_methods(BaseGripperController, "base_gripper_controller")
subsnippets.append({"title": "BaseGripperController", "snippets": [s0] + s1})

snippets.append({"title": "Controllers", "snippets": subsnippets})

# loggers
s0 = get_class(DataLogger, "data_logger")
s1 = get_methods(DataLogger, "data_logger")
snippets.append({"title": "DataLogger", "snippets": [s0] + s1})

# materials
subsnippets = []

s0 = get_class(OmniGlass, "omni_glass")
s1 = get_methods(OmniGlass, "omni_glass")
subsnippets.append({"title": "OmniGlass", "snippets": [s0] + s1})

s0 = get_class(OmniPBR, "omni_pbr")
s1 = get_methods(OmniPBR, "omni_pbr")
subsnippets.append({"title": "OmniPBR", "snippets": [s0] + s1})

s0 = get_class(ParticleMaterial, "particle_material")
s1 = get_methods(ParticleMaterial, "particle_material")
subsnippets.append({"title": "ParticleMaterial", "snippets": [s0] + s1})

s0 = get_class(ParticleMaterialView, "particle_material_view")
s1 = get_methods(ParticleMaterialView, "particle_material_view")
subsnippets.append({"title": "ParticleMaterialView", "snippets": [s0] + s1})

s0 = get_class(PhysicsMaterial, "physics_material")
s1 = get_methods(PhysicsMaterial, "physics_material")
subsnippets.append({"title": "PhysicsMaterial", "snippets": [s0] + s1})

s0 = get_class(PreviewSurface, "preview_surface")
s1 = get_methods(PreviewSurface, "preview_surface")
subsnippets.append({"title": "PreviewSurface", "snippets": [s0] + s1})

s0 = get_class(VisualMaterial, "visual_material")
s1 = get_methods(VisualMaterial, "visual_material")
subsnippets.append({"title": "VisualMaterial", "snippets": [s0] + s1})

snippets.append({"title": "Materials", "snippets": subsnippets})

# objects
subsnippets = []

s0 = get_class(DynamicCapsule, "dynamic_capsule")
s1 = get_methods(DynamicCapsule, "dynamic_capsule")
s2 = get_methods(RigidPrim, "dynamic_capsule")
s3 = get_methods(VisualCapsule, "dynamic_capsule")
s4 = get_methods(GeometryPrim, "dynamic_capsule")
s5 = get_methods(_SinglePrimWrapper, "dynamic_capsule")
subsnippets.append({"title": "DynamicCapsule", "snippets": [s0] + s1 + s2 + s3 + s4 + s5})

s0 = get_class(DynamicCone, "dynamic_cone")
s1 = get_methods(DynamicCone, "dynamic_cone")
s2 = get_methods(RigidPrim, "dynamic_cone")
s3 = get_methods(VisualCone, "dynamic_cone")
s4 = get_methods(GeometryPrim, "dynamic_cone")
s5 = get_methods(_SinglePrimWrapper, "dynamic_cone")
subsnippets.append({"title": "DynamicCone", "snippets": [s0] + s1 + s2 + s3 + s4 + s5})

s0 = get_class(DynamicCuboid, "dynamic_cuboid")
s1 = get_methods(DynamicCuboid, "dynamic_cuboid")
s2 = get_methods(RigidPrim, "dynamic_cuboid")
s3 = get_methods(VisualCuboid, "dynamic_cuboid")
s4 = get_methods(GeometryPrim, "dynamic_cuboid")
s5 = get_methods(_SinglePrimWrapper, "dynamic_cuboid")
subsnippets.append({"title": "DynamicCuboid", "snippets": [s0] + s1 + s2 + s3 + s4 + s5})

s0 = get_class(DynamicCylinder, "dynamic_cylinder")
s1 = get_methods(DynamicCylinder, "dynamic_cylinder")
s2 = get_methods(RigidPrim, "dynamic_cylinder")
s3 = get_methods(VisualCylinder, "dynamic_cylinder")
s4 = get_methods(GeometryPrim, "dynamic_cylinder")
s5 = get_methods(_SinglePrimWrapper, "dynamic_cylinder")
subsnippets.append({"title": "DynamicCylinder", "snippets": [s0] + s1 + s2 + s3 + s4 + s5})

s0 = get_class(DynamicSphere, "dynamic_sphere")
s1 = get_methods(DynamicSphere, "dynamic_sphere")
s2 = get_methods(RigidPrim, "dynamic_sphere")
s3 = get_methods(VisualSphere, "dynamic_sphere")
s4 = get_methods(GeometryPrim, "dynamic_sphere")
s5 = get_methods(_SinglePrimWrapper, "dynamic_sphere")
subsnippets.append({"title": "DynamicSphere", "snippets": [s0] + s1 + s2 + s3 + s4 + s5})


s0 = get_class(FixedCapsule, "fixed_capsule")
s1 = get_methods(VisualCapsule, "fixed_capsule")
s2 = get_methods(GeometryPrim, "fixed_capsule")
s3 = get_methods(_SinglePrimWrapper, "fixed_capsule")
subsnippets.append({"title": "FixedCapsule", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(FixedCone, "fixed_cone")
s1 = get_methods(VisualCone, "fixed_cone")
s2 = get_methods(GeometryPrim, "fixed_cone")
s3 = get_methods(_SinglePrimWrapper, "fixed_cone")
subsnippets.append({"title": "FixedCone", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(FixedCuboid, "fixed_cuboid")
s1 = get_methods(VisualCuboid, "fixed_cuboid")
s2 = get_methods(GeometryPrim, "fixed_cuboid")
s3 = get_methods(_SinglePrimWrapper, "fixed_cuboid")
subsnippets.append({"title": "FixedCuboid", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(FixedCylinder, "fixed_cylinder")
s1 = get_methods(VisualCylinder, "fixed_cylinder")
s2 = get_methods(GeometryPrim, "fixed_cylinder")
s3 = get_methods(_SinglePrimWrapper, "fixed_cylinder")
subsnippets.append({"title": "FixedCylinder", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(FixedSphere, "fixed_sphere")
s1 = get_methods(VisualSphere, "fixed_sphere")
s2 = get_methods(GeometryPrim, "fixed_sphere")
s3 = get_methods(_SinglePrimWrapper, "fixed_sphere")
subsnippets.append({"title": "FixedSphere", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(GroundPlane, "ground_plane")
s1 = get_methods(GroundPlane, "ground_plane")
subsnippets.append({"title": "GroundPlane", "snippets": [s0] + s1})


s0 = get_class(VisualCapsule, "visual_capsule")
s1 = get_methods(VisualCapsule, "visual_capsule")
s2 = get_methods(GeometryPrim, "visual_capsule")
s3 = get_methods(_SinglePrimWrapper, "visual_capsule")
subsnippets.append({"title": "VisualCapsule", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(VisualCone, "visual_cone")
s1 = get_methods(VisualCone, "visual_cone")
s2 = get_methods(GeometryPrim, "visual_cone")
s3 = get_methods(_SinglePrimWrapper, "visual_cone")
subsnippets.append({"title": "VisualCone", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(VisualCuboid, "visual_cuboid")
s1 = get_methods(VisualCuboid, "visual_cuboid")
s2 = get_methods(GeometryPrim, "visual_cuboid")
s3 = get_methods(_SinglePrimWrapper, "visual_cuboid")
subsnippets.append({"title": "VisualCuboid", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(VisualCylinder, "visual_cylinder")
s1 = get_methods(VisualCylinder, "visual_cylinder")
s2 = get_methods(GeometryPrim, "visual_cylinder")
s3 = get_methods(_SinglePrimWrapper, "visual_cylinder")
subsnippets.append({"title": "VisualCylinder", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(VisualSphere, "visual_sphere")
s1 = get_methods(VisualSphere, "visual_sphere")
s2 = get_methods(GeometryPrim, "visual_sphere")
s3 = get_methods(_SinglePrimWrapper, "visual_sphere")
subsnippets.append({"title": "VisualSphere", "snippets": [s0] + s1 + s2 + s3})

snippets.append({"title": "Objects", "snippets": subsnippets})

# physics_context
s0 = get_class(PhysicsContext, "physics_context")
s1 = get_methods(PhysicsContext, "physics_context")
snippets.append({"title": "PhysicsContext", "snippets": [s0] + s1})

# prims
subsnippets = []

s0 = get_class(BaseSensor, "base_sensor")
s1 = get_methods(BaseSensor, "base_sensor")
s2 = get_methods(_SinglePrimWrapper, "base_sensor")
subsnippets.append({"title": "BaseSensor", "snippets": [s0] + s1 + s2})

s0 = get_class(ClothPrim, "cloth_prim")
s1 = get_methods(ClothPrim, "cloth_prim")
s2 = get_methods(_SinglePrimWrapper, "cloth_prim")
subsnippets.append({"title": "ClothPrim", "snippets": [s0] + s1 + s2})

s0 = get_class(ClothPrimView, "cloth_prim_view")
s1 = get_methods(ClothPrimView, "cloth_prim_view")
s2 = get_methods(XFormPrimView, "cloth_prim_view")
subsnippets.append({"title": "ClothPrimView", "snippets": [s0] + s1 + s2})

s0 = get_class(GeometryPrim, "geometry_prim")
s1 = get_methods(GeometryPrim, "geometry_prim")
s2 = get_methods(_SinglePrimWrapper, "geometry_prim")
subsnippets.append({"title": "GeometryPrim", "snippets": [s0] + s1 + s2})

s0 = get_class(GeometryPrimView, "geometry_prim_view")
s1 = get_methods(GeometryPrimView, "geometry_prim_view")
s2 = get_methods(XFormPrimView, "geometry_prim_view")
subsnippets.append({"title": "GeometryPrimView", "snippets": [s0] + s1 + s2})

s0 = get_class(ParticleSystem, "particle_system")
s1 = get_methods(ParticleSystem, "particle_system")
subsnippets.append({"title": "ParticleSystem", "snippets": [s0] + s1})

s0 = get_class(ParticleSystemView, "particle_system_view")
s1 = get_methods(ParticleSystemView, "particle_system_view")
subsnippets.append({"title": "ParticleSystemView", "snippets": [s0] + s1})

s0 = get_class(RigidContactView, "rigid_contact_view")
s1 = get_methods(RigidContactView, "rigid_contact_view")
subsnippets.append({"title": "RigidContactView", "snippets": [s0] + s1})

s0 = get_class(RigidPrim, "rigid_prim")
s1 = get_methods(RigidPrim, "rigid_prim")
s2 = get_methods(_SinglePrimWrapper, "rigid_prim")
subsnippets.append({"title": "RigidPrim", "snippets": [s0] + s1 + s2})

s0 = get_class(RigidPrimView, "rigid_prim_view")
s1 = get_methods(RigidPrimView, "rigid_prim_view")
s2 = get_methods(XFormPrimView, "rigid_prim_view")
subsnippets.append({"title": "RigidPrimView", "snippets": [s0] + s1 + s2})

s0 = get_class(XFormPrim, "xform_prim")
s1 = get_methods(XFormPrim, "xform_prim")
s2 = get_methods(_SinglePrimWrapper, "xform_prim")
subsnippets.append({"title": "XFormPrim", "snippets": [s0] + s1 + s2})

s0 = get_class(XFormPrimView, "xform_prim_view")
s1 = get_methods(XFormPrimView, "xform_prim_view")
subsnippets.append({"title": "XFormPrimView", "snippets": [s0] + s1})

snippets.append({"title": "Prims", "snippets": subsnippets})

# robots
subsnippets = []

s0 = get_class(Robot, "robot")
s1 = get_methods(Robot, "robot")
s2 = get_methods(Articulation, "robot")
s3 = get_methods(_SinglePrimWrapper, "robot")
subsnippets.append({"title": "Robot", "snippets": [s0] + s1 + s2 + s3})

s0 = get_class(RobotView, "robot_view")
s1 = get_methods(RobotView, "robot_view")
s2 = get_methods(ArticulationView, "robot_view")
s3 = get_methods(XFormPrimView, "robot_view")
subsnippets.append({"title": "RobotView", "snippets": [s0] + s1 + s2 + s3})

snippets.append({"title": "Robots", "snippets": subsnippets})

# scenes
subsnippets = []

s0 = get_class(Scene, "scene")
s1 = get_methods(Scene, "scene")
subsnippets.append({"title": "Scene", "snippets": [s0] + s1})

s0 = get_class(SceneRegistry, "scene_registry")
s1 = get_methods(SceneRegistry, "scene_registry")
subsnippets.append({"title": "SceneRegistry", "snippets": [s0] + s1})

snippets.append({"title": "Scenes", "snippets": subsnippets})

# simulation_context
s0 = get_class(SimulationContext, "simulation_context")
s1 = get_methods(SimulationContext, "simulation_context")
snippets.append({"title": "SimulationContext", "snippets": [s0] + s1})

# world
s0 = get_class(World, "world")
s1 = get_methods(World, "world")
s2 = get_methods(SimulationContext, "world")
snippets.append({"title": "World", "snippets": [s0] + s1 + s2})

# tasks
subsnippets = []

s0 = get_class(BaseTask, "base_task")
s1 = get_methods(BaseTask, "base_task")
subsnippets.append({"title": "BaseTask", "snippets": [s0] + s1})

s0 = get_class(FollowTarget, "follow_target")
s1 = get_methods(FollowTarget, "follow_target")
s2 = get_methods(BaseTask, "follow_target")
subsnippets.append({"title": "FollowTarget", "snippets": [s0] + s1 + s2})

s0 = get_class(PickPlace, "pick_place")
s1 = get_methods(PickPlace, "pick_place")
s2 = get_methods(BaseTask, "pick_place")
subsnippets.append({"title": "PickPlace", "snippets": [s0] + s1 + s2})

s0 = get_class(Stacking, "stacking")
s1 = get_methods(Stacking, "stacking")
s2 = get_methods(BaseTask, "stacking")
subsnippets.append({"title": "Stacking", "snippets": [s0] + s1 + s2})

snippets.append({"title": "Tasks", "snippets": subsnippets})




# core utils
snippets_utils = []

s0 = get_functions(utils_bounds, "bounds_utils", exclude_functions=["get_prim_at_path"])
snippets_utils.append({"title": "Bounds", "snippets": s0})

s0 = get_functions(utils_carb, "carb_utils")
snippets_utils.append({"title": "Carb", "snippets": s0})

s0 = get_functions(utils_collisions, "collisions_utils", exclude_functions=["get_current_stage"])
snippets_utils.append({"title": "Collisions", "snippets": s0})

s0 = get_functions(utils_constants, "constants_utils")
snippets_utils.append({"title": "Constants", "snippets": [{"title": "AXES_INDICES", "description": "Mapping from axis name to axis ID", "snippet": "AXES_INDICES\n"},
                                                          {"title": "AXES_TOKEN", "description": "Mapping from axis name to axis USD token", "snippet": "AXES_TOKEN\n"}]})

s0 = get_functions(utils_distance_metrics, "distance_metrics_utils")
snippets_utils.append({"title": "Distance Metrics", "snippets": s0})

s0 = get_functions(utils_extensions, "extensions_utils")
snippets_utils.append({"title": "Extensions", "snippets": s0})

s0 = get_functions(utils_math, "math_utils")
snippets_utils.append({"title": "Math", "snippets": s0})

s0 = get_functions(utils_mesh, "mesh_utils", exclude_functions=["get_stage_units", "get_relative_transform"])
snippets_utils.append({"title": "Mesh", "snippets": s0})

s0 = get_functions(utils_nucleus, "nucleus_utils", exclude_functions=["namedtuple", "urlparse", "get_version"])
snippets_utils.append({"title": "Nucleus", "snippets": s0})

s0 = get_functions(utils_numpy, "numpy_utils")
snippets_utils.append({"title": "Numpy", "snippets": s0})

s0 = get_functions(utils_physics, "physics_utils", exclude_functions=["get_current_stage"])
snippets_utils.append({"title": "Physics", "snippets": s0})

s0 = get_functions(utils_prims, "prims_utils", exclude_functions=["add_reference_to_stage", "get_current_stage", "find_root_prim_path_from_regex", "add_update_semantics"])
snippets_utils.append({"title": "Prims", "snippets": s0})

s0 = get_functions(utils_random, "random_utils", exclude_functions=["get_world_pose_from_relative", "get_translation_from_target", "euler_angles_to_quat"])
snippets_utils.append({"title": "Random", "snippets": s0})

s0 = get_functions(utils_render_product, "render_product_utils", exclude_functions=["set_prim_hide_in_stage_window", "set_prim_no_delete", "get_current_stage"])
snippets_utils.append({"title": "Render Product", "snippets": s0})

s0 = get_functions(utils_rotations, "rotations_utils")
snippets_utils.append({"title": "Rotations", "snippets": s0})

s0 = get_functions(utils_semantics, "semantics_utils")
snippets_utils.append({"title": "Semantics", "snippets": s0})

s0 = get_functions(utils_stage, "stage_utils")
snippets_utils.append({"title": "Stage", "snippets": s0})

s0 = get_functions(utils_string, "string_utils")
snippets_utils.append({"title": "String", "snippets": s0})

s0 = get_functions(utils_transformations, "transformations_utils", exclude_functions=["gf_quat_to_np_array"])
snippets_utils.append({"title": "Transformations", "snippets": s0})

s0 = get_functions(utils_torch, "torch_utils")
snippets_utils.append({"title": "Torch", "snippets": s0})

subsnippets = []

s0 = get_class(utils_types.ArticulationAction, "articulation_action")
s1 = get_methods(utils_types.ArticulationAction, "articulation_action")
subsnippets.append({"title": "ArticulationAction", "snippets": [s0] + s1})

s0 = get_class(utils_types.ArticulationActions, "articulation_actions")
subsnippets.append(s0)

s0 = get_class(utils_types.DataFrame, "data_frame")
s1 = get_methods(utils_types.DataFrame, "data_frame")
subsnippets.append({"title": "DataFrame", "snippets": [s0] + s1})

s0 = get_class(utils_types.DOFInfo, "dof_Info")
subsnippets.append(s0)

s0 = get_class(utils_types.DynamicState, "dynamic_state")
subsnippets.append(s0)

s0 = get_class(utils_types.DynamicsViewState, "dynamics_view_state")
subsnippets.append(s0)

s0 = get_class(utils_types.JointsState, "joints_state")
subsnippets.append(s0)

s0 = get_class(utils_types.XFormPrimState, "xform_prim_state")
subsnippets.append(s0)

s0 = get_class(utils_types.XFormPrimViewState, "xform_prim_view_state")
subsnippets.append(s0)

s0 = get_functions(utils_types, "types_utils")
snippets_utils.append({"title": "Types", "snippets": subsnippets})

s0 = get_functions(utils_viewports, "viewports_utils", exclude_functions=["get_active_viewport", "get_current_stage", "set_prim_hide_in_stage_window", "set_prim_no_delete"])
snippets_utils.append({"title": "Viewports", "snippets": s0})

s0 = get_functions(utils_xforms, "xforms_utils")
snippets_utils.append({"title": "XForms", "snippets": s0})




# ui utils
snippets_ui_utils = []

s0 = get_functions(ui_utils, "ui_utils")
snippets_ui_utils.append({"title": "UI Utils", "snippets": s0})




# SimulationApp
snippets_simulation_app = []

s0 = get_class(SimulationApp, "simulation_app")
s1 = get_methods(SimulationApp, "simulation_app")
snippets_simulation_app.append({"title": "SimulationApp", "snippets": [s0] + s1})





with open("isaac-sim-snippets-core.json", "w") as f:
    json.dump(snippets, f, indent=0)

with open("isaac-sim-snippets-utils.json", "w") as f:
    json.dump(snippets_utils, f, indent=0)

with open("isaac-sim-snippets-ui-utils.json", "w") as f:
    json.dump(snippets_ui_utils, f, indent=0)

with open("isaac-sim-snippets-simulation-app.json", "w") as f:
    json.dump(snippets_simulation_app, f, indent=0)

print("DONE")
