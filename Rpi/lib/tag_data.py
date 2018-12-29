#!/usr/bin/env python3


class TagData:

    def __init__(self, wheelchair_weight, past_weights):
        """
        :param wheelchair_weight: float
        :param past_weights: [(datetime.date, float)]
        """
        self.wheelchair_weight = wheelchair_weight
        self.past_weights = past_weights

