# -*- encoding: utf-8 -*-

import abc
import datetime


class Task(object):
    """A task. Override :func:`run` with custom functionality. Tasks itself
    may cause blocking I/O but should terminate.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def run(self, data):
        return


class Cron(Task):
    """Crons are tasks which are re-scheduled after each execution."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        self.timedelta = datetime.timedelta(*args, **kwargs)

    def run(self, data):
        return


from . import db, http, mail


class Jobs(dict):
    """Obviously a poor man's factory"""

    available = {
        "db-purge": db.Purge,
        "http-fetch": http.Fetch,
        "mail-send": mail.Send
    }

    def __init__(self):
        super(Jobs, self).__init__()

    def register(self, name, *args, **kwargs):
        if name in self:
            return

        try:
            cls = Jobs.available[name]
        except KeyError:
            raise RuntimeError("No such task '%s'" % name)

        self[name] = cls(*args, **kwargs)


__all__ = ["Job", "Cron", "Jobs"]
