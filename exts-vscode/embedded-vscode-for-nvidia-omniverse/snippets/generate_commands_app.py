import json
import inspect
import collections

count = 0
snippets = []
snippets_by_extensions_depth = 2
snippets_by_extensions = collections.defaultdict(list)


def class_fullname(c):
    try:
        module = c.__module__
        if module == 'builtins':
            return c.__name__
        return module + '.' + c.__name__
    except:
        return str(c)

from pxr import Sdf
commands = omni.kit.commands.get_commands()

for k, v in commands.items():
    # count += 1
    # print()
    # if count > 20:
    #     break

    if v:
        command_class = list(v.values())[0]
        command_extension = list(v.keys())[0]

        spec = inspect.getfullargspec(command_class.__init__)
        signature = inspect.signature(command_class.__init__)

        command = command_class.__qualname__
        command_args = []
        command_annotations = []

        for parameter in signature.parameters.values():
            if parameter.name in ["self", "args", "kwargs"]:
                continue
            # arg
            if type(parameter.default) == type(inspect.Parameter.empty):
                command_args.append("{}={}".format(parameter.name, parameter.name))
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
                command_args.append("{}={}".format(parameter.name, default_value))
            # annotation
            if parameter.annotation == inspect.Parameter.empty:
                command_annotations.append("")
            else:
                command_annotations.append(class_fullname(parameter.annotation))

        # build snippet
        arguments_as_string = '")'
        if command_args:
            arguments_as_string = '",\n'
        
        for i, arg, annotation in zip(range(len(command_args)), command_args, command_annotations):
            is_last = i >= len(command_args) - 1
            if annotation:
                arguments_as_string += " " * 26 + "{}{}".format(arg, ")  # {}".format(annotation) if is_last else ",  # {}\n".format(annotation))
            else:
                arguments_as_string += " " * 26 + "{}{}".format(arg, ")" if is_last else ",\n")

        title = command
        try:
            description = command_class.__doc__.replace("\n    ", "\n").replace(" **Command**", "")
            if description.startswith("\n"):
                description = description[1:]
            if description.endswith("\n"):
                description = description[:-1]
            while "  " in description:
                description = description.replace("  ", " ")
            description = "[{}]\n\n".format(command_extension) + description
        except Exception as e:
            description = None
        if not description:
            description = "[{}]".format(command_extension)
        snippet = 'omni.kit.commands.execute("{}{}'.format(command, arguments_as_string) + "\n"
        
        # storage snippet (all)
        snippets.append({"title": title, "description": description, "snippet": snippet})
        # storage snippet (by extension)
        command_extension = ".".join(command_extension.split(".")[:snippets_by_extensions_depth])
        snippets_by_extensions[command_extension].append({"title": title, "description": description, "snippet": snippet})


snippets = []
for title, snippets_by_extension in snippets_by_extensions.items():
    snippets.append({"title": title, "snippets": snippets_by_extension})

with open("kit-commands.json", "w") as f:
    json.dump({"snippets": snippets}, f, indent=0)

print("done")