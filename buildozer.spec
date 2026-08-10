[app]
title = AIShell
package.name = aishell
package.domain = org.wolfyprajan
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Lock the Android app to Python 3.11 to prevent the compiler crash!
requirements = python3==3.11.5,kivy

orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
