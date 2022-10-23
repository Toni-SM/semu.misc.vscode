import * as vscode from 'vscode';
import * as net from 'net';
import * as dgram from 'dgram';

import {CommandTreeView, SnippetTreeView, ResourceTreeView} from './extensionViews';


function logCarb(ip: string, port: number, outputChannel: vscode.OutputChannel) {
	let socket: dgram.Socket = dgram.createSocket('udp4');
	socket.on('message', (msg, rinfo) => {
		outputChannel.appendLine(`${new Date().toLocaleTimeString()} ${msg}`);
	}).on('error', (err) => {
		console.error('embedded-vscode-for-nvidia-omniverse: UDP connection error: ' + err.message);
	}).on('close', () => {
		console.log('embedded-vscode-for-nvidia-omniverse: UDP connection closed');
	});

	// Send alive message on specified interval
	setInterval(() => {
		socket.send('*', port, ip);
	}, 5000);
}

function executeCode(ip: string, port: number, outputChannel: vscode.OutputChannel, selectedText: boolean) {
	// Get editor
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		vscode.window.showWarningMessage('[Embedded VS Code for NVIDIA Omniverse] No active editor found');
		return;
	}
	let document = editor.document;

	// Get the document text
	let selection = undefined;
	if (selectedText) {
		selection = editor.selection;
	}
	const documentText = document.getText(selection);

	if (documentText.length == 0) {
		vscode.window.showWarningMessage('[Embedded VS Code for NVIDIA Omniverse] No text available or selected');
		return;
	}

	// Get extension configuration
	const config = vscode.workspace.getConfiguration();
	const clearAfterRun = config.get('output', {"clearBeforeRun": true}).clearBeforeRun;

	// Create TCP socket client
	let socket: net.Socket = new net.Socket();

	// Connect to server, send text, and show output
	socket.connect(port, ip, () => {
		// Clear output if needed
		if (clearAfterRun) {
			outputChannel.clear();
		}
		// Print info to output
		const extraInfo = selectedText ? ' selected text' : '';
		outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] executing${extraInfo} at ${ip}:${port}...`);
		// Send text to be executed
		socket.write(documentText);
	}).on('data', (data) => {
		outputChannel.show();
		let reply = JSON.parse(data.toString());
		// Show successfull execution
		if (reply.status === 'ok') {
			if (reply.output.length > 0) {
				outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] executed with output:`);
				outputChannel.appendLine(reply.output);
			}
			else {
				outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] executed without output`);
			}
		}
		// Show error during execution
		else if (reply.status === 'error') {
			if (reply.output.length > 0) {
				outputChannel.appendLine(reply.output);
			}
			outputChannel.appendLine('--------------------------------------------------');
			outputChannel.appendLine('Traceback (most recent call last) ' + reply.traceback);
			outputChannel.appendLine('');
		}
		socket.destroy();
	})
	.on('close', () => {
	}).on('error', (err) => {
		vscode.window.showErrorMessage('[Embedded VS Code for NVIDIA Omniverse] Connection error: ' + err.message);
		console.error('embedded-vscode-for-nvidia-omniverse: TCP connection error: ' + err.message);
		socket.destroy();
	}).on('timeout', () => {
		console.log('embedded-vscode-for-nvidia-omniverse: timeout');
	});
}

function getWebviewContent(resourceUrl: string) {
	return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
	<style>
		html, body {
			margin: 0;
			padding: 0;
			width: 100%;
			height: 100%;
			min-height: 100%;
		}
		body > iframe {
			border: 0;
		}
	</style>
</head>
<body>
	<iframe width="100%" height="100%" frameBorder="0" src="${resourceUrl}"></iframe>
</body>
</html>`;
}

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	
	// create/register TreeDataProvider
	const commandTreeView = new CommandTreeView();
	const snippetTreeView = new SnippetTreeView();
	const resourceTreeView = new ResourceTreeView();

	// Get configuration
	const config = vscode.workspace.getConfiguration();
	const localSocketPort = config.get('localSocket', {"extensionPort": 8226}).extensionPort;
	const remoteSocketIp = config.get('remoteSocket', {"extensionIp": "127.0.0.1"}).extensionIp;
	const remoteSocketPort = config.get('remoteSocket', {"extensionPort": 8226}).extensionPort;

	// Get OUTPUT panel
	let outputChannel = vscode.window.createOutputChannel('Embedded VS Code for NVIDIA Omniverse');  //, 'python');
	
	// carb logging
	if (config.get('output', {"carbLogging": true}).carbLogging) {	
		let outputChannelCarb = vscode.window.createOutputChannel('Embedded VS Code for NVIDIA Omniverse (carb logging)');  //, 'python');
		
		// UDP clients for carb.log_*
		logCarb('127.0.0.1', localSocketPort, outputChannelCarb);
		if (remoteSocketIp != '127.0.0.1' && remoteSocketIp != 'localhost') {
			logCarb(remoteSocketIp, localSocketPort, outputChannelCarb);
		}
	}

	// Local execution
	let disposable_local = vscode.commands.registerCommand('embedded-vscode-for-nvidia-omniverse.run', () => {
		executeCode('127.0.0.1', localSocketPort, outputChannel, false);
	});

	let disposable_local_selected_text = vscode.commands.registerCommand('embedded-vscode-for-nvidia-omniverse.runSelectedText', () => {
		executeCode('127.0.0.1', localSocketPort, outputChannel, true);
	});

	// Remote execution
	let disposable_remote = vscode.commands.registerCommand('embedded-vscode-for-nvidia-omniverse.runRemotely', () => {
		executeCode(remoteSocketIp, remoteSocketPort, outputChannel, false);
	});

	let disposable_remote_selected_text = vscode.commands.registerCommand('embedded-vscode-for-nvidia-omniverse.runSelectedTextRemotely', () => {
		executeCode(remoteSocketIp, remoteSocketPort, outputChannel, true);
	});

	// Snippet
	let disposable_insert_snippet = vscode.commands.registerCommand('embedded-vscode-for-nvidia-omniverse.insertSnippet', (args) => {
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showWarningMessage('[Embedded VS Code for NVIDIA Omniverse] No active editor found');
			return;
		}
		editor.insertSnippet(new vscode.SnippetString(args)).then(
			() => {},
			err => { vscode.window.showWarningMessage(`[Embedded VS Code for NVIDIA Omniverse] Unable to insert snippet: ${err}`); }
		);
	});
		
	// Open resource
	let disposable_open_resource = vscode.commands.registerCommand('embedded-vscode-for-nvidia-omniverse.openResource', (title, args, openInternal) => {
		// internal view
		if (openInternal) {
			const panel = vscode.window.createWebviewPanel(
				'resource', // type of the webview panel
				title, // panel title
				vscode.ViewColumn.Beside, // editor column to show the panel in
				{enableScripts: true} // Webview options
			);
			panel.webview.html = getWebviewContent(args);
		}
		// external view
		else {
			vscode.env.openExternal(vscode.Uri.parse(args));
		}
	});
	
	context.subscriptions.push(disposable_local);
	context.subscriptions.push(disposable_local_selected_text);
	context.subscriptions.push(disposable_remote);
	context.subscriptions.push(disposable_remote_selected_text);
	context.subscriptions.push(disposable_insert_snippet);
	context.subscriptions.push(disposable_open_resource);
}

export function deactivate() {
}
