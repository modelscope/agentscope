# -*- coding: utf-8 -*-
""" Monitor for agentscope """

import re
import copy
from abc import ABC
from abc import abstractmethod
from typing import Optional, Any
from loguru import logger


class MonitorBase(ABC):
    r"""Base interface of Monitor"""

    @abstractmethod
    def register(
        self,
        metric_name: str,
        metric_unit: Optional[str] = None,
        quota: Optional[float] = None,
    ) -> bool:
        """Register a metric to the monitor with value initialized to 0.

        Args:
            metric_name (`str`):
                Name of the metric, must be unique.
            metric_unit (`Optional[str]`):
                Unit of the metric.
            quota (`Optional[str]`):
                The quota of the metric. An alert is triggered when metrics
                accumulate above this value.

        Returns:
            `bool`: whether the operation success.
        """

    @abstractmethod
    def exists(self, metric_name: str) -> bool:
        """Determine whether a metric exists in the monitor.

        Args:
            metric_name (`str`):
                Name of the metric.

        Returns:
            `bool`: Whether the metric exists.
        """

    @abstractmethod
    def add(self, metric_name: str, value: float) -> bool:
        """Add value to a specific metric.

        Args:
            metric_name (`str`):
                Name of the metric.
            value (`float`):
                Increased value.

        Returns:
            `bool`: whether the operation success.
        """

    def update(self, **kwargs: Any) -> None:
        """Update multiple metrics at once."""
        for k, v in kwargs.items():
            self.add(k, v)

    @abstractmethod
    def clear(self, metric_name: str) -> bool:
        """Clear the values of a specific metric.

        Args:
            metric_name (`str`):
                Name of the metric.

        Returns:
            `bool`: whether the operation success.
        """

    @abstractmethod
    def remove(self, metric_name: str) -> bool:
        """Remove a specific metric from the monitor.

        Args:
            metric_name (`str`):
                Name of the metric.

        Returns:
            `bool`: Whether the operation success.
        """

    @abstractmethod
    def get_value(self, metric_name: str) -> Optional[float]:
        """Get the value of a specific metric.

        Args:
            metric_name (`str`):
                Name of the metric.

        Returns:
            `Optional[float]`: the value of the metric.
        """

    @abstractmethod
    def get_unit(self, metric_name: str) -> Optional[str]:
        """Get the unit of a specific metric.

        Args:
            metric_name (`str`):
                Name of the metric.

        Returns:
            `Optional[str]`: The unit of the metric.
        """

    @abstractmethod
    def get_quota(self, metric_name: str) -> Optional[float]:
        """Get the quota of a specific metric.

        Args:
            metric_name (`str`):
                Name of the metric.

        Returns:
            `Optional[float]`: The quota of the metric.
        """

    @abstractmethod
    def set_quota(self, metric_name: str, quota: float) -> bool:
        """Set the quota of a specific metric

        Args:
            metric_name (`str`):
                Name of the metric.
            quota (`float`):
                New quota of the metric.

        Returns:
            `bool`: whether the operation success.
        """

    @abstractmethod
    def get_metric(self, metric_name: str) -> Optional[dict]:
        """Get the specific metric

        Args:
            metric_name (`str`):
                Name of the metric.

        Returns:
            `Optional[dict]`: A dictionary of metric with following format::

                {
                    metric_value: [float],
                    metric_unit: [str],
                    quota: [float]
                }
        """

    @abstractmethod
    def get_metrics(self, filter_regex: Optional[str] = None) -> dict:
        """Get a dictionary of metrics.

        Args:
            filter_regex (`Optional[str]`):
                Regular expression for filtering metric names, get all
                metrics if not provided.

        Returns:
            `dict`: a dictionary of metric with following format::

                {
                    metric_name_A: {
                        metric_value: [float],
                        metric_unit: [str],
                        quota: [float]
                    },
                    metric_name_B: {
                        ...
                    },
                    ...
                }
        """


class QuotaExceededError(Exception):
    """An Exception used to indicate that a certain metric exceeds quota"""

    def __init__(self, metric_name: str, quota: float) -> None:
        self.message = f"Metric [{metric_name}] exceed quota [{quota}]"
        super().__init__(self.message)


