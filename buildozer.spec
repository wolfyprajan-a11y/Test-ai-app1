[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2

# Downgraded Python to 3.10.14 to fix the Kivy 2.1.0 'struct _frame' compilation crash
requirements = python3==3.10.14,hostpython3==3.10.14,kivy==2.1.0,requests

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
