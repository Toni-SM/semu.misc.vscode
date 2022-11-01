import json


title = "TITLE"

description = "DESCRIPTION"

# placehorlders syntax: ${1:foo}, ${2:bar}, $0.
# placeholder traversal order is ascending by number, starting from one.
# zero is an optional special case that always comes last, 
#   and exits snippet mode with the cursor at the specified position
snippet = """
CODE
"""


# generate entry
print()
print(json.dumps({"title": title, 
                  "description": description, 
                  "snippet":snippet[1:]},  # remove first line break
                 indent=4))
print()
