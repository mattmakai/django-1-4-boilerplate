from fabric.api import *

SERVER_IP = '' # ex: '50.116.62.11'

def localhost():
  env.hosts = [''] # ex: matt@localhost
  env.db_user = '' # ex: sqladmin
  env.db_passwd = ''
  env.db_schema = '' # ex: appschema
  env.directory = '' # ex: /home/matt/devel/py/
  env.deploy_dir = '' # ex: /home/matt/devel/py/ec/
  env.activate = '' # ex: source /home/matt/devel/venvs/app/bin/activate


def root():
  env.hosts = [env.root + '@' + SERVER_IP]
  common()


def prod():
  common()
  env.hosts = [env.non_root_user + '@' + SERVER_IP + ':8313']
 

def common(): 
  env.root = 'root'
  env.non_root_user = '' # appuser
  env.user_group = '' # appusergroup
  env.password = ''
  env.directory = '' # ex: /home/app/
  env.project_name = '' # ex: app
  env.deploy_dir = '' # ex: /srv/www/app/webapp/
  env.db_root_user = 'root'
  env.db_root_passwd = ''
  env.db_user = '' # ex: sqladmin
  env.db_passwd = ''
  env.db_schema = '' # ex: appschema
  env.activate = '' # ex: source /home/app/venvs/app/bin/activate
  env.git_repo = '' # ex: 'git@github.com:makaimc/app.git'

