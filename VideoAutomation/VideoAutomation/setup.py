from setuptools import setup

APP = ['video_app.py']
DATA_FILES = ['automate_videos.py', 'process_timeline.py']
OPTIONS = {
    'argv_emulation': False,
    'packages': ['PyQt5'],
    'iconfile': None,
    'plist': {
        'CFBundleName': 'Creators Video Automation',
        'CFBundleDisplayName': 'Creators Video Automation',
        'CFBundleIdentifier': 'com.creators.videoautomation',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)