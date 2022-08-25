"""
    Test Suite for /reports/filterPage
"""

# Standard Imports
from sys import path
from os import environ
import unittest
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError
from moto import mock_dynamodb2

# Common test helper utilities for setup
from tests.env_setup_for_tests import env_setup_for_tests
from tests.env_setup_for_tests import create_mock_widget_ddb_table

# Set up lambda layer directories to support imports, establish mock env
path.extend(["pylambda/layers/lambdaDdbEnv/python"])
env_setup_for_tests()

# Class/proc's under test import
from pylambda.layers.lambdaDdbEnv.python.lambdaDdbEnvLayer import EnvParams
from pylambda.reports.filterPage.app import lambda_handler
from pylambda.reports.filterPage.app import widget_get


@mock_dynamodb2
class TestReportsFilterPage(unittest.TestCase):
    """
    Test Suite for /reports/filterPage
    """

    def setUp(self):
        """
        Establish test configuration
        :return:
        """
        env_setup_for_tests()
        self.mock_dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.mock_table = create_mock_widget_ddb_table(self.mock_dynamodb)

        self.sample_data = [{environ["DynamoPartitionKey"]: 'TEST001',
                             'color': 'red'},
                            {environ["DynamoPartitionKey"]: 'TEST002',
                             'color': 'blue'},
                            {environ["DynamoPartitionKey"]: 'TEST003',
                             'color': 'green'},
                            {environ["DynamoPartitionKey"]: 'TEST004',
                             'color': 'purple'},
                            {environ["DynamoPartitionKey"]: 'FOO',
                             'color': 'yellow'}
                            ]

        for data in self.sample_data:
            self.mock_table.put_item(Item=data)

        self.test_env = EnvParams()
        self.test_env.dynamodb = self.mock_dynamodb
        self.test_env.ddb_table = self.mock_table

    def tearDown(self):
        """
        Delete database resource and mock table
        """
        self.mock_table.delete()

    @patch('pylambda.reports.filterPage.app.logging')
    def test_widget_get(self, mock_log):
        """
        Test handler for widget_get
        :return:
        """

        # No parameters, no paging
        test_context = {}
        self.test_env.ddb_limit = len(self.sample_data) + 1
        ret = widget_get(test_context, self.test_env)
        assert len(ret["widgetList"]) == len(self.sample_data)
        assert ret["metadata"]["count"] == len(self.sample_data)

        # No parameters, filter out 1 item, no paging
        test_context = {"filter": "TEST"}
        self.test_env.ddb_limit = len(self.sample_data) + 1
        ret = widget_get(test_context, self.test_env)
        assert len(ret["widgetList"]) == (len(self.sample_data) - 1)
        assert ret["metadata"]["count"] == (len(self.sample_data) - 1)

        # Test limit
        test_context = {"limit": "1"}
        self.test_env.ddb_limit = len(self.sample_data) + 1
        ret = widget_get(test_context, self.test_env)
        assert len(ret["widgetList"]) == 1
        assert ret["metadata"]["count"] == 1

        # Test Paging
        test_context = {"limit": "1", "lastkey": "TEST003"}
        self.test_env.ddb_limit = len(self.sample_data) + 1
        ret = widget_get(test_context, self.test_env)
        assert len(ret["widgetList"]) == 1
        assert ret["metadata"]["count"] == 1

        # Test NotFound
        mock_log.return_value = None
        with self.assertRaises(Exception) as context:
            test_context = {"filter": "WILLNOTBEFOUND"}
            lambda_handler(test_context, None)
            self.assertTrue('NotFound' in str(context.exception))

    @patch('pylambda.reports.filterPage.app.logging')
    @patch('pylambda.reports.filterPage.app.GLOBAL_ENV')
    def test_lambda_handler(self, mock_env, mock_log):
        """
        Full test of lambda_handler
        :param self:
        :param mock_env: mocked object pylambda.reports.filterPage.app.logging
        :param mock_log: mocked object pylambda.reports.filterPage.app.EnvParams
        :return:
        """

        # Intercept the environment and logger
        mock_env.return_value = self.test_env
        mock_log.return_value = None

        # Test Error
        mock_env.side_effect = ClientError({"Error": {"Code": "500", "Message": "Error"}},
                                           "Operation", )
        with self.assertRaises(Exception) as context:
            test_context = {}
            lambda_handler(test_context, None)
            self.assertTrue('error' in str(context.exception))
