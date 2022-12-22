import * as vscode from 'vscode';
import {readFileSync} from 'fs'
import * as path from 'path'


export class CommandTreeView {
    private readonly commandTreeViewProvider: CommandTreeViewProvider

    constructor() {
        this.commandTreeViewProvider = new CommandTreeViewProvider()
        vscode.window.createTreeView('embedded-vscode-for-nvidia-omniverse-views-commands', 
                                     {treeDataProvider: this.commandTreeViewProvider, showCollapseAll: true});
    }
}


export class SnippetTreeView {
    private snippetTreeViewProvider: SnippetTreeViewProvider;
    private treeView: vscode.TreeView<Snippet>;

    constructor(snippetLanguage: string) {
        this.snippetTreeViewProvider = new SnippetTreeViewProvider(snippetLanguage, true)
        this.treeView = vscode.window.createTreeView('embedded-vscode-for-nvidia-omniverse-views-snippets', 
                                                     {treeDataProvider: this.snippetTreeViewProvider, showCollapseAll: true});
    }

    public expandAll(): void {
        this.snippetTreeViewProvider.expandAll(this.treeView);
    }
}


export class ResourceTreeView {
    private readonly resourceTreeViewProvider: ResourceTreeViewProvider

    constructor() {
        this.resourceTreeViewProvider = new ResourceTreeViewProvider()
        vscode.window.createTreeView('embedded-vscode-for-nvidia-omniverse-views-resources', 
                                     {treeDataProvider: this.resourceTreeViewProvider, showCollapseAll: true});
    }
}


class CommandTreeViewProvider implements vscode.TreeDataProvider<Command> {
    private commands: Command[] = []

    constructor() {
        // codicon: https://microsoft.github.io/vscode-codicons/dist/codicon.html

        // let icon1, icon2, icon3, icon4: vscode.Uri | undefined;
        // const currentExtension = vscode.extensions.getExtension("Toni-SM.embedded-vscode-for-nvidia-omniverse");

        // if (currentExtension){
        // 	icon1 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run.svg"));
        // 	icon2 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run-selected.svg"));
        // 	icon3 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run-remote.svg"));
        // 	icon4 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run-remote-selected.svg"));
        // }

        this.commands.push(new Command("Run", 
                                       {command: "embedded-vscode-for-nvidia-omniverse.run"}, 
                                       new vscode.ThemeIcon("play")));
        this.commands.push(new Command("Run selected text", 
                                       {command: "embedded-vscode-for-nvidia-omniverse.runSelectedText"}, 
                                       new vscode.ThemeIcon("play")));
        this.commands.push(new Command("---", {command: ""}));
        this.commands.push(new Command("Run remotely", 
                                       {command: "embedded-vscode-for-nvidia-omniverse.runRemotely"}, 
                                       new vscode.ThemeIcon("run-all")));
        this.commands.push(new Command("Run selected text remotely", 
                                       {command: "embedded-vscode-for-nvidia-omniverse.runSelectedTextRemotely"}, 
                                       new vscode.ThemeIcon("run-all")));
        this.commands.push(new Command("---", {command: ""}));
        this.commands.push(new Command("Clear output", 
                                       {command: "workbench.output.action.clearOutput"}, 
                                       new vscode.ThemeIcon("clear-all")));
    }

    getTreeItem(element: Command): vscode.TreeItem {
        return element;
    }

    getChildren(element?: Command): Command[] {
        return this.commands;
    }
}


class SnippetTreeViewProvider implements vscode.TreeDataProvider<Snippet> {
    private snippets: Snippet[] = []

    constructor(snippetLanguage: string, collapsed: boolean) {
        if(snippetLanguage == "python") {
            this.snippets.push(this.buildSubtree("Kit", this.parseJSON("python-kit.json"), collapsed));
            this.snippets.push(this.buildSubtree("Kit commands", this.parseJSON("python-kit-commands.json"), collapsed));
            this.snippets.push(this.buildSubtree("USD", this.parseJSON("python-usd.json"), collapsed));
            this.snippets.push(this.buildSubtree("Isaac Sim", this.parseJSON("python-isaac-sim.json"), collapsed));
        }
        else if(snippetLanguage == "cpp") {
            this.snippets.push(this.buildSubtree("Kit", this.parseJSON("cpp-usd.json"), collapsed));
        }
    }

    getTreeItem(element: Snippet): vscode.TreeItem {
        return element;
    }

    getChildren(element?: Snippet): Snippet[] {
        if (!element)
            return this.snippets
        return element.children
    }

    getParent(element: Snippet) {
        return element.parent
    }

