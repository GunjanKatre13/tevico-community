"""
AUTHOR: 
DATE: 
"""

import boto3

from tevico.engine.entities.report.check_model import CheckReport
from tevico.engine.entities.check.check import Check


class ec2_ebs_default_encryption(Check):

    def execute(self, connection: boto3.Session) -> CheckReport:
         # Initialize EC2 client
        client = connection.client('ec2')

        report = CheckReport(name=__name__)

        # Initialize report status
        report.passed = True  # Assume passed unless default encryption is not enabled
        report.resource_ids_status = {}

        try:
            # Fetch EBS default encryption status
            res = client.describe_account_attributes(AttributeNames=['defaultEBSEncryption'])
            default_encryption_enabled = res['AccountAttributes'][0]['AttributeValues'][0]['Value'] == 'true'

            report.resource_ids_status['Default EBS Encryption'] = default_encryption_enabled

            if not default_encryption_enabled:
                report.passed = False  # If default encryption is not enabled, mark as failed

        except Exception as e:
            report.passed = False
            report.resource_ids_status = {}

        return report