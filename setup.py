from setuptools import setup, find_packages
import os

APP = ['main.py']
DATA_FILES = [
    ('src', ['src/app.py', 'src/antivirus_engine.py', 'src/webhook_server.py', 'src/database.py']),
    ('data', ['data/users.db']),
    ('resources', ['resources/icon.ico'])
]

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'resources/icon.ico',
    'packages': find_packages(),
    'includes': ['streamlit', 'flask', 'stripe', 'Crypto', 'psutil', 'pandas', 'numpy'],
    'excludes': ['tkinter'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)