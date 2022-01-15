import os
import shutil
import configparser
import sys

def SourcePath(relative_path):
    if getattr(sys,'frozen', False): 
        basePath = sys._MEIPASS
    else:
        basePath = os.path.abspath(".")
    basePath = basePath.replace(os.sep, '/')
    return os.path.join(basePath, relative_path)
def repair():
    if os.path.exists('.config') == False: # test if config directory exists
        os.mkdir('.config')
    if os.path.exists('.config/config.ini') == False: #test if config file exists
        shutil.copy(SourcePath('res/defaults/config.ini'),'.config')
    config = configparser.ConfigParser() # use config file to validate theme file
    config.read('.config/config.ini')
    if os.path.exists('themes') == False:
        os.mkdir('themes')
    if os.path.exists(config['theme']['themefile']) == False: # if selected themefile does not exist
        shutil.copy(SourcePath('res/defaults/theme.json'),'themes')
        config['theme']['themefile'] = 'themes/theme.json' # set to a valid theme
        with open('.config/config.ini', 'w') as configfile:
            config.write(configfile)
            configfile.close()
    if os.path.exists('screenshots') == False:
        os.mkdir('screenshots')
    if os.path.exists('nets') == False:
        os.mkdir('nets')