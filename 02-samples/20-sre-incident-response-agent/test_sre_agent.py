"""
Unit tests for sre_agent.py tools.

These tests use mocked AWS clients so they can run without real AWS credentials.
Run with:  pytest test_sre_agent.py -v
"""

import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Force dry-run mode for all tests
os.environ["DRY_RUN"] = "true"
os.environ["AWS_REGION"] = "us-east-1"

# Import after setting env vars
from sre_agent import (  # noqa: E402
    fetch_log_events,
    get_metric_statistics,
    helm_rollback,
    helm_scale,
    kubectl_get,
    kubectl_rollout_restart,
    list_active_alarms,
    post_incident_report,
)


# ---------------------------------------------------------------------------
# CloudWatch Tools
# ---------------------------------------------------------------------------


class TestListActiveAlarms:
    @patch("sre_agent.boto3.client")
    def test_returns_alarm_list(self, mock_boto):
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        mock_cw.get_paginator.return_value.paginate.return_value = [
            {
                "MetricAlarms": [
                    {
                        "AlarmName": "my-service-HighCPU",
                        "Namespace": "AWS/ECS",
                        "MetricName": "CPUUtilization",
                        "Threshold": 85.0,
                        "ComparisonOperator": "GreaterThanThreshold",
                        "StateReason": "Threshold crossed",
                        "StateUpdatedTimestamp": datetime(2025, 1, 1, 12, 0, 0),
                    }
                ]
            }
        ]

        result = list_active_alarms()
        alarms = json.loads(result)

        assert len(alarms) == 1
        assert alarms[0]["name"] == "my-service-HighCPU"
        assert alarms[0]["threshold"] == 85.0
        assert alarms[0]["namespace"] == "AWS/ECS"

    @patch("sre_agent.boto3.client")
    def test_empty_when_no_alarms(self, mock_boto):
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        mock_cw.get_paginator.return_value.paginate.return_value = [
            {"MetricAlarms": []}
        ]

        result = list_active_alarms()
        assert json.loads(result) == []

    @patch("sre_agent.boto3.client")
    def test_namespace_filter_matches_on_namespace_field_not_alarm_name(self, mock_boto):
        """
        Regression test: namespace filtering must match the Namespace field of
        each alarm, not be passed as AlarmNamePrefix to the AWS API.
        AlarmNamePrefix is a string prefix on the alarm *name*, so passing a
        namespace string like 'AWS/ECS' would silently return an empty list
        even when matching alarms exist.
        """
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        mock_cw.get_paginator.return_value.paginate.return_value = [
            {
                "MetricAlarms": [
                    {
                        "AlarmName": "ecs-service-HighCPU",
                        "Namespace": "AWS/ECS",
                        "MetricName": "CPUUtilization",
                        "Threshold": 85.0,
                        "ComparisonOperator": "GreaterThanThreshold",
                        "StateReason": "Threshold crossed",
                        "StateUpdatedTimestamp": datetime(2025, 1, 1, 12, 0, 0),
                    },
                    {
                        "AlarmName": "lambda-errors-high",
                        "Namespace": "AWS/Lambda",
                        "MetricName": "Errors",
                        "Threshold": 10.0,
                        "ComparisonOperator": "GreaterThanThreshold",
                        "StateReason": "Threshold crossed",
                        "StateUpdatedTimestamp": datetime(2025, 1, 1, 12, 5, 0),
                    },
                ]
            }
        ]

        result = list_active_alarms(namespace="AWS/ECS")
        alarms = json.loads(result)

        # Only the ECS alarm should be returned; the Lambda alarm filtered out
        assert len(alarms) == 1
        assert alarms[0]["namespace"] == "AWS/ECS"
        assert alarms[0]["name"] == "ecs-service-HighCPU"

        # AlarmNamePrefix must NOT have been passed to the AWS paginator —
        # it operates on alarm names, not namespaces, and would silently
        # return nothing when a namespace string like 'AWS/ECS' is used.
        call_kwargs = mock_cw.get_paginator.return_value.paginate.call_args.kwargs
        assert "AlarmNamePrefix" not in call_kwargs, (
            "AlarmNamePrefix must not be used for namespace filtering; "
            "it matches alarm names, not CloudWatch namespaces."
        )

    @patch("sre_agent.boto3.client")
    def test_no_namespace_filter_returns_all_alarms(self, mock_boto):
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        mock_cw.get_paginator.return_value.paginate.return_value = [
            {
                "MetricAlarms": [
                    {
                        "AlarmName": "ecs-alarm",
                        "Namespace": "AWS/ECS",
                        "MetricName": "CPUUtilization",
                        "Threshold": 85.0,
                        "ComparisonOperator": "GreaterThanThreshold",
                        "StateReason": "Threshold crossed",
                        "StateUpdatedTimestamp": datetime(2025, 1, 1, 12, 0, 0),
                    },
                    {
                        "AlarmName": "lambda-alarm",
                        "Namespace": "AWS/Lambda",
                        "MetricName": "Errors",
                        "Threshold": 10.0,
                        "ComparisonOperator": "GreaterThanThreshold",
                        "StateReason": "Threshold crossed",
                        "StateUpdatedTimestamp": datetime(2025, 1, 1, 12, 5, 0),
                    },
                ]
            }
        ]

        result = list_active_alarms()
        alarms = json.loads(result)

        assert len(alarms) == 2


