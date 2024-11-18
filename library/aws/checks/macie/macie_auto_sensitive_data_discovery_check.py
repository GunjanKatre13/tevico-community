"""
AUTHOR: deepak-puri-comprinno
EMAIL: deepak.puri@comprinno.net
DATE: 2024-11-16
"""

import boto3
from tevico.engine.entities.report.check_model import CheckReport
from tevico.engine.entities.check.check import Check
from botocore.exceptions import EndpointConnectionError

class macie_auto_sensitive_data_discovery_check(Check):
    def execute(self, connection: boto3.Session) -> CheckReport:
        client = connection.client('macie2')
        report = CheckReport(name=__name__)
        report.passed = True
        
        try:
            auto_discovery_status = client.get_automated_discovery_configuration()
            if auto_discovery_status['status'] == 'ENABLED':
                report.passed = True
            else:
                report.passed = False
        except (client.exceptions.AccessDeniedException, EndpointConnectionError):
            report.passed = False

        return report

