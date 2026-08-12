[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2

# Explicitly pin python3 to 3.11.5 to prevent the Python 3.14 bleeding-edge crash
requirements = python3==3.11.5, kivy, requests, urllib3, certifi, openssl

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33

# Force NDK 25b to prevent the r28c compatibility failure
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