class TestGetMetricStatistics:
    @patch("sre_agent.boto3.client")
    def test_returns_sorted_datapoints(self, mock_boto):
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        mock_cw.get_metric_statistics.return_value = {
            "Datapoints": [
                {
                    "Timestamp": datetime(2025, 1, 1, 12, 5),
                    "Average": 90.0,
                    "Sum": 270.0,
                    "Maximum": 97.0,
                    "Unit": "Percent",
                },
                {
                    "Timestamp": datetime(2025, 1, 1, 12, 0),
                    "Average": 75.0,
                    "Sum": 225.0,
                    "Maximum": 80.0,
                    "Unit": "Percent",
                },
            ]
        }

        result = get_metric_statistics(
            namespace="AWS/ECS",
            metric_name="CPUUtilization",
            dimensions='[{"Name": "ServiceName", "Value": "my-service"}]',
        )
        datapoints = json.loads(result)

        assert len(datapoints) == 2
        # Should be sorted ascending by timestamp
        assert datapoints[0]["average"] == 75.0
        assert datapoints[1]["average"] == 90.0

    @patch("sre_agent.boto3.client")
    def test_handles_invalid_dimensions_json(self, mock_boto):
        mock_cw = MagicMock()
        mock_boto.return_value = mock_cw
        mock_cw.get_metric_statistics.return_value = {"Datapoints": []}

        # Should not raise even with malformed dimensions
        result = get_metric_statistics(
            namespace="AWS/Lambda",
            metric_name="Errors",
            dimensions="not-valid-json",
        )
        assert json.loads(result) == []


class TestFetchLogEvents:
    @patch("sre_agent.boto3.client")
    def test_returns_error_events(self, mock_boto):
        mock_logs = MagicMock()
        mock_boto.return_value = mock_logs
        mock_logs.filter_log_events.return_value = {
            "events": [
                {
                    "timestamp": 1700000000000,
                    "message": "ERROR: OOMKilled",
                    "logStreamName": "ecs/my-service/abc123",
                },
            ]
        }
        mock_logs.exceptions.ResourceNotFoundException = Exception

        result = fetch_log_events("/ecs/my-service")
        events = json.loads(result)

        assert len(events) == 1
        assert "OOMKilled" in events[0]["message"]

    @patch("sre_agent.boto3.client")
    def test_handles_missing_log_group(self, mock_boto):
        mock_logs = MagicMock()
        mock_boto.return_value = mock_logs
        mock_logs.exceptions.ResourceNotFoundException = Exception
        mock_logs.filter_log_events.side_effect = Exception("ResourceNotFoundException")

        result = fetch_log_events("/nonexistent/group")
        events = json.loads(result)

        assert len(events) == 1
        assert "error" in events[0]


# ---------------------------------------------------------------------------
# Dry-Run Remediation Tools
# ---------------------------------------------------------------------------


class TestKubectl:
    def test_kubectl_get_dry_run(self):
        result = kubectl_get("pods", "production")
        assert "[DRY-RUN]" in result
        assert "kubectl get pods -n production" in result

    def test_kubectl_rollout_restart_dry_run(self):
        result = kubectl_rollout_restart("my-api", "production")
        assert "[DRY-RUN]" in result
        assert "kubectl rollout restart deployment/my-api -n production" in result


class TestHelm:
    def test_helm_rollback_dry_run(self):
        result = helm_rollback("my-release", revision=3, namespace="staging")
        assert "[DRY-RUN]" in result
        assert "helm rollback my-release 3 -n staging" in result

    def test_helm_rollback_previous_revision(self):
        result = helm_rollback("my-release", revision=0)
        assert "[DRY-RUN]" in result
        # revision=0 means omit the revision number
        assert "3" not in result

    def test_helm_scale_dry_run(self):
        result = helm_scale("my-release", replicas=5)
        assert "[DRY-RUN]" in result
        assert "--replicas=5" in result


# ---------------------------------------------------------------------------
# Notification Tool
# ---------------------------------------------------------------------------


class TestPostIncidentReport:
    def test_prints_to_stdout_when_no_webhook(self, capsys):
        result = post_incident_report("Test incident summary", severity="P3")
        captured = capsys.readouterr()

        assert "stdout" in result.lower() or "printed" in result.lower()
        assert "Test incident summary" in captured.out
        assert "P3" in captured.out

    @patch("sre_agent.SLACK_WEBHOOK_URL", "https://hooks.slack.com/fake")
    def test_posts_to_slack_when_webhook_set(self):
        mock_resp = MagicMock()
        mock_resp.status = 200

        with patch("urllib.request.Request"), \
                patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda s: mock_resp
            mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)

            result = post_incident_report("Critical incident", severity="P1")
            assert "Slack" in result or "200" in result