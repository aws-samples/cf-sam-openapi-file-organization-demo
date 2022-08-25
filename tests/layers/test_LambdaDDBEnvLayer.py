"""
    Test Suite for /layers/lambdaDdbEnvLayer
"""
# Standard Imports

import unittest

import boto3
from moto import mock_dynamodb

# Common test helper utilities for setup
from tests.env_setup_for_tests import env_setup_for_tests
from tests.env_setup_for_tests import create_mock_widget_ddb_table

from pylambda.layers.lambdaDdbEnv.python.lambdaDdbEnvLayer import EnvParams


@mock_dynamodb
class TestLambdaDdbEnvLayer(unittest.TestCase):
    """
    Test Suite for /layers/lambdaDdbEnvLayer
    """

    def setUp(self):
        """
        Establish test configuration
        :return: Nothing
        """
        env_setup_for_tests()
        self.mock_dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.mock_table = create_mock_widget_ddb_table(self.mock_dynamodb)

        self.env_params = EnvParams()
        self.env_params.dynamodb = self.mock_dynamodb
        self.env_params.ddb_table = self.mock_table

    def tearDown(self):
        """
        Delete database resource and mock table
        """
        self.mock_table.delete()

    def test_widget_to_ddb(self):
        """
         Test convert from widget to DB ready object
        """
        widget = {"widgetName": "Super Widget", "color": "Red"}
        response = self.env_params.widget_to_ddb(widget)
        self.assertEqual(response, {"testing_ddb_pk": "Super Widget", "color": "Red"})

    def test_ddb_to_widget(self):
        """
        Test convert from DB object to widget
        """
        db_object = {"testing_ddb_pk": "Super Widget", "color": "Red"}
        response = self.env_params.ddb_to_widget(db_object)
        self.assertEqual(response, {"widgetName": "Super Widget", "color": "Red"})
