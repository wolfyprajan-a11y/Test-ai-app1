[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2

# Cleaned requirements: hostpython3 and openssl removed to prevent recipe conflicts
requirements = python3, kivy, requests, urllib3, certifi

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33

android.ndk = 25b

# Lock Buildozer to the stable 2024 compiler branch to prevent the Python 3.14 bleeding-edge crash!
p4a.branch = v2024.1.21

[buildozer]
log_level = 2
warn_on_root = 1
