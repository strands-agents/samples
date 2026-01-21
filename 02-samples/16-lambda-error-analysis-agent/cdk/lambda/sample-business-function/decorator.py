import json
from functools import wraps
import traceback
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Generic event types
TASK_SUCCEEDED_DETAIL_TYPE = "TaskSucceeded"
TASK_FAILED_DETAIL_TYPE = "TaskFailed"
TASK_UPDATE_DETAIL_TYPE = "TaskUpdate"


def get_lambda_execution_info(context: LambdaContext, logger: Logger):
    """Get Lambda execution information for logging"""
    try:
        return (
            f"Lambda: {context.function_name} | "
            f"Request: {context.aws_request_id} | "
            f"Log: {context.log_group_name}/{context.log_stream_name}"
        )
    except Exception as e:
        logger.warning("Could not fetch Lambda execution information")
        logger.exception(e)
        return ""

def publish_event(eventbridge_client, event_bus_name, event, context, detailType, info, error):
    """Publish event to EventBridge with Lambda execution details"""
    event_body = {
        "eventDetail": event.get("detail", {}),
        "eventDetailType": event.get("detail-type", ""),
        "lambda": {
            "requestId": context.aws_request_id,
            "functionName": context.function_name,
            "logGroupName": context.log_group_name,
            "logStreamName": context.log_stream_name,
        },
    }
    if info:
        event_body["info"] = info
    if error:
        event_body["error"] = error

    try:
        eventbridge_client.put_events(
            Entries=[
                {
                    "Source": f"lambda.{context.function_name}",
                    "DetailType": detailType,
                    "Detail": json.dumps(event_body),
                    **({"EventBusName": event_bus_name} if event_bus_name else {}),
                }
            ]
        )
    except Exception as e:
        raise e


def publish_succeeded_event(eventbridge_client, event_bus_name, event, context, logger, info, status_code):
    """Publish success event to EventBridge"""
    logger.info(f"Publishing TaskSucceeded event with status code {status_code}")
    try:
        detailType = TASK_SUCCEEDED_DETAIL_TYPE
        if status_code == 102:
            detailType = TASK_UPDATE_DETAIL_TYPE
        publish_event(
            eventbridge_client=eventbridge_client,
            event_bus_name=event_bus_name,
            event=event,
            context=context,
            error=None,
            detailType=detailType,
            info=info,
        )
    except Exception as e:
        logger.exception("Failed to publish TaskSucceeded event", error=e)


def publish_failed_event(eventbridge_client, event_bus_name, event, context, logger, error, info):
    """Publish failure event to EventBridge"""
    logger.error("Publishing TaskFailed event", error=error)
    unknown_error = {
        "message": f"Unhandled error encountered. Please check the logs for {context.function_name}",
    }

    if not (error and isinstance(error, dict) and error.get("message")):
        error = unknown_error

    try:
        publish_event(
            eventbridge_client=eventbridge_client,
            event_bus_name=event_bus_name,
            event=event,
            context=context,
            error=error,
            detailType=TASK_FAILED_DETAIL_TYPE,
            info=info,
        )
    except Exception as e:
        logger.exception("Failed to publish TaskFailed event", error=e)


