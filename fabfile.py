from fabric.api import *
from fabric.context_managers import cd
from fabric.operations import local as lrun, sudo
from fabric.contrib.files import sed
from fabric.utils import warn
from local_fabfile import root, prod, lh, SERVER_IP


def virtualenv(command, run_directory=''):
  if run_directory == '':
    run_directory = env.directory
  with cd(run_directory):
    sudo(env.activate + '&&' + command, user=env.user)


def apt_get(*packages):
  sudo('apt-get -y --no-upgrade install %s' % ' '.join(packages), shell=False)


def create_privileged_group():
  run('/usr/sbin/groupadd ' + env.user_group)
  run('mv /etc/sudoers /etc/sudoers-backup')
  run('(cat /etc/sudoers-backup ; echo "%' + env.user_group + \
    ' ALL=(ALL) ALL") > /etc/sudoers')
  run('chmod 440 /etc/sudoers')


def create_privileged_user():
  run('/usr/sbin/adduser ' + env.non_root_user)
  run('/usr/sbin/usermod -a -G ' + env.user_group + ' ' + env.non_root_user)
  run('mkdir /home/%s/.ssh' % env.non_root_user)
  run('chown -R %s /home/%s/.ssh' % (env.non_root_user, env.non_root_user))
  run('chgrp -R %s /home/%s/.ssh' % (env.user_group, env.non_root_user))


def install_pip():
  """
    Install pip system-wide. Must be run as root.
  """
  run('easy_install -U pip')
  run('pip install --upgrade pip')
  run('pip install -U virtualenv')


def rebuild_db():
  run('mysql -u %s -p%s -e "drop database if exists %s"' % (env.db_user, 
    env.db_passwd, env.db_schema))
  run('mysql -u %s -p%s -e "create database %s"' % (env.db_user,
    env.db_passwd, env.db_schema))
  virtualenv('python %smanage.py syncdb --noinput' % \
    env.deploy_dir)
  virtualenv('python %smanage.py loaddata %s/core/fixtures/test.json' % \
    (env.deploy_dir, env.deploy_dir))

def dumpdata(filename):
  proj_dir = env.directory + env.project_name
  virtualenv('python ' + proj_dir + \
    '/manage.py dumpdata auth.User auth.Group ' + env.dumpmodels + \
    ' ' + proj_dir + '/core/fixtures/' + filename)
    

def upload_keys(username):
  local('scp ~/.ssh/id_rsa ~/.ssh/id_rsa.pub ~/.ssh/authorized_keys2 ' + \
    username + '@' + SERVER_IP + ':~/.ssh')


def clone_repo():
  with cd(env.directory):
    run('git clone %s %s' % (env.git_repo, env.project_name))
    run('chown -R %s %s' % (env.non_root_user, env.project_name))
    run('chgrp -R %s %s' % (env.user_group, env.project_name))


def modify_firewall_rules():
  run('/sbin/iptables -F')
  run('cp /home/%s/%s/deploy/firewall/iptables.up.rules /etc/' % \
    (env.non_root_user, env.project_name))
  run('cp /home/%s/%s/deploy/firewall/iptables /etc/network/if-pre-up.d/' % \
    (env.non_root_user, env.project_name))
  run('chmod +x /etc/network/if-pre-up.d/iptables')
  sed('/etc/ssh/sshd_config', '^Port 22', 'Port 8313')
  # prevent root logins now that automated set up is complete
  sed('/etc/ssh/sshd_config', '^PermitRootLogin yes', 'PermitRootLogin no')
  run('/sbin/iptables-restore < /etc/iptables.up.rules')
  run('service ssh restart')


def install_nginx():
  """
    Install nginx and copy in configuration files. Depends on project source
    code available in /home/[env.user]/[env.project_name]. Must be run as root.
  """
  run('mv /etc/apt/sources.list /etc/apt/sources.list.bak')
  run('(cat /etc/apt/sources.list.bak ; ' + \
    'cat /home/%s/%s/deploy/nginx/sources.list ) > /etc/apt/sources.list' % \
      (env.non_root_user, env.project_name))
  run('apt-get install nginx')
  run('cp /home/%s/%s/deploy/nginx/%s.conf /etc/nginx/conf.d/%s.conf' % \
    (env.non_root_user, env.project_name, env.project_name, env.project_name))
  run('rm /etc/nginx/sites-enabled/default')


