# -*- coding: utf-8 -*-
""" Monitor for agentscope """

import re
import copy
import sqlite3
from abc import ABC
from abc import abstractmethod
from contextlib import contextmanager
from typing import Optional, Any, Generator
from loguru import logger

from agentscope.constants import _DEFAULT_MONITOR_TABLE_NAME


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

    def update(self, values: dict, prefix: Optional[str] = None) -> None:
        """Update multiple metrics at once."""
        for k, v in values:
            self.add(full_name(prefix=prefix, name=k), v)

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

    @abstractmethod
    def register_budget(
        self,
        model_name: str,
        value: float,
        prefix: Optional[str] = "local",
    ) -> bool:
        """Register model call budget to the monitor, the monitor will raise
        QuotaExceededError, when budget is exceeded.

        Args:
            model_name (`str`): model that requires budget.
            value (`float`): the budget value.
            prefix (`Optional[str]`, default `None`): used to distinguish
            multiple budget registrations. For multiple registrations with
            the same `prefix`, only the first time will take effect.

        Returns:
            `bool`: whether the operation success.
        """


def full_name(name: str, prefix: Optional[str] = None) -> str:
    """get the full name of a metric.

    Args:
        metric_name (`str`): name of a metric.
        prefix (` Optional[str]`, default `None`): metric prefix.

    Returns:
        `str`: the full name of the metric
    """
    if prefix is None:
        return name
    else:
        return f"{prefix}.{name}"


class QuotaExceededError(Exception):
    """An Exception used to indicate that a certain metric exceeds quota"""

    def __init__(
        self,
        metric_name: Optional[str] = None,
        quota: Optional[float] = None,
    ) -> None:
        if metric_name is not None and quota is not None:
            self.message = f"Metric [{metric_name}] exceeds quota [{quota}]"
            super().__init__(self.message)
        else:
            super().__init__()


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
        if (
            self.metrics[metric_name]["quota"] is not None
            and self.metrics[metric_name]["value"] + value
            > self.metrics[metric_name]["quota"]
        ):
            logger.warning(f"Metric [{metric_name}] quota exceeded.")
            raise QuotaExceededError(
                metric_name=metric_name,
                quota=self.metrics[metric_name]["quota"],
            )
        self.metrics[metric_name]["value"] += value
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

    def register_budget(
        self,
        model_name: str,
        value: float,
        prefix: Optional[str] = "local",
    ) -> bool:
        logger.warning("DictMonitor doesn't support register_budget")
        return False


@contextmanager
def sqlite_transaction(db_path: str) -> Generator:
    """Get a sqlite transaction cursor.

    Args:
        db_path (`str`): path to the sqlite db file

    Yields:
        `Generator`: a cursor with transaction
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN")
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


@contextmanager
def sqlite_cursor(db_path: str) -> Generator:
    """Get a sqlite cursor.

    Args:
        db_path (`str`): path to the sqlite db file

    Yields:
        `Generator`: a cursor
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        conn.close()


