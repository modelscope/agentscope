# -*- coding: utf-8 -*-
# Copyright (c) Alibaba, Inc. and its affiliates.
# This file is licensed under the terms of the Apache 2.0 license. Some
# codes of this file is modified from
# https://github.com/alibaba/FederatedScope/blob/master/tests/run.py, which
# is also licensed under the terms of the Apache 2.0.
""" This module provides a test runner for unittest cases."""

import argparse
import os
import sys
import unittest

file_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(file_dir)

parser = argparse.ArgumentParser("test runner")
parser.add_argument("--list_tests", action="store_true", help="list all tests")
parser.add_argument("--pattern", default="*_test.py", help="test file pattern")
parser.add_argument(
    "--test_dir",
    default="tests",
    help="directory to be tested",
)
args = parser.parse_args()


def gather_test_cases(
    test_dir: str,
    pattern: str,
    list_tests: bool,
) -> unittest.TestSuite:
    """Gathers all the test cases that match the given pattern and
    directory."""
    test_suite = unittest.TestSuite()
    discover = unittest.defaultTestLoader.discover(
        test_dir,
        pattern=pattern,
        top_level_dir=None,
    )
    for suite_discovered in discover:
        for test_case in suite_discovered:
            test_suite.addTest(test_case)
            if hasattr(test_case, "__iter__"):
                for subcase in test_case:
                    if list_tests:
                        print(subcase)
            else:
                if list_tests:
                    print(test_case)
    return test_suite


def main() -> None:
    """Main func for the runner for unittest cases."""
    runner = unittest.TextTestRunner()
    test_suite = gather_test_cases(
        os.path.abspath(args.test_dir),
        args.pattern,
        args.list_tests,
    )
    if not args.list_tests:
        res = runner.run(test_suite)
        if not res.wasSuccessful():
            sys.exit(1)


if __name__ == "__main__":
    main()