def return_false_if_not_exists(  # type: ignore [no-untyped-def]
    func,
):
    """A decorator used to check whether the attribute exists.
    It will return False directly without executing the function,
    if the metric does not exist.
    """

    def inner(
        monitor: MonitorBase,
        metric_name: str,
        *args: tuple,
        **kwargs: dict,
    ) -> bool:
        if not monitor.exists(metric_name):
            logger.warning(f"Metric [{metric_name}] not exists.")
            return False
        return func(monitor, metric_name, *args, **kwargs)

    return inner


def return_none_if_not_exists(  # type: ignore [no-untyped-def]
    func,
):
    """A decorator used to check whether the attribute exists.
    It will return None directly without executing the function,
    if the metric does not exist.
    """

    def inner(  # type: ignore [no-untyped-def]
        monitor: MonitorBase,
        metric_name: str,
        *args: tuple,
        **kwargs: dict,
    ):
        if not monitor.exists(metric_name):
            logger.warning(f"Metric [{metric_name}] not exists.")
            return None
        return func(monitor, metric_name, *args, **kwargs)

    return inner


class DictMonitor(MonitorBase):
    """MonitorBase implementation based on dictionary."""

    def __init__(self) -> None:
        self.metrics = {}

    def register(
        self,
        metric_name: str,
        metric_unit: Optional[str] = None,
        quota: Optional[float] = None,
    ) -> bool:
        if metric_name in self.metrics:
            logger.warning(f"Metric [{metric_name}] is already registered.")
            return False
        self.metrics[metric_name] = {
            "value": 0.0,
            "unit": metric_unit,
            "quota": quota,
        }
        logger.info(
            f"Register metric [{metric_name}] to Monitor with unit "
            f"[{metric_unit}] and quota [{quota}]",
        )
        return True

    @return_false_if_not_exists
    def add(self, metric_name: str, value: float) -> bool:
        self.metrics[metric_name]["value"] += value
        if (
            self.metrics[metric_name]["quota"] is not None
            and self.metrics[metric_name]["value"]
            > self.metrics[metric_name]["quota"]
        ):
            logger.warning(f"Metric [{metric_name}] quota exceeded.")
            raise QuotaExceededError(
                metric_name=metric_name,
                quota=self.metrics[metric_name]["quota"],
            )
        return True

    def exists(self, metric_name: str) -> bool:
        return metric_name in self.metrics

    @return_false_if_not_exists
    def clear(self, metric_name: str) -> bool:
        self.metrics[metric_name]["value"] = 0.0
        return True

    @return_false_if_not_exists
    def remove(self, metric_name: str) -> bool:
        self.metrics.pop(metric_name)
        logger.info(f"Remove metric [{metric_name}] from monitor.")
        return True

    @return_none_if_not_exists
    def get_value(self, metric_name: str) -> Optional[float]:
        if metric_name not in self.metrics:
            return None
        return self.metrics[metric_name]["value"]

    @return_none_if_not_exists
    def get_unit(self, metric_name: str) -> Optional[str]:
        if metric_name not in self.metrics:
            return None
        return self.metrics[metric_name]["unit"]

    @return_none_if_not_exists
    def get_quota(self, metric_name: str) -> Optional[float]:
        return self.metrics[metric_name]["quota"]

    @return_false_if_not_exists
    def set_quota(self, metric_name: str, quota: float) -> bool:
        self.metrics[metric_name]["quota"] = quota
        return True

    @return_none_if_not_exists
    def get_metric(self, metric_name: str) -> Optional[dict]:
        return copy.deepcopy(self.metrics[metric_name])

    def get_metrics(self, filter_regex: Optional[str] = None) -> dict:
        if filter_regex is None:
            return copy.deepcopy(self.metrics)
        else:
            pattern = re.compile(filter_regex)
            return {
                key: copy.deepcopy(value)
                for key, value in self.metrics.items()
                if pattern.search(key)
            }


class MonitorFactory:
    """Factory of Monitor.

    Get the singleton monitor using::

        from agentscope.utils import MonitorFactory
        monitor = MonitorFactory.get_monitor()

    """

    _instance = None

    @classmethod
    def get_monitor(cls, impl_type: Optional[str] = None) -> MonitorBase:
        """Get the monitor instance.

        Returns:
            `MonitorBase`: the monitor instance.
        """
        if cls._instance is None:
            # todo: init a specific monitor implementation by input args
            if impl_type is None or impl_type.lower() == "dict":
                cls._instance = DictMonitor()
            else:
                raise NotImplementedError(
                    "Monitor with type [{type}] is not implemented.",
                )
        return cls._instance
