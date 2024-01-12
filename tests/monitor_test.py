# -*- coding: utf-8 -*-
"""
Unit tests for Monitor classes
"""

import unittest

from agentscope.utils import MonitorBase, QuotaExceededError, MonitorFactory

from agentscope.utils.monitor import DictMonitor


class MonitorFactoryTest(unittest.TestCase):
    "Test class for MonitorFactory"

    def test_get_monitor(self) -> None:
        """Test get monitor method of MonitorFactory."""
        monitor1 = MonitorFactory.get_monitor()
        monitor2 = MonitorFactory.get_monitor()
        self.assertEqual(monitor1, monitor2)
        self.assertTrue(
            monitor1.register("token_num", metric_unit="token", quota=200),
        )
        self.assertTrue(monitor2.exists("token_num"))
        self.assertTrue(monitor2.remove("token_num"))
        self.assertFalse(monitor1.exists("token_num"))


class MonitorTestBase(unittest.TestCase):
    """An abstract test class for MonitorBase interface"""

    def setUp(self) -> None:
        if self.__class__ is MonitorTestBase:
            raise unittest.SkipTest("Base test class")
        self.monitor = self.get_monitor_instance()

    def get_monitor_instance(self) -> MonitorBase:
        """Implement this method for your Monitorbase implementation."""
        raise NotImplementedError

    def test_register_exists_remove(self) -> None:
        """Test register and remove of monitor"""
        # register token_num
        self.assertTrue(
            self.monitor.register(
                "token_num",
                metric_unit="token",
                quota=1000,
            ),
        )
        # register an existing metric (ignore this operation and return false)
        self.assertFalse(
            self.monitor.register(
                "token_num",
                metric_unit="token",
                quota=2000,
            ),
        )
        # exists
        self.assertTrue(self.monitor.exists("token_num"))
        # not exists
        self.assertFalse(self.monitor.exists("communication"))
        # metric content
        metric = self.monitor.get_metric("token_num")
        self.assertIsNotNone(metric)
        self.assertEqual(metric["unit"], "token")  # type: ignore [index]
        self.assertEqual(metric["quota"], 1000)  # type: ignore [index]
        # remove a registered metric
        self.assertTrue(self.monitor.remove("token_num"))
        self.assertFalse(self.monitor.exists("token_num"))
        # remove an not existed metric
        self.assertFalse(self.monitor.remove("cost"))

    def test_add_clear_set_quota(self) -> None:
        """Test add and clear of monitor"""
        self.monitor.register("token_num", metric_unit="token", quota=100)
        # add to an existing metric
        self.assertTrue(self.monitor.add("token_num", 10))
        # add to a not existing metric
        self.assertFalse(self.monitor.add("communication", 20))
        # add and exceed quota
        self.assertRaises(
            QuotaExceededError,
            self.monitor.add,
            "token_num",
            91,
        )
        # set quota of not exists metric
        self.assertFalse(self.monitor.set_quota("communication", 200))
        # update quota
        self.assertTrue(self.monitor.set_quota("token_num", 200))
        # add success and check new value
        self.assertTrue(self.monitor.add("token_num", 10))
        self.assertEqual(self.monitor.get_value("token_num"), 111)
        # clear an existing metric
        self.assertTrue(self.monitor.clear("token_num"))
        # clear an not existing metric
        self.assertFalse(self.monitor.clear("communication"))
        self.assertTrue(self.monitor.remove("token_num"))

    def test_get(self) -> None:
        """Test get method of monitor"""
        self.assertTrue(
            self.monitor.register(
                "agentA.token_num",
                metric_unit="token",
                quota=200,
            ),
        )
        self.assertTrue(
            self.monitor.register(
                "agentB.token_num",
                metric_unit="token",
                quota=100,
            ),
        )
        self.assertTrue(
            self.monitor.register(
                "agentA.communication",
                metric_unit="KB",
                quota=500,
            ),
        )
        self.assertTrue(
            self.monitor.register(
                "agentB.communication",
                metric_unit="KB",
                quota=600,
            ),
        )
        self.assertTrue(
            self.monitor.register(
                "agentC.token_num",
                metric_unit="token",
                quota=600,
            ),
        )
        self.monitor.add("agentA.token_num", 10)
        self.assertEqual(self.monitor.get_value("agentA.token_num"), 10)
        self.assertEqual(self.monitor.get_unit("agentA.token_num"), "token")
        self.assertEqual(self.monitor.get_quota("agentA.token_num"), 200)
        self.assertIsNone(self.monitor.get_value("token_num"))
        self.assertIsNone(self.monitor.get_unit("token_num"))
        self.assertIsNone(self.monitor.get_quota("token_num"))
        self.assertIsNone(self.monitor.get_metric("token_num"))
        metric = self.monitor.get_metric("agentB.token_num")
        self.assertIsNotNone(metric)
        self.assertEqual(metric["value"], 0)  # type: ignore [index]
        self.assertEqual(metric["unit"], "token")  # type: ignore [index]
        self.assertEqual(metric["quota"], 100)  # type: ignore [index]
        self.assertEqual(self.monitor.get_metrics(r"cost"), {})
        agenta_metrics = self.monitor.get_metrics("agentA")
        self.assertEqual(len(agenta_metrics.keys()), 2)
        comm_metrics = self.monitor.get_metrics("communication")
        self.assertEqual(len(comm_metrics.keys()), 2)
        agentc_metrics = self.monitor.get_metrics("agentC")
        self.assertEqual(len(agentc_metrics.keys()), 1)
        self.assertEqual(
            agenta_metrics["agentA.token_num"],
            {"value": 10.0, "unit": "token", "quota": 200},
        )


class DictMonitorTest(MonitorTestBase):
    """Test class for DictMonitor"""

    def get_monitor_instance(self) -> MonitorBase:
        return DictMonitor()
