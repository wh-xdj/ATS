# -*- coding: utf-8 -*-
"""测试示例 - 展示如何使用框架"""
import pytest
from framework.utils import assert_response_success, assert_response_error


@pytest.mark.api
def test_example_with_async_client():
    """使用异步客户端测试API"""
    assert True
