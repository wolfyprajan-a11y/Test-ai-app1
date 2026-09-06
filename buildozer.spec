[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# Pinned to 3.12.3 to naturally bypass Unix C-library compilation bugs
requirements = python3==3.12.3,hostpython3==3.12.3,kivy==2.3.0,requests

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# CRITICAL FIX: Target 64-bit ONLY. Bypasses the 32-bit 'grp' crash and cuts build time in half.
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
