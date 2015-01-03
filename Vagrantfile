# -*- mode: ruby -*-
# vi: set ft=ruby :

# This is the Vagrant config file for setting up an environment for Isso development.
# It requires:
#
# * Vagrant (http://vagrantup.com)
# * A VM engine, like VirtualBox (http://virtualbox.org)
# * The Vagrant-Hostmanager plugin (https://github.com/smdahlen/vagrant-hostmanager)
#
# With them installed, cd into this directory and do 'vagrant up'. It's possible Vagrant will
# ask for your root password so it can update your /etc/hosts file. Once it's happily churning out
# console output, go get a coffee :)
#
# The resulting VM should be accessible at http://isso-dev.local/ so you can try the demo page out.
# Edit files in your checkout as usual. If you need to look at log files and stuff, 'vagrant ssh'
# to get into the VM. Useful info about it:
#
# * Running Ubuntu 14.04
# * Isso is running on uWSGI via port 8080
# * Actual webserver is Apache2, using mod_proxy_uwsgi to talk to uWSGI
# * uWSGI log file is /tmp/uwsgi.log
# * Isso DB file is /tmp/isso/comments.db
# * Isso log file is /tmp/isso/isso.log
#
# Enjoy!

$bootstrap = <<BOOTSTRAP
  apt-get update
  apt-get install -y apache2 curl build-essential python-setuptools python-dev sqlite3 git python-pip
  a2enmod proxy
  service apache2 restart

  curl -sL https://deb.nodesource.com/setup | bash -
  apt-get install -y nodejs

  npm install -g bower requirejs uglifyjs jade

  cd /vagrant
  python setup.py develop
  make init
  make js

  ln -s /vagrant/isso/demo /var/www/isso

  pip install uwsgi
  mkdir -p /tmp/isso/spool

  uwsgi --socket 127.0.0.1:8080 --master --processes 4 --cache2 name=hash,items=1024,blocksize=32 --spooler /tmp/isso/spool --module isso.run --env ISSO_SETTINGS=/vagrant/share/isso-dev.conf --daemonize /tmp/uwsgi.log --py-autoreload 1 
  chmod a+r /tmp/uwsgi.log
  
  apt-get install libapache2-mod-proxy-uwsgi

  cp /vagrant/share/isso-dev.local.apache-conf /etc/apache2/sites-available/isso-dev.local.conf
  a2ensite isso-dev.local
  a2dissite 000-default
  service apache2 restart

BOOTSTRAP

Vagrant.configure(2) do |config|

  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  config.vm.box = "ubuntu/trusty32"

  config.vm.hostname = 'isso-dev.local'
  config.vm.network "private_network", type: "dhcp"

  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.ignore_private_ip = false
  config.hostmanager.include_offline = true
  config.hostmanager.ip_resolver = proc do |machine|
    result = ""
    machine.communicate.execute("ifconfig eth1") do |type, data|
      result << data if type == :stdout
    end
    (ip = /inet addr:(\d+\.\d+\.\d+\.\d)/.match(result)) && ip[1]
  end

  config.vm.provision "shell", inline: $bootstrap

end
