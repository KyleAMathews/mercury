# vim: tabstop=4 shiftwidth=4 softtabstop=4
from fabric.api import *
import os

import pantheon
import update

def configure(vps="none"):
    '''configure the Pantheon system.'''
    server = pantheon.PantheonServer()
    _test_for_previous_run()
    _configure_server(server)
    if (vps == "aws"):
        _config_ec2_(server)
    _configure_apache(server)
    _configure_postfix(server)
    _restart_services(server)
    _configure_databases()
    _configure_iptables(server)
    _mark_incep(server)
    _report()

def _test_for_previous_run():
    if os.path.exists("/etc/pantheon/incep"):
        abort("Pantheon config has already run. Exiting.")

def _configure_server(server):
    server.update_packages()
    update.update_pressflow()
    update.update_pantheon()
    local('cp /etc/pantheon/templates/tuneables /etc/pantheon/server_tuneables')
    local('chmod 755 /etc/pantheon/server_tuneables')

def  _configure_ec2(server):
    local('chmod 1777 /tmp')
    if(server.distro == 'centos'):
        local('mv /var/log/mysqld.log /mnt/mysql/')
        local('ln -s /mnt/mysql/mysqld.log /var/log/mysqld.log')
    else:
        local('mv /var/log/mysql /mnt/mysql/log')
        local('ln -s /mnt/mysql/log /var/log/mysql')
    local('mv /var/lib/mysql /mnt/mysql/lib')
    local('ln -s /mnt/mysql/lib /var/lib/mysql')
    local('/etc/init.d/varnish stop')
    local('mv /var/lib/varnish /mnt/varnish/lib')
    local('ln -s /mnt/varnish/lib /var/lib/varnish')
    local('chown varnish:varnish /mnt/varnish/lib/pressflow/')

def _configure_apache(server):
    if(server.distro == 'centos'):
        local('cp /etc/pantheon/templates/vhost/* /etc/httpd/conf/vhosts/')
    else:
        local('cp /etc/pantheon/templates/vhost/* /etc/apache2/sites-available/')
        local('ln -sf /etc/apache2/sites-available/pantheon_live /etc/apache2/sites-available/default')
        local('a2ensite pantheon_dev')
        local('a2ensite pantheon_test')

def _configure_postfix(server):
    f = open('/etc/mailname', 'w')
    f.write(server.hostname)
    f.close()
    local('/usr/sbin/postconf -e "myhostname = %s"' % server.hostname)
    local('/usr/sbin/postconf -e "mydomain = %s"' % server.hostname)
    local('/usr/sbin/postconf -e "mydestination = %s"' % server.hostname)
    local('/etc/init.d/postfix restart')

def _restart_services(server):
     server.restart_services()

def _configure_databases():
    #TODO: allow for mysql already having a password
    local("mysql -u root -e 'CREATE DATABASE IF NOT EXISTS pantheon_dev'")
    local("mysql -u root -e 'CREATE DATABASE IF NOT EXISTS pantheon_test;'")
    local("mysql -u root -e 'CREATE DATABASE IF NOT EXISTS pantheon_live;'")

def _configure_iptables(server):
    local('sed -i "s/#-A/-A/g" /etc/pantheon/templates/iptables')
    server.setup_iptables()

def _mark_incep(server):
    '''Mark incep date. This prevents us from ever running again.'''
    f = open('/etc/pantheon/incep', 'w')
    f.write(server.hostname)
    f.close()

def _report():
    '''Phone home - helps us to know how many users there are without passing any identifying or personal information to us.'''
    id = local('hostname -f | md5sum | sed "s/[^a-zA-Z0-9]//g"').rstrip('\n')
    local('curl "http://getpantheon.com/pantheon.php?id="' + id + '"&product=pantheon"')
    
    print('##############################')
    print('#   Pantheon Setup Complete! #')
    print('##############################')

    local('echo "DEAR SYSADMIN: PANTHEON IS READY FOR YOU NOW.  Do not forget the README.txt, CHANGELOG.txt and docs!" | wall')