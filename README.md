# AI Shell

A mobile Python coding environment built with Kivy and packaged with Buildozer.

## Features
* **Safe Code Execution**: Executes Python logic within a restricted namespace.
* **Mobile-Optimized UI**: Utilizes ScrollViews for responsive rendering on Android devices.
* **Isolated Data Storage**: Safely manages state within the `~/.aishell` directory.

## Build Instructions
This project uses a configured GitHub Actions workflow to automatically compile an Android APK via Buildozer.
1. Push your code to the `main` branch.
2. The `Build Android APK` action will run automatically.
3. Upon success, download the generated `AI-Shell-App` artifact from the Actions tab.

## Troubleshooting
If the build process fails or times out:
* Review the uploaded `build-log` artifact for specific Buildozer compilation issues.
* Ensure no conflicting dependencies are re-introduced in `buildozer.spec` (e.g., maintain Kivy at `2.1.0` and Cython at `0.29.36`).

## API Key Management
To integrate external AI services, place your keys inside `~/.aishell/config.json`. Do not hardcode secrets directly into `main.py`.
