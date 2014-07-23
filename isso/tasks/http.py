# -*- encoding: utf-8 -*-

from . import Task


class Fetch(Task):

    def __init__(self, db):
        self.db = db

    def run(self, data):
        raise NotImplemented
