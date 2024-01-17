# -*- coding: utf-8 -*-
""" Operate file test."""
import os
import shutil
import unittest

from agentscope.service import (
    create_file,
    delete_file,
    move_file,
    create_directory,
    delete_directory,
    move_directory,
    read_text_file,
    write_text_file,
    read_json_file,
    write_json_file,
)
from agentscope.service.service_status import ServiceExecStatus


class OperateFileTest(unittest.TestCase):
    """
    Operate file test.
    """

    def setUp(self) -> None:
        """Set up test variables."""
        self.file_name = "tmp_file.txt"
        self.moved_file_name = "moved_tmp_file.txt"
        self.dir_name = "tmp_dir"
        self.moved_dir_name = "moved_tmp_dir"

        self.txt_file_name = "tmp_txt_file.txt"
        self.json_file_name = "tmp_json_file.json"

        self.tearDown()

    def tearDown(self) -> None:
        """Clean up before & after tests."""
        if os.path.exists(self.file_name):
            os.remove(self.file_name)
        if os.path.exists(self.moved_file_name):
            os.remove(self.moved_file_name)
        if os.path.exists(self.dir_name):
            shutil.rmtree(self.dir_name)
        if os.path.exists(self.moved_dir_name):
            shutil.rmtree(self.moved_dir_name)
        if os.path.exists(self.txt_file_name):
            os.remove(self.txt_file_name)

    def test_file(self) -> None:
        """Execute file test."""
        is_success = create_file(self.file_name, "This is a test").status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

        is_success = move_file(self.file_name, self.moved_file_name).status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

        is_success = delete_file(self.moved_file_name).status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

    def test_dir(self) -> None:
        """Execute dir test."""
        is_success = create_directory(self.dir_name).status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

        is_success = move_directory(self.dir_name, self.moved_dir_name).status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

        is_success = delete_directory(self.moved_dir_name).status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

    def test_txt(self) -> None:
        """Execute txt test."""
        is_success = write_text_file(
            self.txt_file_name,
            "This is a test",
            True,
        ).status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

        info = read_text_file(self.txt_file_name).content
        self.assertEqual(info, "This is a test")

    def test_json(self) -> None:
        """Execute json test."""
        data = {"test": "This is a test"}
        is_success = write_json_file(self.json_file_name, data, True).status
        self.assertEqual(is_success, ServiceExecStatus.SUCCESS)

        info = read_json_file(self.json_file_name).content
        self.assertEqual(info, f"{data}")


if __name__ == "__main__":
    unittest.main()
