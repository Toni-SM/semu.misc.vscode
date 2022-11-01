import os
import json


def merge(snippets, app):
    for s in app["snippets"]:

        exists = False
        for ss in snippets:
            if s["title"] == ss["title"]:
                exists = True
                break
        
        # add section
        if not exists:
            print("  |-- new: {} ({})".format(s["title"], len(s["snippets"])))
            snippets.append(s)
        
        # update section
        else:
            print("  |-- update: {} ({} <- {})".format(s["title"], len(ss["snippets"]), len(s["snippets"])))
            for subs in s["snippets"]:
                exists = False
                for subss in ss["snippets"]:
                    if subs["title"] == subss["title"]:
                        exists = True
                        break
                
                if not exists:
                    print("  |     |-- add:", subs["title"])
                    ss["snippets"].append(subs)


snippets = []

# merge
print("CREATE")
with open(os.path.join("commands", "kit-commands-create.json")) as f: 
    merge(snippets, json.load(f))
print("CODE")
with open(os.path.join("commands", "kit-commands-code.json")) as f: 
    merge(snippets, json.load(f))
print("ISAAC SIM")
with open(os.path.join("commands", "kit-commands-isaac-sim.json")) as f: 
    merge(snippets, json.load(f))

# sort snippets
snippets = sorted(snippets, key=lambda d: d["title"]) 
for s in snippets:
    s["snippets"] = sorted(s["snippets"], key=lambda d: d["title"])


# save snippets 
with open("kit-commands.json", "w") as f:
    json.dump({"snippets": snippets}, f, indent=0)

print("done")