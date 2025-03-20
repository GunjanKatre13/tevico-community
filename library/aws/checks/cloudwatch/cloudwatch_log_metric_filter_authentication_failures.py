"""
AUTHOR: Sheikh Aafaq Rashid
EMAIL: aafaq.rashid@comprinno.net
DATE: 2025-01-10
"""

import boto3
import re
from botocore.exceptions import BotoCoreError, ClientError

from tevico.engine.entities.report.check_model import (
    CheckReport, CheckStatus, AwsResource, GeneralResource, ResourceStatus
)
from tevico.engine.entities.check.check import Check


class cloudwatch_log_metric_filter_authentication_failures(Check):
    def execute(self, connection: boto3.Session) -> CheckReport:
        logs_client = connection.client('logs')
        report = CheckReport(name=__name__)
        report.resource_ids_status = []

        try:
            log_groups = []
            next_token = None

            while True:
                response = logs_client.describe_log_groups(nextToken=next_token) if next_token else logs_client.describe_log_groups()
                log_groups.extend(response.get('logGroups', []))
                next_token = response.get('nextToken')

                if not next_token:
                    break

            if not log_groups:
                report.status = CheckStatus.NOT_APPLICABLE
                report.resource_ids_status.append(
                    ResourceStatus(
                        resource=GeneralResource(name=""),
                        status=CheckStatus.NOT_APPLICABLE,
                        summary="No CloudWatch log groups found."
                    )
                )
                return report  # Early exit since there are no log groups to check

            # Define the custom pattern for authentication failure (ConsoleLogin + Failed authentication)
            pattern = r"\\$\\.eventName\\s*=\\s*.?ConsoleLogin.+\\$\\.errorMessage\\s*=\\s*.?Failed authentication.?"
            
            for log_group in log_groups:
                log_group_name = log_group.get('logGroupName')
                log_group_arn = log_group.get('arn')

                try:
                    metric_filters = logs_client.describe_metric_filters(logGroupName=log_group_name).get('metricFilters', [])
                    matching_filters = []
                    
                    for filter in metric_filters:
                        filter_pattern = filter.get("filterPattern", "")
                        if re.search(pattern, filter_pattern):
                            matching_filters.append(filter.get('filterName'))
                    
                    if matching_filters:
                        report.resource_ids_status.append(
                            ResourceStatus(
                                resource=AwsResource(arn=log_group_arn),
                                status=CheckStatus.PASSED,
                                summary=f"Log group {log_group_name} has authentication failure metric filters configured: {', '.join(matching_filters)}."
                            )
                        )
                    else:
                        report.status = CheckStatus.FAILED
                        report.resource_ids_status.append(
                            ResourceStatus(
                                resource=AwsResource(arn=log_group_arn),
                                status=CheckStatus.FAILED,
                                summary=f"Log group {log_group_name} does not have authentication failure metric filters configured."
                            )
                        )
                except (BotoCoreError, ClientError) as e:
                    report.status = CheckStatus.UNKNOWN
                    report.resource_ids_status.append(
                        ResourceStatus(
                            resource=AwsResource(arn=log_group_arn),
                            status=CheckStatus.UNKNOWN,
                            summary=f"Error retrieving metric filters for log group {log_group_name}.",
                            exception=str(e)
                        )
                    )
        except Exception as e:
            report.status = CheckStatus.UNKNOWN
            report.resource_ids_status.append(
                ResourceStatus(
                    resource=GeneralResource(name=""),
                    status=CheckStatus.UNKNOWN,
                    summary="Error retrieving CloudWatch log groups.",
                    exception=str(e)
                )
            )

        return report