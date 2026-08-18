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
# Pinning charset-normalizer, requests, urllib3, and certifi ensures wheel compatibility on Android
requirements = python3,kivy,requests==2.31.0,urllib3==2.1.0,certifi==2024.2.2,charset-normalizer==3.3.2

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
