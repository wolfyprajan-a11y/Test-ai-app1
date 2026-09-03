[app]

# (str) Title of your application
title = AIShell

# (str) Package name
package.name = aishell

# (str) Package domain (needed for android/ios packaging)
package.domain = org.wolfyprajan

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning (method 1)
version = 0.2

# (list) Application requirements
# Downgrading Kivy to 2.2.1 resolves the Cython C-API compilation crash
requirements = python3,kivy==2.2.1,requests==2.31.0,urllib3==2.1.0,certifi==2024.2.2,charset-normalizer==2.1.1,idna==3.7

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (list) The Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Android allow backup
android.allow_backup = True

# (bool) Automatically accept SDK license
android.accept_sdk_license = True

# (int) Target Android API
android.api = 33

# (str) Android NDK version to use
android.ndk = 25b

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
