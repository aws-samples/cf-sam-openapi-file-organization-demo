"""
  Lambda Handler for /reports/filterpage
  Returns a full widget list with support for web pagination

    Optional query parameters:
        event[limit] - the number of records to return
        event[lastkey] - the starting widget of the list
        event[filter] - a "contains" filtering of widget name

     Optional parameters are passed from the API GW with querystring integration:
        api/paths/reports/reportsAll.yaml

    requestParameters:
      - integration.request.querystring.limit: "method.request.querystring.limit"
      - integration.request.querystring.lastkey: "method.request.querystring.lastkey"
      - integration.request.querystring.filter: "method.request.querystring.filter"
    requestTemplates:
      "application/json": |
        #set ($root=$input.path('$'))
        { "limit": "$method.request.querystring.limit",
          "lastKey": "$method.request.querystring.lastkey",
          "filter": "$method.request.querystring.filter"
        }

"""

from typing import Any, ClassVar
import logging
from lambdaDdbEnvLayer import EnvParams
from botocore.exceptions import ClientError

# Initialize Global environment once for provisioned concurrency

GLOBAL_ENV = EnvParams()


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda Handler for /reports/filterpage GET

    :param event: lambda event
    :param context: lambda context
    :return: metadata and widget records {metadata, widgetList}
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
    Retrieve a page of widgets based on event parameters
    :param event: lambda event dictionary
    :param env: passed environment
    :return:
    """

    # See if the client wants a specific limit, else set the default limit
    if "limit" in event.keys() and len(event["limit"]) > 0 and int(event["limit"]) > 0:
        scan_limit = int(event["limit"])
    else:
        scan_limit = int(env.ddb_limit)

    # Build the DynamoDb query dynamically based on query parameters
    # ProjectionExpression and Limit are always specified
    scan_kwargs = {
        'ProjectionExpression': env.ddb_pk + ", color",
        'Limit': scan_limit
    }

    # Client requests an option for filtering on widget name
    if "filter" in event.keys() and len(event["filter"]) > 0:
        scan_kwargs["FilterExpression"] = 'contains(#S, :s)'
        scan_kwargs["ExpressionAttributeNames"] = {"#S": env.ddb_pk}
        scan_kwargs["ExpressionAttributeValues"] = {":s": event["filter"]}

    # Client has specified a pagination start
    if "lastKey" in event.keys() and len(event["lastKey"]) > 0:
        scan_kwargs["ExclusiveStartKey"] = {env.ddb_pk: event["lastKey"]}

    # Execute the query
    response = env.ddb_table.scan(**scan_kwargs)

    # Raise NotFound if return is 0
    if len(response.get("Items", [])) == 0:
        raise Exception("NotFound: no data matching query")

    # Return the payload.  With web client pagination,
    # you will need to specify "next" so it can pass it as "lastKey"
    # in the next call


    data = [env.ddb_to_widget(item) for item in response.get("Items", [])]

    return {
        "metadata": {
            "next": response.get("LastEvaluatedKey", {env.ddb_pk: ""})[env.ddb_pk],
            "previous": event.get("lastKey", ""),
            "message": "OK",
            "count": len(data)
        },
        "widgetList": data
    }
