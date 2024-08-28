import boto3

from tevico.framework.entities import report
from tevico.framework.entities.report.check_model import CheckReport
from tevico.framework.entities.check.check import Check


class rds_instance_multi_az(Check):

    def execute(self, connection: boto3.Session) -> CheckReport:
        report = CheckReport(name=__name__)
        client = connection.client('rds')
        response = client.describe_db_instances()
        for instance in response['DBInstances']:
            if not instance['MultiAZ']:
                report.passed = False
                report.resource_ids_status[instance['DBInstanceIdentifier']] = False
        return report
    