import * as vscode from 'vscode';
import * as net from 'net';


function executeCode(ip: string, port: number, outputChannel: vscode.OutputChannel) {
	// Get editor
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		vscode.window.showWarningMessage('[Embedded Python for NVIDIA Omniverse] No active editor found');
		return;
	}
	let document = editor.document;

	// Get the document text
	const documentText = document.getText();
	if (documentText.length === 0) {
		vscode.window.showWarningMessage('[Embedded Python for NVIDIA Omniverse] No text found');
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
		outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] executing at ${ip}:${port}...`);
		// Send text to be executed
		socket.write(documentText);
	}).on('data', (data) => {
		outputChannel.show();
		let reply = JSON.parse(data.toString());
		// Show successfull execution
		if (reply.status === 'ok') {
			if (reply.output.length > 0) {
				outputChannel.appendLine(reply.output);
			}
		}
		// Show error during execution
		else if (reply.status === 'error') {
			if (reply.output.length > 0) {
				outputChannel.appendLine(reply.output);
			}
			outputChannel.appendLine('--------------------------------------------------');
			outputChannel.appendLine(reply.traceback);
			outputChannel.appendLine('');
		}
		socket.destroy();
	})
	.on('close', () => {
		console.log('embedded-python-for-nvidia-omniverse: disconnected');
	}).on('error', (err) => {
		vscode.window.showErrorMessage('[Embedded Python for NVIDIA Omniverse] Connection error: ' + err.message);
		console.error('embedded-python-for-nvidia-omniverse: connection error: ' + err.message);
		socket.destroy();
	}).on('timeout', () => {
		console.log('embedded-python-for-nvidia-omniverse: timeout');
	}).on('drain', () => {
		console.log('embedded-python-for-nvidia-omniverse: drain');
	}).on('end', () => {
		console.log('embedded-python-for-nvidia-omniverse: end');
	});
}


// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	
	// This line of code will only be executed once when your extension is activated
	console.log('embedded-python-for-nvidia-omniverse: active');
	
	// Get OUTPUT pane
	let outputChannel = vscode.window.createOutputChannel('Embedded Python for NVIDIA Omniverse');  //, 'python');
	
	// Local execution
	let disposable_local = vscode.commands.registerCommand('embedded-python-for-nvidia-omniverse.run', () => {
		// Get extension configuration
		const config = vscode.workspace.getConfiguration();
		const socketPort = config.get('localSocket', {"extensionPort": 8226}).extensionPort;
		executeCode('127.0.0.1', socketPort, outputChannel);
	});

	// Remote execution
	let disposable_remote = vscode.commands.registerCommand('embedded-python-for-nvidia-omniverse.runRemotely', () => {
		// Get extension configuration
		const config = vscode.workspace.getConfiguration();
		const socketIp = config.get('remoteSocket', {"extensionIp": "127.0.0.1"}).extensionIp;
		const socketPort = config.get('remoteSocket', {"extensionPort": 8226}).extensionPort;
		executeCode(socketIp, socketPort, outputChannel);
	});

	context.subscriptions.push(disposable_local);
	context.subscriptions.push(disposable_remote);
}

// this method is called when your extension is deactivated
export function deactivate() {
	console.log('embedded-python-for-nvidia-omniverse: deactive');
	// Release OUTPUT pane
	vscode.window.createOutputChannel('Embedded Python for NVIDIA Omniverse').dispose();
}