def configure_supervisor():
  run('service supervisor stop')
  run('cp /home/%s/%s/deploy/supervisor/%s.conf /etc/supervisor/conf.d/' % \
    (env.non_root_user, env.project_name, env.project_name))
  run('service supervisor start')


def initial_root_setup():
  """
    Set up commands meant to be run as soon as a blank Ubuntu 10.04 machine
    is turned on.
  """
  run('mkdir ~/.ssh')
  upload_keys(env.root)
  sed('/etc/ssh/sshd_config', '^UsePAM yes', 'UsePAM no')
  sed('/etc/ssh/sshd_config', '^#PasswordAuthentication yes', 
    'PasswordAuthentication no')
  sed('/etc/ssh/sshd_config', '^HostbasedAuthentication no',
    'HostbasedAuthentication yes')
  # update and install packages
  run('apt-get update')
  run('apt-get install -y git-core build-essential pip python-dev vim ' + \
    'python-setuptools python-mysqldb libmysqlclient-dev supervisor')
  #run('apt-get -y --force-yes upgrade')
  # add group and user
  create_privileged_group()
  create_privileged_user()
  # upload ssh keys for non-root user
  upload_keys(env.non_root_user)
  run('service ssh reload')
  clone_repo()
  install_pip()
  install_nginx()
  configure_supervisor()
  run('mkdir -p /srv/www/%s/webapp/' % env.project_name)
  modify_firewall_rules()


def install_mysql():
  sudo('echo "mysql-server-5.0 mysql-server/root_password password ' \
    '%s" | debconf-set-selections' % env.db_root_passwd)
  sudo('echo "mysql-server-5.0 mysql-server/root_password_again password ' \
    '%s" | debconf-set-selections' % env.db_root_passwd)
  apt_get('mysql-server')


def mysql_create_user_and_schema():
  run(('mysql -u %s -p%s -e "create user \'%s\'@\'localhost\' ' + \
    'identified by \'%s\';"') % (env.db_root_user, env.db_root_passwd, 
    env.db_user, env.db_passwd))
  run('mysql -u %s -p%s -e "grant all on *.* to \'%s\'@\'localhost\';"' % \
    (env.db_root_user, env.db_root_passwd, env.db_user))
  run(('mysql -u %s -p%s -e "grant all privileges on *.* to ' + \
    '\'%s\'@\'localhost\';"') % (env.db_root_user, env.db_root_passwd,
    env.db_user))
  run('mysqladmin -u %s -p%s create %s' % (env.db_user, env.db_passwd, 
    env.db_schema))


def generate_ssl_cert():
  with cd(env.directory):
    sudo('openssl genrsa -des3 -out %s.key 4096' % env.project_name)
    sudo('openssl req -new -key %s -out %s' % \
      (env.project_name + '.key', env.project_name + '.csr'))
    sudo('openssl x509 -req -days 730 -in %s.csr -signkey %s.key ' + \
      '-out %s.crt' % (env.project_name, env.project_name, env.project_name))
    sudo('chmod 600 %s.*' % env.project_name)
    sudo('mkdir /etc/nginx/%s' % env.project_name)
    sudo('mv %s.* /etc/nginx/%s/' % (env.project_name, env.project_name))


def initial_prod_setup():
  """
    Set up script meant to be run once after initial_root_setup is finished.
    Must be prod user to set up properly.
  """
  install_mysql()
  mysql_create_user_and_schema()
  run('cp ~/%s/deploy/deploy.sh ~/deploy.sh' % env.project_name)
  run('cp ~/%s/deploy/vim/.vimrc ~/.vimrc' % env.project_name)
  run('mkdir ~/venvs')
  run('virtualenv --distribute ~/venvs/%s' % env.project_name)
  virtualenv('pip install -r ~/%s/requirements.txt' % env.project_name)
  #generate_ssl_cert()
  run('~/deploy.sh')
  virtualenv('python %smanage.py syncdb --noinput' % (env.deploy_dir))
  virtualenv('python %smanage.py loaddata %s' % (env.deploy_dir, 
    env.deploy_dir + 'core/fixtures/test.json'))


def deploy():
  run(env.directory + 'deploy.sh')

