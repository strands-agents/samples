import aws_cdk as core
import aws_cdk.assertions as assertions

from smart_building_analytics_agent.smart_building_analytics_agent_stack import SmartBuildingAnalyticsAgentStack

# example tests. To run these tests, uncomment this file along with the example
# resource in smart_building_analytics_agent/smart_building_analytics_agent_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SmartBuildingAnalyticsAgentStack(app, "smart-building-analytics-agent")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
