# -*- coding: utf-8 -*-
"""测试示例 - 展示如何使用框架"""
import pytest
from framework.utils import assert_response_success, assert_response_error


class TestDemo:
    def test_caseid_853873(self):
        """测试用例1"""
        assert True

    def test_caseid_144943(self):
        """测试用例2"""
        assert False

    def test_caseid_144163(self):
        """测试用例3"""
        assert Exception("测试用例3异常")
