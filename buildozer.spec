[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2

# Requirements for API rotation and networking
requirements = python3, kivy, requests, urllib3, certifi, openssl

orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33

# FORCE NDK 25b to prevent the NDK r28c build failure
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
