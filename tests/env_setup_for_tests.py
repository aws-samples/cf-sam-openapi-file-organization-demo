from os import environ
import boto3

def env_setup_for_tests():
    """
    Set the OD Environment for testing
    :return:
    """

    environ["AWS_ACCESS_KEY_ID"] = "testing"  # nosec
    environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # nosec
    environ["AWS_SECURITY_TOKEN"] = "testing"  # nosec
    environ["AWS_SESSION_TOKEN"] = "testing"  # nosec

    environ["DynamoName"] = "testing_ddb"
    environ["DynamoPartitionKey"] = "testing_ddb_pk"
    environ['DynamoDefaultLimit'] = "1"
    environ['DynamoIndexColor'] = "testing_color_idx"
    environ['DynamoIndexColorKey'] = "color"

def create_mock_widget_ddb_table(dynamodb=None):
    """
    Create a DynamoDB table for unit testing
    :param dynamodb: DynamoDB resource for table creation
    :return:
    """
    if not dynamodb:
        dynamodb = boto3.resource(
            "dynamodb", endpoint_url="http://localhost:8000"
        )

    table = dynamodb.create_table(
        TableName=environ["DynamoName"],
        KeySchema=[
            {"AttributeName": environ["DynamoPartitionKey"], "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": environ["DynamoPartitionKey"], "AttributeType": "S"},
            {"AttributeName": "color", "AttributeType": "S"}
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 10,
            "WriteCapacityUnits": 10,
        },
        GlobalSecondaryIndexes=[
            {
                "IndexName": environ['DynamoIndexColor'],
                "KeySchema": [
                    {"AttributeName": "color", "KeyType": "HASH"}
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 10,
                    "WriteCapacityUnits": 10,
                },
            }
        ],
    )

    return table
