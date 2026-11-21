[app]
title = تصفية العربيات
package.name = tasfiya
package.domain = org.tasfiya
source.dir = .
source.include_exts = py,png,jpg,ttf,json
source.exclude_dirs = .github,bin,.buildozer
version = 1.0
requirements = python3,kivy==2.3.0,arabic-reshaper==3.0.0,python-bidi==0.4.2,six
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.accept_sdk_license = True
android.permissions =

[buildozer]
log_level = 2
warn_on_root = 1
