[app]
title = Gemini AI Shell
package.name = aishell
package.domain = org.balaji
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3==3.10.14,hostpython3==3.10.14,kivy==2.3.0,requests,certifi,urllib3,charset-normalizer,idna
orientation = all
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25b
android.private_storage = True
android.skip_update = False
android.accept_sdk_license = True
android.archs = arm64-v8a
android.allow_backup = True
android.release_artifact = apk
android.debug_artifact = apk
android.windowSoftInputMode = adjustResize

[buildozer]
log_level = 2
warn_on_root = 1
