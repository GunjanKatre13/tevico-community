"""
AUTHOR: deepak-puri-comprinno
EMAIL: deepak.puri@comprinno.net
DATE: 2024-11-15
"""
import boto3
from tevico.engine.entities.report.check_model import CheckReport
from tevico.engine.entities.check.check import Check

class cloudfront_cloudwatch_logging_enabled(Check):
    def execute(self, connection: boto3.Session) -> CheckReport:
        client = connection.client('cloudfront')
        report = CheckReport(name=__name__)
        report.passed = True
        distributions = client.list_distributions()
        
        if distributions.get('DistributionList', {}).get('Items'):
            for distribution in distributions['DistributionList']['Items']:
                dist_id = distribution['Id']

                try:
                    monitoring_config = client.get_monitoring_subscription(DistributionId=dist_id)
                    if monitoring_config.get('MonitoringSubscription', {}).get('RealtimeMetricsSubscriptionConfig', {}).get('RealtimeMetricsSubscriptionStatus') == 'Enabled':
                        report.resource_ids_status[dist_id] = True
                    else:
                        report.resource_ids_status[dist_id] = False
                        report.passed = False
                except client.exceptions.NoSuchMonitoringSubscription:
                    report.resource_ids_status[dist_id] = False
                    report.passed = False
        else:
            report.passed = True  
            
        return report
