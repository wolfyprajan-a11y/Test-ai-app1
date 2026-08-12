[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2

# Cleaned requirements as recommended: removed hostpython3 and openssl
requirements = python3,kivy,requests,urllib3,certifi

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33

# Keeping NDK pinned to 25b for stability
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 1
