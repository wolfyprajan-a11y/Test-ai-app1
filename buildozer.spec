[app]

# (str) Title of your application
title = AI Coding Assistant

# (str) Package name
package.name = aicoding

# (str) Package domain (needed for android packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include 
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning 
version = 1.0

# (list) Application requirements
requirements = python3,kivy

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature
android.allow_backup = True

#
# Python for android (p4a) specific
#

# (str) python-for-android branch to use, pulling the latest fixes
p4a.branch = master


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
