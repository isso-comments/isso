#!/usr/bin/env python
import os
import shutil

env = os.environ.get

smtp_settings = [
    ('username', ''),
    ('password', ''),
    ('host', 'localhost'),
    ('port', '25'),
    ('security', 'none'),
    ('to', ''),
    ('from', ''),
]

required = ['to', 'from']

settings = env('ISSO_SETTINGS')
if not settings:
    raise Exception('No ISSO_SETTINGS defined')

settings = settings.split(';')


def backup_name(setting):
    return setting + '.bak'


def purge_backup(setting):
    # if there is a backup file, delete it
    backup_setting = backup_name(setting)
    if os.path.exists(backup_setting):
        try:
            os.remove(backup_setting)
        except OSError:
            pass


def create_backup(setting):
    # make a backup
    shutil.copyfile(setting, backup_name(setting))


def load_values():
    values = []
    for name, default in smtp_settings:
        label = 'ISSO_SMTP_%s' % name.upper()
        value = env(label, default)
        if name in required and not value.strip():
            raise Exception('Required environment variable is not set: %s' %
                            label)
        values.append([label, value])
    return values


def replace_placeholders(setting, values):
    with open(setting, 'r') as _file:
        content = _file.read()

    for label, value in values:
        content = content.replace(label, value)

    # make a backup
    create_backup(setting)

    with open(setting, 'w') as _file:
        _file.write(content)

    return content


def main():
    values = load_values()

    for setting in settings:
        print("Replacing settings %s" % setting)
        replace_placeholders(setting, values)


if __name__ == '__main__':
    main()
