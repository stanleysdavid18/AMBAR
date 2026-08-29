import unittest

from ambar.conversation.casual import CasualController


class _Clock:
    def __init__(self):
        self.value = 0

    def __call__(self):
        return self.value


class _Random:
    def uniform(self, _lower, _upper):
        return 0


class CasualControllerTests(unittest.TestCase):
    def setUp(self):
        self.clock = _Clock()
        self.controller = CasualController(
            {"sleep_seconds": 60, "cooldown_seconds": 300, "jitter_seconds": 0},
            clock=self.clock,
            random_source=_Random(),
        )

    def test_can_only_enable_in_normal_mode(self):
        self.assertFalse(self.controller.enable("study"))
        self.assertFalse(self.controller.enabled)
        self.assertTrue(self.controller.enable("normal"))
        self.assertTrue(self.controller.enabled)

    def test_disabling_cancels_pending_initiative(self):
        self.controller.enable("normal")
        self.controller.disable()
        self.clock.value = 100
        self.assertFalse(self.controller.begin_if_due("normal", sleeping=True, busy=False))

    def test_respects_idle_timeout_and_cooldown(self):
        self.controller.enable("normal")
        self.controller.on_sleep()
        self.clock.value = 59
        self.assertFalse(self.controller.begin_if_due("normal", sleeping=True, busy=False))
        self.clock.value = 60
        self.assertTrue(self.controller.begin_if_due("normal", sleeping=True, busy=False))
        self.controller.complete()
        self.assertFalse(self.controller.begin_if_due("normal", sleeping=True, busy=False))
        self.clock.value = 360
        self.assertTrue(self.controller.begin_if_due("normal", sleeping=True, busy=False))

    def test_user_activity_restarts_idle_countdown(self):
        self.controller.enable("normal")
        self.controller.on_sleep()
        self.clock.value = 30
        self.controller.record_activity()
        self.controller.on_sleep()
        self.clock.value = 60
        self.assertFalse(self.controller.begin_if_due("normal", sleeping=True, busy=False))
        self.clock.value = 90
        self.assertTrue(self.controller.begin_if_due("normal", sleeping=True, busy=False))

    def test_never_initiates_when_asleep_or_busy(self):
        self.controller.enable("normal")
        self.controller.on_sleep()
        self.clock.value = 60
        self.assertFalse(self.controller.begin_if_due("normal", sleeping=False, busy=False))
        self.assertFalse(self.controller.begin_if_due("normal", sleeping=True, busy=True))
        self.assertTrue(self.controller.begin_if_due("normal", sleeping=True, busy=False))
        self.assertFalse(self.controller.begin_if_due("normal", sleeping=True, busy=False))

    def test_mode_change_disables_casual_and_shutdown_is_safe(self):
        self.controller.enable("normal")
        for mode in ("study", "work", "gaming"):
            self.controller.on_mode_changed(mode)
            self.assertFalse(self.controller.enabled)
            self.controller.enable("normal")
        self.controller.shutdown()
        self.assertFalse(self.controller.enabled)
        self.assertFalse(self.controller.in_progress)

    def test_sleep_delay_can_be_configured_separately_from_normal_idle(self):
        controller = CasualController(
            {"sleep_seconds": 30, "cooldown_seconds": 300, "jitter_seconds": 0},
            clock=self.clock,
            random_source=_Random(),
        )
        controller.enable("normal")
        controller.on_sleep()
        self.clock.value = 29
        self.assertFalse(controller.begin_if_due("normal", sleeping=True, busy=False))
        self.clock.value = 30
        self.assertTrue(controller.begin_if_due("normal", sleeping=True, busy=False))
