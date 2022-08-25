"""
    Test Suite for /reports/filterpage
"""
# Standard Imports

from sys import path
from os import environ
import unittest
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError
from moto import mock_dynamodb

# Common test helper utilities for setup
from tests.env_setup_for_tests import env_setup_for_tests
from tests.env_setup_for_tests import create_mock_widget_ddb_table

# Set up lambda layer directories to support imports, establish mock env
path.extend(["pylambda/layers/lambdaDdbEnv/python"])
env_setup_for_tests()

# Class/proc's under test import
from pylambda.layers.lambdaDdbEnv.python.lambdaDdbEnvLayer import EnvParams
from pylambda.reports.color.app import get_ddb_data
from pylambda.reports.color.app import lambda_handler

@mock_dynamodb
class TestReportsColor(unittest.TestCase):
    """
    Test Suite for /reports/filterpage
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
                             'color': 'blue'},
                            {environ["DynamoPartitionKey"]: 'TEST002',
                             'color': 'blue'},
                            {environ["DynamoPartitionKey"]: 'TEST003',
                             'color': 'green'},
                            {environ["DynamoPartitionKey"]: 'TEST004',
                             'color': 'purple'},
                            {environ["DynamoPartitionKey"]: 'FOO',
                             'color': 'blue'}
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

    def test_get_ddb_data(self):
        """
        Full test of get_ddb_data
        :param self:
        :return:
        """

        # No paging
        self.test_env.ddb_limit = 10
        ret = get_ddb_data({"color": "blue"}, self.test_env)
        assert len(ret) == 3

        # With paging, limit 1 per page to force
        self.test_env.ddb_limit = 1
        ret = get_ddb_data({"color": "blue"}, self.test_env)
        assert len(ret) == 3

        # One
        self.test_env.ddb_limit = 1
        ret = get_ddb_data({"color": "green"}, self.test_env)
        assert len(ret) == 1

        # Zero
        self.test_env.ddb_limit = 1
        with self.assertRaises(Exception) as context:
            get_ddb_data({"color": "WILLNOTFIND"}, self.test_env)
            self.assertTrue('NotFound' in str(context.exception))

        self.test_env.ddb_limit = 1
        with self.assertRaises(Exception) as context:
            get_ddb_data({}, self.test_env)
            self.assertTrue('Malformed' in str(context.exception))

    @patch('pylambda.reports.color.app.logging')
    @patch('pylambda.reports.color.app.get_ddb_data')
    @patch('pylambda.reports.color.app.GLOBAL_ENV')
    def test_lambda_handler(self, mock_env, mock_get_ddb_data, mock_log):
        """
        Full test of lambda_handler
        :param self:
        :param mock_env: mocked object pylambda.reports.color.app.logging
        :param mock_get_ddb_data: pylambda.reports.color.app.get_ddb_data
        :param mock_log: mocked object pylambda.reports.color.app.logging
        :return:
        """

        # Intercept the environment and logger
        mock_env.return_value = self.test_env
        mock_get_ddb_data.return_value = [{"TEST": "OK"}]
        mock_log.return_value = None

        # Test good data directly returned
        ret = lambda_handler({"color": "green"}, None)
        assert len(ret) == 1
        assert ret[0].get("TEST") == "OK"

        # Test AWS Error
        mock_get_ddb_data.side_effect = ClientError({"Error": {"Code": "500", "Message": "Error"}},
                                                    "Operation", )
        test_context = {"color": "WILLNOTBEFOUND"}
        with self.assertRaises(Exception) as context:
            lambda_handler(test_context, None)
        mock_log.error.assert_called_once()
        mock_log.info.assert_called_once()
        self.assertTrue('error' in str(context.exception))
