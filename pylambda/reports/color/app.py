"""
  Lambda Handler for /reports/color/{color}
  Returns a full widget list with a particular color

   Expects event[color] from the API GW path integration:
        api/paths/reports/reportsColor.yaml

    requestTemplates:
      "application/json": |
          { "path": "$context.path",
            "user-id": "$context.identity.userArn",
            "color": "$method.request.path.color" }

"""
from typing import Any, ClassVar
import logging
from lambdaDdbEnvLayer import EnvParams
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# Initialize Global environment once for provisioned concurrency

GLOBAL_ENV = EnvParams()


def lambda_handler(event: dict, context: Any) -> list:
    """
    Lambda Handler for /reports/color/{color} GET

    :param event: lambda event
    :param context: lambda context
    :return: metadata and widget records {metadata, widgetList}
    """

    # One try-except block in lambda_handler for all AWS service calls
    try:
        return get_ddb_data(event, GLOBAL_ENV)

    except ClientError as client_error:
        # AWS Service error handling
        logging.info('Context: %s %s', event, context)
        logging.error(client_error.response)
        raise Exception("error: Internal Server Error") from client_error


def get_ddb_data(event: dict, env: ClassVar) -> list:
    """
    Retrieve widgets from dynamo dv that match the specified color
    :param env: Lambda execution environment variables and AWS resources
    :param event: lambda event
    :return:
    """

    if "color" not in event.keys() or len(event["color"]) == 0:
        raise Exception("Malformed path error")

    color_filter = event["color"]

    db_resp = env.ddb_table.query(
        IndexName=env.ddb_idx_color,
        KeyConditionExpression=Key(env.ddb_idx_color_pk).eq(color_filter),
        Limit=int(env.ddb_limit)
    )
    widget_list = [env.ddb_to_widget(item) for item in db_resp.get("Items", [])]

    # Paginate when compiling a full list
    while db_resp.get('LastEvaluatedKey', None) is not None:
        db_resp = env.ddb_table.query(
            IndexName=env.ddb_idx_color,
            KeyConditionExpression=Key(env.ddb_idx_color_pk).eq(color_filter),
            ExclusiveStartKey=db_resp['LastEvaluatedKey'],
            Limit=int(env.ddb_limit)
        )

        widget_list.extend([env.ddb_to_widget(item) for item in db_resp.get("Items", [])])

    # Raise NotFound if return is 0
    if len(widget_list) == 0:
        raise Exception("NotFound: no data matching query")

    return widget_list
