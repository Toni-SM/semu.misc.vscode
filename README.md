# Embedded VS Code for NVIDIA Omniverse

This extension is the pair of the [*Embedded VS Code for NVIDIA Omniverse*](https://github.com/Toni-SM/semu.misc.vscode) extension for NVIDIA Omniverse applications that can be described as the [VS Code](https://code.visualstudio.com/) version of Omniverse's [Script Editor](https://docs.omniverse.nvidia.com/prod_extensions/prod_extensions/ext_script-editor.html). It allows to execute python code, embedded in a local/remote NVIDIA Omniverse application scope, from the VS Code editor and display the results in the OUTPUT panel (under *Embedded VS Code for NVIDIA Omniverse*) of the VS Code editor.

<br>

![preview](https://github.com/Toni-SM/embedded-vscode-for-nvidia-omniverse/raw/main/images/preview.png)

## Overview

<br>

![preview1](https://github.com/Toni-SM/embedded-vscode-for-nvidia-omniverse/raw/main/images/preview1.png)

## Available commands

* **Embedded VS Code for NVIDIA Omniverse: Run** - Execute the python code from the active editor in the local configured NVIDIA Omniverse application and display the results in the OUTPUT panel

* **Embedded VS Code for NVIDIA Omniverse: Run Remotely** - Execute the python code from the active editor in the remote configured NVIDIA Omniverse application and display the results in the OUTPUT panel

## Extension Settings

This extension contributes the following settings:

* `remoteSocket.extensionIp`: IP address where the remote Omniverse application is running (default: `"127.0.0.1"`)
* `remoteSocket.extensionPort`: Port used by the *Embedded VS Code for NVIDIA Omniverse* extension in the remote Omniverse application (default: `8226`)
* `localSocket.extensionPort`: Port used by the *Embedded VS Code for NVIDIA Omniverse* extension in the local Omniverse application (default: `8226`)
* `output.clearBeforeRun`: Whether to clear the output before run the code. If unchecked (default value), the output will be appended to the existing content"

## Limitations

- Printing, inside callbacks (such as events), is not displayed in the VS Code OUTPUT panel but in the Omniverse application terminal

## Release Notes

### 0.0.1

- Initial release