class SqliteMonitor(MonitorBase):
    """A monitor based on sqlite"""

    def __init__(
        self,
        db_path: str,
        table_name: str = _DEFAULT_MONITOR_TABLE_NAME,
        drop_exists: bool = False,
    ) -> None:
        super().__init__()
        self.db_path = db_path
        self.table_name = table_name
        self._create_monitor_table(drop_exists)

    def _create_monitor_table(self, drop_exists: bool = False) -> None:
        """Internal method to create a table in sqlite3."""
        with sqlite_transaction(self.db_path) as cursor:
            if drop_exists:
                cursor.execute(f"DROP TABLE IF EXISTS {self.table_name};")
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    value REAL NOT NULL,
                    quota REAL,
                    unit TEXT
                );""",
            )
            cursor.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS {self.table_name}_quota_exceeded
                BEFORE UPDATE ON {self.table_name}
                FOR EACH ROW
                WHEN OLD.quota is not NULL AND NEW.value > OLD.quota
                BEGIN
                    SELECT RAISE(FAIL, 'QuotaExceeded');
                END;
                """,
            )

    def _get_trigger_name(self, metric_name: str) -> str:
        """Get the name of the trigger on a certain metric"""
        return f"{self.table_name}.{metric_name}.trigger"

    def register(
        self,
        metric_name: str,
        metric_unit: Optional[str] = None,
        quota: Optional[float] = None,
    ) -> bool:
        with sqlite_transaction(self.db_path) as cursor:
            if self._exists(cursor, metric_name):
                return False
            cursor.execute(
                f"""
                INSERT INTO {self.table_name} (name, value, quota, unit)
                VALUES (?, ?, ?, ?)
                """,
                (metric_name, 0.0, quota, metric_unit),
            )
            logger.info(
                f"Register metric [{metric_name}] to SqliteMonitor with unit "
                f"[{metric_unit}] and quota [{quota}]",
            )
            return True

    def _add(
        self,
        cursor: sqlite3.Cursor,
        metric_name: str,
        value: float,
    ) -> None:
        try:
            cursor.execute(
                f"""
                    UPDATE {self.table_name}
                    SET value = value + ?
                    WHERE name = ?
                """,
                (value, metric_name),
            )
        except sqlite3.IntegrityError as e:
            raise QuotaExceededError() from e

    def add(self, metric_name: str, value: float) -> bool:
        with sqlite_transaction(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return False
            self._add(cursor, metric_name, value)
            return True

    def clear(self, metric_name: str) -> bool:
        with sqlite_transaction(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return False
            cursor.execute(
                f"""
                UPDATE {self.table_name}
                SET value = value + ?
                WHERE name = ?
            """,
                (0.0, metric_name),
            )
            return True

    def remove(self, metric_name: str) -> bool:
        with sqlite_transaction(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return False
            cursor.execute(
                f"""
                DELETE FROM {self.table_name}
                WHERE name = ?""",
                (metric_name,),
            )
        return True

    def _get_metric(self, cursor: sqlite3.Cursor, metric_name: str) -> dict:
        cursor.execute(
            f"""
            SELECT value, quota, unit FROM {self.table_name}
            WHERE name = ?""",
            (metric_name,),
        )
        row = cursor.fetchone()
        if row:
            value, quota, unit = row
            return {
                "value": value,
                "quota": quota,
                "unit": unit,
            }
        else:
            raise RuntimeError(f"Fail to get metric {metric_name}")

    def get_value(self, metric_name: str) -> Optional[float]:
        with sqlite_cursor(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return None
            metric = self._get_metric(cursor, metric_name)
            return metric["value"]

    def get_quota(self, metric_name: str) -> Optional[float]:
        with sqlite_cursor(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return None
            metric = self._get_metric(cursor, metric_name)
            return metric["quota"]

    def set_quota(self, metric_name: str, quota: float) -> bool:
        with sqlite_transaction(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return False
            cursor.execute(
                f"""
                UPDATE {self.table_name}
                SET quota = ?
                WHERE name = ?
            """,
                (quota, metric_name),
            )
            return True

    def get_unit(self, metric_name: str) -> Optional[str]:
        with sqlite_cursor(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return None
            metric = self._get_metric(cursor, metric_name)
            return metric["unit"]

    def get_metric(self, metric_name: str) -> Optional[dict]:
        with sqlite_cursor(self.db_path) as cursor:
            if not self._exists(cursor, metric_name):
                return None
            return self._get_metric(cursor, metric_name)

    def get_metrics(self, filter_regex: Optional[str] = None) -> dict:
        with sqlite_cursor(self.db_path) as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name}")
            rows = cursor.fetchall()
            metrics = {
                row[1]: {
                    "value": row[2],
                    "quota": row[3],
                    "unit": row[4],
                }
                for row in rows
            }
        if filter_regex is None:
            return metrics
        else:
            pattern = re.compile(filter_regex)
            return {
                key: value
                for key, value in metrics.items()
                if pattern.search(key)
            }

    def _exists(self, cursor: sqlite3.Cursor, name: str) -> bool:
        cursor.execute(
            f"""
            SELECT 1 FROM {self.table_name}
            WHERE name = ? LIMIT 1
        """,
            (name,),
        )
        return cursor.fetchone() is not None

    def exists(self, metric_name: str) -> bool:
        with sqlite_cursor(self.db_path) as cursor:
            return self._exists(cursor, metric_name)

    def update(self, values: dict, prefix: Optional[str] = None) -> None:
        with sqlite_transaction(self.db_path) as cursor:
            for metric_name, value in values.items():
                self._add(
                    cursor,
                    full_name(
                        name=metric_name,
                        prefix=prefix,
                    ),
                    value,
                )

    def _create_update_cost_trigger(
        self,
        token_metric: str,
        cost_metric: str,
        unit_price: float,
    ) -> None:
        with sqlite_transaction(self.db_path) as cursor:
            cursor.execute(
                f"""
                CREATE TRIGGER IF NOT EXISTS
                "{self.table_name}_{token_metric}_{cost_metric}_price"
                AFTER UPDATE OF value ON "{self.table_name}"
                FOR EACH ROW
                WHEN NEW.name = "{token_metric}"
                BEGIN
                    UPDATE {self.table_name}
                    SET value = value + (NEW.value - OLD.value) * {unit_price}
                    WHERE name = "{cost_metric}";
                END;
                """,
            )

    def register_budget(
        self,
        model_name: str,
        value: float,
        prefix: Optional[str] = None,
    ) -> bool:
        logger.info(f"set budget {value} to {model_name}")
        pricing = get_pricing()
        if model_name in pricing:
            budget_metric_name = full_name(
                name="cost",
                prefix=prefix,
            )
            ok = self.register(
                metric_name=budget_metric_name,
                metric_unit="dollor",
                quota=value,
            )
            if not ok:
                return False
            for metric_name, unit_price in pricing[model_name].items():
                token_metric_name = full_name(
                    name=metric_name,
                    prefix=prefix,
                )
                self.register(
                    metric_name=token_metric_name,
                    metric_unit="token",
                )
                self._create_update_cost_trigger(
                    token_metric_name,
                    budget_metric_name,
                    unit_price,
                )
            return True
        else:
            logger.warning(
                f"Calculate budgets for model [{model_name}] is not supported",
            )
            return False


def get_pricing() -> dict:
    """Get pricing as a dict

    Returns:
        `dict`: the dict with pricing information.
    """
    return {
        "gpt-4-turbo": {
            "prompt_tokens": 0.00001,
            "completion_tokens": 0.00003,
        },
        "gpt-4": {
            "prompt_tokens": 0.00003,
            "completion_tokens": 0.00006,
        },
        "gpt-4-32k": {
            "prompt_tokens": 0.00006,
            "completion_tokens": 0.00012,
        },
        "gpt-3.5-turbo": {
            "prompt_tokens": 0.000001,
            "completion_tokens": 0.000002,
        },
    }


class MonitorFactory:
    """Factory of Monitor.

    Get the singleton monitor using::

        from agentscope.utils import MonitorFactory
        monitor = MonitorFactory.get_monitor()
    """

    _instance = None

    @classmethod
    def get_monitor(
        cls,
        impl_type: Optional[str] = None,
        **kwargs: Any,
    ) -> MonitorBase:
        """Get the monitor instance.

        Returns:
            `MonitorBase`: the monitor instance.
        """
        if cls._instance is None:
            if impl_type is None or impl_type.lower() == "sqlite":
                cls._instance = SqliteMonitor(**kwargs)
            elif impl_type.lower() == "dict":
                cls._instance = DictMonitor()
            else:
                raise NotImplementedError(
                    "Monitor with type [{type}] is not implemented.",
                )
        return cls._instance  # type: ignore [return-value]
