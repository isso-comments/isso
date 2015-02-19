# -*- mode: ruby -*-
# vi: set ft=ruby :

# This is the Vagrant config file for setting up an environment for Isso development.
# It requires:
#
# * Vagrant (https://vagrantup.com)
# * A VM engine, like VirtualBox (https://virtualbox.org)
# * The Vagrant-Hostmanager plugin (https://github.com/smdahlen/vagrant-hostmanager)
# * Ansible (https://www.ansible.com)
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
# * Isso is running on uWSGI
# * Actual webserver is Nginx to talk to uWSGI over a unix socket
# * uWSGI log file is /var/log/uwsgi/apps/isso.log
# * Isso DB file is /var/isso/comments.db
# * Isso log file is /var/log/isso.log
#
# When the VM is getting rebooted vagrant mounts the shared folder after uWSGI is getting startet. To fix this issue for
# the moment you need to 'vagrant ssh' into the VM and execute 'sudo service uwsgi restart'.
#
# For debugging with _pudb_ stop uWSGI service and start it manually
# 'sudo uwsgi --ini /etc/uwsgi/apps-available/isso.ini'.
#
# Enjoy!

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

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "ansible/site.yml"
    ansible.limit = "all"
    ansible.verbose = "v"
  end

  config.vm.post_up_message = "Browse to http://isso-dev.local/demo/index.html to start."
end
