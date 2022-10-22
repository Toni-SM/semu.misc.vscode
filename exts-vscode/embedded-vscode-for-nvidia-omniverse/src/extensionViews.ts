import * as vscode from 'vscode';
import * as path from 'path'

export class CommandTreeView {
    private readonly commandTreeViewProvider: CommandTreeViewProvider

    constructor() {
        this.commandTreeViewProvider = new CommandTreeViewProvider()
        vscode.window.createTreeView('embedded-vscode-for-nvidia-omniverse-views-commands', 
									 {treeDataProvider: this.commandTreeViewProvider, showCollapseAll: true});
    }
}


export class CommandTreeViewProvider implements vscode.TreeDataProvider<Command> {
	private commands: Command[] = []

	constructor() {
		// codicon: https://microsoft.github.io/vscode-codicons/dist/codicon.html

		let icon1, icon2, icon3, icon4: vscode.Uri | undefined;
		// const currentExtension = vscode.extensions.getExtension("Toni-SM.embedded-vscode-for-nvidia-omniverse");

		// if (currentExtension){
		// 	icon1 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run.svg"));
		// 	icon2 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run-selected.svg"));
		// 	icon3 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run-remote.svg"));
		// 	icon4 = vscode.Uri.file(path.join(currentExtension.extensionPath, 'images', "command-run-remote-selected.svg"));
		// }

		this.commands.push(new Command("Run", 
									   {command: "embedded-vscode-for-nvidia-omniverse.run"}, 
									   icon1 || new vscode.ThemeIcon("play")));
		this.commands.push(new Command("Run Selected Text", 
						   			   {command: "embedded-vscode-for-nvidia-omniverse.runSelectedText"}, 
						   			   icon2 || new vscode.ThemeIcon("play")));
		this.commands.push(new Command("---------------------------", {command: ""}));
		this.commands.push(new Command("Run Remotely", 
									   {command: "embedded-vscode-for-nvidia-omniverse.runRemotely"}, 
									   icon3 || new vscode.ThemeIcon("run-all")));
		this.commands.push(new Command("Run Selected Text Remotely", 
						  			   {command: "embedded-vscode-for-nvidia-omniverse.runSelectedTextRemotely"}, 
						   			   icon4 || new vscode.ThemeIcon("run-all")));
	}

	getTreeItem(element: Command): vscode.TreeItem {
		return element;
	}

	getChildren(element?: Command): Command[] {
		return this.commands;
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
