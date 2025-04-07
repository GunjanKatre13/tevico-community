"""
AUTHOR: Prajwal G
EMAIL: prajwal.govindraja@comprinno.net
DATE: 2024-04-05
"""

import boto3
from tevico.engine.entities.report.check_model import AwsResource, GeneralResource, CheckReport, CheckStatus, ResourceStatus
from tevico.engine.entities.check.check import Check

class vpc_service_endpoint_enabled(Check):
    def execute(self, connection: boto3.Session) -> CheckReport:
        # -------------------------------------------------------------------
        # Initializes the check report.
        # -------------------------------------------------------------------
        report = CheckReport(name=__name__)
        report.status = CheckStatus.PASSED
        report.resource_ids_status = []
        
        try:
            # -------------------------------------------------------------------
            # Set up AWS clients for EC2 and STS.
            # EC2 client: to retrieve VPCs and flow logs.
            # STS client: to retrieve account information.
            # -------------------------------------------------------------------
            ec2_client = connection.client('ec2')
            sts_client = connection.client('sts')
            
            # -------------------------------------------------------------------
            # Retrieves AWS Account ID and Region.
            # These values are used for constructing valid ARNs for resources.
            # -------------------------------------------------------------------
            account_id = sts_client.get_caller_identity()['Account']
            region = ec2_client.meta.region_name
            
            # -------------------------------------------------------------------
            # Retrieves All VPCs Using Pagination.
            # Initializes an empty list to store VPCs.
            # -------------------------------------------------------------------
            vpcs = []
            next_token = None
            while True:
                if next_token:
                    response = ec2_client.describe_vpcs(NextToken=next_token)
                else:
                    response = ec2_client.describe_vpcs()
                vpcs.extend(response.get("Vpcs", []))
                next_token = response.get("NextToken")
                if not next_token:
                    break
            
            # -------------------------------------------------------------------
            # If the VPCs list is empty, marks the check as NOT_APPLICABLE,
            # -------------------------------------------------------------------
            if not vpcs:
                report.status = CheckStatus.NOT_APPLICABLE
                report.resource_ids_status.append(
                    ResourceStatus(
                        resource=GeneralResource(name=""),
                        status=CheckStatus.NOT_APPLICABLE,
                        summary="No VPCs found in the account."
                    )
                )
                return report

            # -------------------------------------------------------------------
            # Retrieves All VPC Endpoints Using Pagination.
            # Initializes an empty list for VPC endpoints.
            # -------------------------------------------------------------------
            vpc_endpoints = []
            next_token = None
            while True:
                if next_token:
                    response = ec2_client.describe_vpc_endpoints(NextToken=next_token)
                else:
                    response = ec2_client.describe_vpc_endpoints()
                vpc_endpoints.extend(response.get("VpcEndpoints", []))
                next_token = response.get("NextToken")
                if not next_token:
                    break

            # -------------------------------------------------------------------
            # Groups VPC Endpoints by VPC ID.
            # This creates a dictionary where each key is a VPC ID and its value
            # is a list of endpoints associated with that VPC.
            # -------------------------------------------------------------------
            endpoints_by_vpc = {}
            for endpoint in vpc_endpoints:
                vpc_id = endpoint.get("VpcId")
                if vpc_id:
                    endpoints_by_vpc.setdefault(vpc_id, []).append(endpoint)

            # -------------------------------------------------------------------
            # Evaluates Each VPC.
            # For each VPC, checks if there is at least one associated endpoint that
            # is in the "available" state.
            # -------------------------------------------------------------------
            for vpc in vpcs:
                vpc_id = vpc.get("VpcId")
                vpc_arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
                resource = AwsResource(arn=vpc_arn, resource_id=vpc_id)
                
                # Retrieves the list of endpoints for this VPC from the grouped dictionary.
                endpoints = endpoints_by_vpc.get(vpc_id, [])
                # Filter the endpoints to include only those with state "available".
                available_endpoints = [ep for ep in endpoints if ep.get("State", "").lower() == "available"]
                
                # -------------------------------------------------------------------
                # Determine the Result and Construct a Summary Message.
                # If there are available endpoints, mark the VPC as PASSED.
                # Otherwise, marks it as FAILED and updates the overall report status.
                # -------------------------------------------------------------------
                if available_endpoints:
                    summary = (
                        f"VPC {vpc_id} has {len(available_endpoints)} service endpoint(s) "
                        f"that are in the 'available' state, meeting the requirement."
                    )
                    status = CheckStatus.PASSED
                else:
                    summary = (
                        f"VPC {vpc_id} does not have any service endpoints in the 'available' state. "
                        "At least one available endpoint is required."
                    )
                    status = CheckStatus.FAILED
                    report.status = CheckStatus.FAILED

                # -------------------------------------------------------------------
                # Appends the Evaluation Result for the VPC to the Report.
                # Each result includes the resource, its status, and a summary.
                # -------------------------------------------------------------------
                report.resource_ids_status.append(
                    ResourceStatus(
                        resource=resource,
                        status=status,
                        summary=summary
                    )
                )

        except Exception as e:
            # -------------------------------------------------------------------
            # Global Exception Handling.
            # If an error occurs during the process, mark the overall check as UNKNOWN
            # and record the error details.
            # -------------------------------------------------------------------
            report.status = CheckStatus.UNKNOWN
            report.resource_ids_status.append(
                ResourceStatus(
                    resource=GeneralResource(name=""),
                    status=CheckStatus.UNKNOWN,
                    summary=f"Error retrieving VPCs or endpoints: {str(e)}",
                    exception=str(e)
                )
            )
            
        return report