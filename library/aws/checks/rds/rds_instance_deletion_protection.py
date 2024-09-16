import boto3

from tevico.app.entities.report.check_model import CheckReport
from tevico.app.entities.check.check import Check


class rds_instance_deletion_protection(Check):

    def execute(self, connection: boto3.Session) -> CheckReport:
        report = CheckReport(name=__name__)
        client = connection.client('rds')
        instances = client.describe_db_instances()['DBInstances']
        
        for instance in instances:
            instance_name = instance['DBInstanceIdentifier']
            
            if instance['DeletionProtection']:
                report.passed = True
                report.resource_ids_status[instance_name] = True
            else:
                report.passed = False
                report.resource_ids_status[instance_name] = False
                
        return report

    