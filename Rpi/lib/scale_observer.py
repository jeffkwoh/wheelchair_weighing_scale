# ScaleObserver is used to monitor changes in the weighing scale used, and trigger callbacks that are bound to it
class ScaleObserver:

    def __init__(self, threshold_weight=2000, tolerance=3):
        self._person_on_scale = False
        self._tolerance = tolerance
        self._threshold_weight = threshold_weight
        self._threshold_state = (0, tolerance)
        self.weight = -1
        self._scale_dismount_callbacks = set()

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
            self._exec_scale_dismount_callbacks()

        self._person_on_scale = value

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, value):
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

        if value > self._threshold_weight:
            if threshold_change(0):
                self.person_on_scale = True
        elif threshold_change(1):
            self.person_on_scale = False

        self._weight = value

    def on_scale_dismount(self, callback):
        """
        Binds callbacks the dismounting event
        :param callback: lambda: void
        :return: void
        """
        self._scale_dismount_callbacks.add(callback)

    def _exec_scale_dismount_callbacks(self):
        for callback in self._scale_dismount_callbacks:
            callback()
