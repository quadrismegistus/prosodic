import os,sys
PATH_HERE = os.path.abspath(os.path.dirname(__file__))
PATH_REPO = os.path.dirname(PATH_HERE)
PATH_MTREE = os.path.join(PATH_REPO, 'metricaltree')
sys.path.append(PATH_MTREE)

# import tools
# from tools import *

# if 'configure_home_dir' in set(dir(tools)):
# 	tools.configure_home_dir(force=False)

# config=loadConfigPy(toprint=toprintconfig,dir_prosodic=dir_prosodic)

# import json
# os.environ['prosodic_config_json']=json.dumps(config)

# #default_dir_prosodic_home = os.path.abspath(os.path.expanduser('~/prosodic_data'))
# dir_prosodic_home = config.get('path_prosodic_data')
# dir_dicts = config.get('path_dicts', os.path.join(dir_prosodic, 'dicts'))
# dir_meters = config.get('path_meters', os.path.join(dir_prosodic_home, 'meters'))
# dir_results = config.get('path_results', os.path.join(dir_prosodic_home, 'results'))
# dir_tagged = config.get('path_tagged_samples', os.path.join(dir_prosodic_home, 'tagged_samples'))
# dir_corpus = config.get('path_corpora', os.path.join(dir_prosodic_home, 'corpora'))
# dir_nlp_data = config.get('path_nlp_data', os.path.join(dir_prosodic_home, 'nlp_libraries'))

# config['meters']=loadMeters(dir_meters,config)

# METER=config['meter']=config['meters'][config['meter']] if 'meter' in config and config['meter'] else None

# text=''
# cmd=''