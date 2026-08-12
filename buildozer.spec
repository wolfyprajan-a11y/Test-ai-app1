[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2

# We strictly pin BOTH python3 and hostpython3 to bypass the 3.14 bleeding-edge crash and sync the compilers.
requirements = python3==3.11.5, hostpython3==3.11.5, kivy, requests, urllib3, certifi, openssl

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33

android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