def error_capture(
    logger: Logger,
    eventbridge_client=None,
    event_bus_name=None,
    publish_succeeded: bool = True,
    publish_failed_on_error: bool = True,
    publish_failed_on_exception: bool = True,
    expose_errors: bool = False,
):
    """
    Decorator for AWS Lambda functions to automate event publishing and error handling.

    This decorator enhances a Lambda function by automatically publishing success or failure
    events to Amazon EventBridge. It captures exceptions, logs execution details, and provides
    structured error handling for Lambda functions.

    Parameters:
    - logger (Logger): AWS Lambda Powertools Logger instance for structured logging
    - eventbridge_client (boto3.client): EventBridge client for publishing events. 
      If None, events will not be published.
    - event_bus_name (str, optional): Name of the EventBridge event bus. 
      If None, uses the default event bus.
    - publish_succeeded (bool): If True, publishes TaskSucceeded event on successful execution 
      (statusCode 200-299 or 102 for updates). Default: True
    - publish_failed_on_error (bool): If True, publishes TaskFailed event when Lambda returns 
      error response (statusCode >= 400). Default: True
    - publish_failed_on_exception (bool): If True, catches unhandled exceptions and publishes 
      TaskFailed event with stack trace. Default: True
    - expose_errors (bool): If True, return detailed error information to caller.
      If False, return generic error message. Default: False
      
      SECURITY NOTE:
      - Set to False for production APIs exposed to end users (prevents information disclosure)
      - Set to True for internal tools and development environments (helpful for debugging)
      - Full error details are ALWAYS logged to CloudWatch regardless of this setting
      - Full error details are ALWAYS sent to EventBridge for AI analysis

    Event Types Published:
    - TaskSucceeded: Successful execution (statusCode 200-299)
    - TaskUpdate: In-progress update (statusCode 102)
    - TaskFailed: Error response or unhandled exception

    Event Payload Structure:
    {
        "eventDetail": {...},           # Original event detail
        "eventDetailType": "...",       # Original event detail-type
        "lambda": {
            "requestId": "...",         # Lambda request ID
            "functionName": "...",      # Lambda function name
            "logGroupName": "...",      # CloudWatch log group
            "logStreamName": "..."      # CloudWatch log stream
        },
        "info": "...",                  # Success info (optional)
        "error": {                      # Error details (optional)
            "message": "...",
            "debug": {"stackTrace": "..."}
        }
    }

    Error Response Behavior:
    When expose_errors=True (Development/Internal):
        {
            "statusCode": 500,
            "error": "Exception caught: 'email'",
            "stackTrace": "Traceback (most recent call last)...",
            "requestId": "abc-123-def-456"
        }

    When expose_errors=False (Production/External):
        {
            "statusCode": 500,
            "error": "Internal server error",
            "requestId": "abc-123-def-456",
            "message": "An error occurred. Please contact support with this request ID."
        }

    Usage Examples:
    ```python
    import boto3
    from aws_lambda_powertools import Logger
    from decorator import error_capture

    logger = Logger()
    eventbridge = boto3.client('events')

    # For internal/demo functions - show detailed errors
    @error_capture(logger, eventbridge, None, True, True, True, expose_errors=True)
    def lambda_handler(event, context):
        # Your business logic here
        return {"statusCode": 200, "info": "Task completed successfully"}

    # For production APIs - hide error details from users
    @error_capture(logger, eventbridge, None, True, True, True, expose_errors=False)
    def lambda_handler(event, context):
        # Your business logic here
        return {"statusCode": 200, "info": "Task completed successfully"}
    ```

    Notes:
    - Lambda function should return dict with 'statusCode' key for proper event routing
    - Stack traces are automatically captured and included in failure events
    - CloudWatch log links are included in event payload for debugging
    - If event_bus_name is None, events are published to the default event bus
    - Exceptions are caught and returned as structured responses (not re-raised)
    """

    def decorator(lambda_func):
        @wraps(lambda_func)
        def wrapper(event, context: LambdaContext, *args, **kwargs):

            # Log event received
            logger.debug("Event received")
            logger.info(event)

            logger.debug(
                "decorator settings",
                has_eventbridge_client=(eventbridge_client is not None),
                publish_succeeded=publish_succeeded,
                publish_failed_on_error=publish_failed_on_error,
                publish_failed_on_exception=publish_failed_on_exception,
            )

            def process_response(response):
                # Pre-initialize status_code and error in case that response was not a dict type
                # If response is a dict, override both values.
                status_code = 400
                error = {"message": "Lambda response is not a dict"}
                info = ""
                if response and isinstance(response, dict):
                    status_code = response.get("statusCode", 400)
                    error = response.get("error")
                    info = response.get("info")
                    if info:
                        info = info if isinstance(info, str) else json.dumps(info)

                lambda_info = get_lambda_execution_info(context, logger)
                info = f"{lambda_info} | {info}".strip() if info else lambda_info

                if publish_succeeded and ((200 <= status_code <= 299) or status_code == 102):
                    publish_succeeded_event(
                        eventbridge_client=eventbridge_client,
                        event_bus_name=event_bus_name,
                        event=event,
                        context=context,
                        logger=logger,
                        info=info,
                        status_code=status_code,
                    )
                elif publish_failed_on_error and status_code >= 400:
                    publish_failed_event(
                        eventbridge_client=eventbridge_client,
                        event_bus_name=event_bus_name,
                        event=event,
                        context=context,
                        logger=logger,
                        error=error,
                        info=info,
                    )
                return response

            if not publish_failed_on_exception:
                response = lambda_func(event, context, *args, **kwargs)
                process_response(response)
                return response

            try:
                response = lambda_func(event, context, *args, **kwargs)
            except Exception as e:
                error_message = f"Exception caught: {str(e)}"
                stack_trace = traceback.format_exc()
                
                # Always publish to EventBridge for internal analysis
                publish_failed_event(
                    eventbridge_client=eventbridge_client,
                    event_bus_name=event_bus_name,
                    event=event,
                    context=context,
                    logger=logger,
                    error={
                        "message": error_message,
                        "debug": {"stackTrace": stack_trace},
                    },
                    info=""
                )
                
                # Return appropriate response based on exposure setting
                if expose_errors:
                    # Development/Internal: Show detailed errors
                    return {
                        "statusCode": 500,
                        "error": error_message,
                        "stackTrace": stack_trace,
                        "requestId": context.aws_request_id
                    }
                else:
                    # Production/External: Generic error message
                    return {
                        "statusCode": 500,
                        "error": "Internal server error",
                        "requestId": context.aws_request_id,
                        "message": "An error occurred. Please contact support with this request ID."
                    }
            else:
                process_response(response)
                return response

        return wrapper

    return decorator
