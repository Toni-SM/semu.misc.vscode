import * as vscode from 'vscode';
import * as net from 'net';



// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	
	// This line of code will only be executed once when your extension is activated
	console.log('embedded-python-for-nvidia-omniverse: active');
	
	// Get OUTPUT pane
	let outputChannel = vscode.window.createOutputChannel('Embedded Python for NVIDIA Omniverse');  //, 'python');
	
	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	let disposable = vscode.commands.registerCommand('embedded-python-for-nvidia-omniverse.run', () => {
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
		console.log(config.toString());
		const socketIp = config.get('socket', {"extensionIp": "127.0.0.1"}).extensionIp;
		const socketPort = config.get('socket', {"extensionPort": 8226}).extensionPort;
		const clearAfterRun = config.get('output', {"clearBeforeRun": true}).clearBeforeRun;

		// Create TCP socket client
		let socket: net.Socket = new net.Socket();
		
		// Connect to server, send text, and show output
		socket.connect(socketPort, socketIp, () => {
			// Clear output if needed
			if (clearAfterRun) {
				outputChannel.clear();
			}
			outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] executing...`);
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
	});

	context.subscriptions.push(disposable);
}

// this method is called when your extension is deactivated
export function deactivate() {
	console.log('embedded-python-for-nvidia-omniverse: deactive');
	// Release OUTPUT pane
	vscode.window.createOutputChannel('Embedded Python for NVIDIA Omniverse').dispose();
}
