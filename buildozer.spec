[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.2

# Upgrading Kivy to >=2.4.0 to resolve Python 3.14 C-API compilation crashes
requirements = python3,kivy>=2.4.0,requests==2.31.0,urllib3==2.1.0,certifi==2024.2.2,charset-normalizer==2.1.1,idna==3.7

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
