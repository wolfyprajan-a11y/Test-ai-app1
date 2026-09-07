[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# Added certifi to map Android HTTPS SSL verification 
requirements = python3==3.10.14,hostpython3==3.10.14,kivy==2.3.0,requests,certifi

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Strictly 64-bit architecture
android.archs = arm64-v8a

android.allow_backup = True
android.accept_sdk_license = True
android.api = 33
android.minapi = 24
android.ndk = 25b
android.disable_telemetry = 1

[buildozer]
log_level = 2
warn_on_root = 1

p4a.branch = master
