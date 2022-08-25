"""
  Lambda Handler for /widget PUT
  Function operation: post or update a specific widget with { widgetName, color }

  Expects event[widgetName] and event[color] from the API GW body integration:
    api/paths/widget/widgetPut.yaml

    requestTemplates:
      "application/json": |
          #set($inputRoot = $input.path('$'))
          {
            "widgetName" : "$inputRoot.widgetName",
            "color" : "$inputRoot.color"
          }
"""

from typing import Any, ClassVar
import logging
from lambdaDdbEnvLayer import EnvParams
from botocore.exceptions import ClientError

#
# Global ENV will enable 1 connection setup per lambda instantiation,
# subsequent executions will re-use this connection for optimization.
#
GLOBAL_ENV = EnvParams()


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda Handler for /widget PUT

    :param event: lambda event
    :param context: lambda context
    :return: one widget record {widgetName, color} on 200
    """

    # One try-except block in lambda_handler for all AWS service calls
    try:
        return widget_put(event, GLOBAL_ENV)

    except ClientError as client_error:
        # AWS Service error handling
        logging.info('Context: %s %s', event, context)
        logging.error(client_error.response)
        raise Exception("error: Internal Server Error") from client_error


def widget_put(event: dict, env: ClassVar) -> dict:
    """
    Handler logic
    :param event: Lambda event Data
    :param env: environment configuration
    :return:
    """
    # widgetName and color is passed through the openAPI from requestTemplates
    # see api/paths/widget/widgetPut.yaml lines 30-40

    if "widgetName" not in event or len(event["widgetName"].strip()) == 0:
        # Validate the input, otherwise throw NotAcceptable
        raise Exception("NotAcceptable: Invalid input for widgetName")
    if "color" not in event or len(event["color"].strip()) == 0:
        # Validate the input, otherwise throw NotAcceptable
        raise Exception("NotAcceptable: Invalid input for color")

    put_payload = env.widget_to_ddb(event)

    # Dynamo DB query through the ENV object to facilitate mock/test
    env.ddb_table.update_item(
        Key={'PK': put_payload[env.ddb_pk]},
        UpdateExpression='SET color = :value',
        ExpressionAttributeValues={
            ':value': put_payload["color"]
        })

    return env.ddb_to_widget(put_payload)
