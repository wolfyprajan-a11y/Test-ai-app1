[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# Reverted to 3.10.14: safely skips the missing 'grp' module without halting the build
requirements = python3==3.10.14,hostpython3==3.10.14,kivy==2.3.0,requests

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# 64-bit only to keep builds fast and stable
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

# Forces the build environment to use the patched master branch
p4a.branch = master
