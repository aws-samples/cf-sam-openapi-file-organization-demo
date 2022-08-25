"""
    Helper lambda layer for environment variables and DDB connections
"""
from os import environ
import boto3


class EnvParams:
    """
    Container Class for environment variables and DDB connection,
    as well as data mapping functions common to all methods
    """

    def __init__(self):
        """
        Init
        """
        self.dynamodb = boto3.resource('dynamodb')

        # Use environment variables for all dynamo PK and SK
        # in case of data model changes

        self.ddb_table = self.dynamodb.Table(environ['DynamoName'])
        self.ddb_pk = environ['DynamoPartitionKey']
        self.ddb_limit = environ['DynamoDefaultLimit']
        self.ddb_idx_color = environ['DynamoIndexColor']
        self.ddb_idx_color_pk = environ['DynamoIndexColorKey']

    def widget_to_ddb(self, widget: dict) -> dict:
        """
        Converts a widget dictionary to a DynamoDB item
        :param widget: Widget
        :return: ddb item
        """
        return {
            self.ddb_pk: widget["widgetName"],
            "color": widget["color"]
        }

    def ddb_to_widget(self, ddb_item: dict) -> dict:
        """
        Converts a DynamoDB item dictionary to a widget
        :param ddb_item: ddb item dictionary
        :return: Widget
        """
        return {
            "widgetName": ddb_item[self.ddb_pk],
            "color": ddb_item["color"]
        }
