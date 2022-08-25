"""
  Lambda Handler for /widget/{widgetName} GET
  Function operation: retrieve a specific widget by widgetName

    Expects event[widgetName] from the API GW path integration:
        api/paths/widget/widgetWIdGetNameGet.yaml

        requestTemplates:
          "application/json":
                { "path": "$context.path",
                  "user-id": "$context.identity.userArn",
                  "widgetName": "$method.request.path.widgetName" }

"""

from typing import Any, ClassVar
import logging
from lambdaDdbEnvLayer import EnvParams
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

#
# Global ENV will enable 1 connection setup per lambda instantiation,
# subsequent executions will re-use this connection for optimization.
#
GLOBAL_ENV = EnvParams()

def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda Handler for /widget/{widgetName} GET

    :param event: lambda event
    :param context: lambda context
    :return: one widget record {widgetName, color}
    """

    # One try-except block in lambda_handler for all AWS service calls
    try:
        return widget_get(event, GLOBAL_ENV)

    except ClientError as client_error:
        # AWS Service error handling
        logging.info('Context: %s %s', event, context)
        logging.error(client_error.response)
        raise Exception("error: Internal Server Error") from client_error


def widget_get(event: dict, env: ClassVar) -> dict:
    """
    Retrieve a Widget from DynamoDB
    :param event: lambda event dictionary
    :param env: passed environment
    :return:
    """

    # widgetName is passed through the openAPI from method.request.path.widgetName
    # see api/paths/widget/widgetWIdGetNameGet.yaml line 37

    if "widgetName" not in event or len(event["widgetName"].strip()) == 0:
        # Validate the input, otherwise throw NotAcceptable
        raise Exception("NotAcceptable: Invalid input")

    # Dynamo DB query through the ENV object to facilitate mock/test
    db_response = env.ddb_table.query(
        KeyConditionExpression=Key(env.ddb_pk).eq(event["widgetName"]),
        Limit=1
    )

    if 'Items' not in db_response or len(db_response['Items']) == 0:
        # No return, throw NotFound
        raise Exception("NotFound: Item not located in DDB")

    # Convert DynamoDB entry to widget using centralized lambda layer method
    return env.ddb_to_widget(db_response['Items'][0])
