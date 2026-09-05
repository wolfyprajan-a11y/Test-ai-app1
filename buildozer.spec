[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.3

# Lock Python to 3.11.9 to prevent the system from downloading Python 3.14 and crashing Kivy
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,requests

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33
android.minapi = 24
android.ndk = 25b
android.disable_telemetry = 1

[buildozer]
log_level = 2
warn_on_root = 1

# Force the environment to use the patched master branch to prevent pip crashes
p4a.branch = master