    private buildSubtree(treeName: string, snippets: {title: string, snippets: [], url: string, snippet: string, description: string}[], collapsed: boolean): Snippet {
        let children: Snippet[] = [];
        
        for (var val of snippets) {
            if(val.hasOwnProperty("snippets"))
                children.push(this.buildSubtree(val.title, val.snippets, collapsed));
            else
                children.push(new Snippet(val.title, {command: 'embedded-vscode-for-nvidia-omniverse.insertSnippet', arguments: [val.snippet]}, val.description));
        }
        
        const parent = new Snippet(treeName, {command: ''});
        if (children.length > 0) {
            if (collapsed)
                parent.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed
            else
                parent.collapsibleState = vscode.TreeItemCollapsibleState.Expanded
            parent.children = children
            children.forEach((c) => c.parent = parent)
        }
        return parent
    }

    private parseJSON(jsonFile: string): [] {
        const currentExtension = vscode.extensions.getExtension("Toni-SM.embedded-vscode-for-nvidia-omniverse");
        if (currentExtension){
            const rawSnippets = JSON.parse(readFileSync(path.join(currentExtension.extensionPath, 'snippets', jsonFile), { encoding: 'utf8' }));
            return rawSnippets.snippets;
        }
        return [];
    }

    private expandSnippet(treeView: vscode.TreeView<Snippet>, snippet: Snippet): void {
        if (snippet.children.length > 0) {
            treeView.reveal(snippet, {select: false, focus: false, expand: 3});
            for (var child of snippet.children)
                this.expandSnippet(treeView, child);
        }
    }

    public expandAll(treeView: vscode.TreeView<Snippet>): void {
        for (var snippet of this.snippets)
            treeView.reveal(snippet, {select: false, focus: false, expand: 3});
            // this.expandSnippet(treeView, snippet);
    }
}


class ResourceTreeViewProvider implements vscode.TreeDataProvider<Resource> {
    private resources: Resource[] = []

    constructor() {
        this.resources.push(this.buildSubtree("Developer", this.parseJSON("developer.json")));
        this.resources.push(this.buildSubtree("Documentation", this.parseJSON("documentation.json")));
        this.resources.push(this.buildSubtree("Forum (external)", this.parseJSON("forums.json")));
        this.resources.push(this.buildSubtree("Isaac Sim: Extensions API", this.parseJSON("isaac-sim_extensions.json")));
    }

    getTreeItem(element: Resource): vscode.TreeItem {
        return element;
    }

    getChildren(element?: Resource): Resource[] {
        if (!element)
            return this.resources
        return element.children
    }

    getParent(element: Resource) {
        return element.parent
    }

    private buildSubtree(treeName: string, resources: {title: string, resources: [], url: string, internal: string, description: string}[]): Resource {
        let children: Resource[] = [];
        
        for (var val of resources) {
            if( val.hasOwnProperty("resources"))
                children.push(this.buildSubtree(val.title, val.resources));
            else
                children.push(new Resource(val.title, {command: 'embedded-vscode-for-nvidia-omniverse.openResource', arguments: [val.title, val.url, val.internal]}, val.description));
        }
        
        const parent = new Resource(treeName, {command: ''});
        if (children.length > 0) {
            parent.collapsibleState = vscode.TreeItemCollapsibleState.Collapsed
            parent.children = children
            children.forEach((c) => c.parent = parent)
        }
        return parent
    }

    private parseJSON(jsonFile: string): [] {
        const currentExtension = vscode.extensions.getExtension("Toni-SM.embedded-vscode-for-nvidia-omniverse");
        if (currentExtension){
            const rawResources = JSON.parse(readFileSync(path.join(currentExtension.extensionPath, 'resources', jsonFile), { encoding: 'utf8' }));
            return rawResources.resources;
        }
        return [];
    }
}


class Command extends vscode.TreeItem {
    public readonly command: vscode.Command | undefined

    constructor(public readonly label: string, 
                command: {command: string, arguments?: string[]},
                public readonly iconPath?: string | vscode.Uri | vscode.ThemeIcon | undefined) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.command = {...command, title: ''};
        if (iconPath)
            this.iconPath = iconPath;
    }
}


class Snippet extends vscode.TreeItem {
    public children: Snippet[] = []
    public parent: Snippet | undefined = undefined

    public readonly command: vscode.Command | undefined

    constructor(public label: string,
                command: {command: string, arguments?: string[], tooltip?: string},
                public tooltip?: string | undefined) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.command = {...command, title: ''};
        if (tooltip)
            this.tooltip = tooltip;
    }
}


class Resource extends vscode.TreeItem {
    public children: Resource[] = []
    public parent: Resource | undefined = undefined

    public readonly command: vscode.Command | undefined

    constructor(public label: string,
                command: {command: string, arguments?: string[], tooltip?: string},
                public tooltip?: string | undefined) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.command = {...command, title: ''};
        if (tooltip)
            this.tooltip = tooltip;
    }
}
