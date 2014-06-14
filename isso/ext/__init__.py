# -*- encoding: utf-8 -*-

from collections import defaultdict


class Signal(object):

    def __init__(self, *subscriber):
        self.subscriptions = defaultdict(list)

        for sub in subscriber:
            for signal, func in sub:
                self.subscriptions[signal].append(func)

    def __call__(self, origin, *args, **kwargs):
        for subscriber in self.subscriptions[origin]:
            subscriber(*args, **kwargs)
