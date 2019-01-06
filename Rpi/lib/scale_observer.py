from collections import deque


# ScaleObserver is used to monitor changes in the weighing scale used, and trigger callbacks that are bound to it
class ScaleObserver:

    def __init__(self, threshold_weight=800, tolerance=3, history_size=5, stability_deviation=100):

        # person_on_scale, scale_dismount
        self._person_on_scale = False
        self._tolerance = tolerance
        self._threshold_weight = threshold_weight
        self._threshold_state = (0, tolerance)
        self._scale_dismount_callbacks = {}

        # scale_mount
        self._scale_mount_callbacks = {}

        # is_stable
        self._stability_deviation = stability_deviation
        self._history_size = history_size
        self._is_stable = False
        self._weight_history = deque()
        self._successful_weighing_callbacks = {}

        self.total_weight = -1
        self.tag_data = None
        self.nfc_present = False

    @property
    def is_stable(self):
        return self._is_stable

    @is_stable.setter
    def is_stable(self, value):

        # A person on the scale has successfully taken his weight
        if self.person_on_scale and (self.nfc_present is True) and (value is True):
            self._exec_successful_weighing_callbacks()

        self._is_stable = value

    @property
    def person_on_scale(self):
        return self._person_on_scale

    @person_on_scale.setter
    def person_on_scale(self, value):
        """
        On setting the value of the person_on_scale attribute, if a dismount is detected, callbacks will be called.
        :param value: boolean
        :return: void
        """
        # if person has dismounted
        if value is False and self._person_on_scale is True:
            self._exec_on_scale_dismount_callbacks()

        # if person has mounted
        if value is True and self._person_on_scale is False:
            self._exec_on_scale_mount_callbacks()

        self._person_on_scale = value

    @property
    def total_weight(self):
        return self._weight

    @total_weight.setter
    def total_weight(self, value):
        """
        Every time a weight is updated, it will check to determine if a person is one scale
        :param value: float
        :return: void
        """

        def threshold_change(other_state):
            state, tolerance_value = self._threshold_state
            if state == other_state:
                tolerance_value -= 1
                self._threshold_state = (other_state, tolerance_value)
            else:
                tolerance_value = self._tolerance - 1
                self._threshold_state = (other_state, tolerance_value)

            return tolerance_value <= 0

        def add_to_history(weight):
            def check_if_stable(history):
                from functools import reduce
                if history is None or len(history) is 0:
                    return False
                mean = reduce(lambda x, y: x + y, history, 0) / len(history)
                return len([w for w in history if abs(w - mean) > self._stability_deviation]) == 0

            self._weight_history.append(weight)

            if len(self._weight_history) < self._history_size:
                return False  # not enough readings in history

            while len(self._weight_history) > self._history_size:
                self._weight_history.popleft()

            return check_if_stable(self._weight_history)

        # Checks to see if a person is on the scale
        if value > self._threshold_weight:
            if threshold_change(0):
                self.person_on_scale = True
        elif threshold_change(1):
            self.person_on_scale = False

        # Checks to see if weight readings are stable
        if add_to_history(value):
            self.is_stable = True
        else:
            self.is_stable = False

        self._weight = value

    def on_scale_mount(self, callback, lifetime=-1):
        """
        Binds callbacks the dismounting event
        Lifetime determines the maximum number of times the callback would be triggered by the event.
        Lifetime of -1 means the callback would always be triggered.
        :param callback: lambda: void
        :param lifetime: int
        :return: void
        """
        self._bind_to_trigger(callback, self._scale_mount_callbacks, lifetime)

    def on_scale_dismount(self, callback, lifetime=-1):
        """
        Binds callbacks the dismounting event
        Lifetime determines the maximum number of times the callback would be triggered by the event.
        Lifetime of -1 means the callback would always be triggered.
        :param callback: lambda: void
        :param lifetime: int
        :return: void
        """
        self._bind_to_trigger(callback, self._scale_dismount_callbacks, lifetime)

    def on_successful_weighing(self, callback, lifetime=-1):
        """
        Binds callbacks the successful weighing event.
        Lifetime determines the maximum number of times the callback would be triggered by the event.
        Lifetime of -1 means the callback would always be triggered.
        :param callback: lambda: void
        :param lifetime: int
        :return: void
        """
        self._bind_to_trigger(callback, self._successful_weighing_callbacks, lifetime)

    def _bind_to_trigger(self, callback, callbacks_dict, lifetime):
        callbacks_dict[callback] = lifetime  # OVERWRITES previous callback if any

    def _exec_successful_weighing_callbacks(self):
        callbacks = self._successful_weighing_callbacks
        wheelchair_weight = 0 if self.tag_data is None else self.tag_data.wheelchair_weight
        for callback, lifetime in callbacks.copy().items():
            if lifetime is -1:
                callback(self.total_weight)
            elif lifetime > 0:
                callbacks[callback] -= 1
                callback(self.total_weight, wheelchair_weight)
            else:  # lazy deletion, callbacks with lifetime of zero are expired
                del callbacks[callback]

    def _exec_on_scale_dismount_callbacks(self):
        for callback, lifetime in self._scale_dismount_callbacks.copy().items():
            if lifetime is -1:
                callback()
            elif lifetime > 0:
                self._scale_dismount_callbacks[callback] -= 1
                callback()
            else:  # lazy deletion, callbacks with lifetime of zero are expired
                del self._scale_dismount_callbacks[callback]

    def _exec_on_scale_mount_callbacks(self):
        for callback, lifetime in self._scale_mount_callbacks.copy().items():
            if lifetime is -1:
                callback()
            elif lifetime > 0:
                self._scale_mount_callbacks[callback] -= 1
                callback()
            else:  # lazy deletion, callbacks with lifetime of zero are expired
                del self._scale_mount_callbacks[callback]

    def update(self, total_weight, tag_data, nfc_present):
        self.nfc_present = nfc_present
        self.tag_data = tag_data
        self.total_weight = total_weight
        print("Weight:{} Nfc_present:{} is_stable:{} person_on_scale:{}".format(
            self.total_weight,
            self.nfc_present,
            self.is_stable,
            self.person_on_scale))
