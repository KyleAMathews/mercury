#!/bin/bash

# Move mysql and varnish to /mnt
# TODO support for EBS and RDS

# Mysql:
#service mysql stop hangs if the service isn't running...
if [[  `service mysql status | grep start` ]]; then
    service mysql stop
fi
mv /var/log/mysql /mnt/mysql/log
ln -s /mnt/mysql/log /var/log/mysql
mv /var/lib/mysql /mnt/mysql/lib
ln -s /mnt/mysql/lib /var/lib/mysql
service mysql start

# Varnish:
mv /var/lib/varnish /mnt/varnish/lib
ln -s /mnt/varnish/lib /var/lib/varnish
chown varnish:varnish /mnt/varnish/lib/pressflow/

# Unset ssh key gen:
chmod -x /etc/init.d/ec2-ssh-host-key-gen
