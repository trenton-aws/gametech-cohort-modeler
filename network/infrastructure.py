# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from aws_cdk import (
    aws_ec2 as ec2,
    CfnMapping,
    Stack,
    aws_iam as iam
)
from constructs import Construct


class Network(Stack):

    def __init__(self,
                 scope: Construct,
                 id_: str,
                 vpc_cidr: str,
                 public_subnet_cidr,
                 private_subnet_1_cidr: str,
                 private_subnet_2_cidr: str,
                 **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        # The code that defines your stack goes here
        region_table = CfnMapping(self, "RegionTable",
                                  mapping={
                                      "ap-southeast-1": {
                                          "AZ1": "ap-southeast-1a",
                                          "AZ2": "ap-southeast-1b"
                                      },
                                      "ap-southeast-2": {
                                          "AZ1": "ap-southeast-2a",
                                          "AZ2": "ap-southeast-2b"
                                      },
                                      "ap-northeast-1": {
                                          "AZ1": "ap-northeast-1a",
                                          "AZ2": "ap-northeast-1b"
                                      },
                                      "ap-northeast-2": {
                                          "AZ1": "ap-northeast-2a",
                                          "AZ2": "ap-northeast-2b"
                                      },
                                      "ap-south-1": {
                                          "AZ1": "ap-south-1a",
                                          "AZ2": "ap-south-1b"
                                      },
                                      "ap-east-1": {
                                          "AZ1": "ap-east-1a",
                                          "AZ2": "ap-east-1b"
                                      },
                                      "ca-central-1": {
                                          "AZ1": "ca-central-1a",
                                          "AZ2": "ca-central-1b"
                                      },
                                      "eu-central-1": {
                                          "AZ1": "eu-central-1a",
                                          "AZ2": "eu-central-1b"
                                      },
                                      "eu-west-1": {
                                          "AZ1": "eu-west-1a",
                                          "AZ2": "eu-west-1b"
                                      },
                                      "eu-west-2": {
                                          "AZ1": "eu-west-2a",
                                          "AZ2": "eu-west-2b"
                                      },
                                      "eu-west-3": {
                                          "AZ1": "eu-west-3a",
                                          "AZ2": "eu-west-3b"
                                      },
                                      "eu-north-1": {
                                          "AZ1": "eu-north-1a",
                                          "AZ2": "eu-north-1b"
                                      },
                                      "sa-east-1": {
                                          "AZ1": "sa-east-1a",
                                          "AZ2": "sa-east-1b"
                                      },
                                      "us-east-1": {
                                          "AZ1": "us-east-1a",
                                          "AZ2": "us-east-1b"
                                      },
                                      "us-east-2": {
                                          "AZ1": "us-east-2a",
                                          "AZ2": "us-east-2b"
                                      },
                                      "us-west-1": {
                                          "AZ1": "us-west-1a",
                                          "AZ2": "us-west-1b"
                                      },
                                      "us-west-2": {
                                          "AZ1": "us-west-2a",
                                          "AZ2": "us-west-2b"
                                      },
                                  }
                                  )
        # Create VPC
        vpc = ec2.CfnVPC(self, "Cohort Modeler VPC",
                         cidr_block=vpc_cidr,
                         enable_dns_support=True,
                         enable_dns_hostnames=True
                         )


        # Create Public Subnet
        public_subnet = ec2.Subnet(self, "CohortPublicSubnet",
                                   vpc_id=vpc.attr_vpc_id,
                                   availability_zone=region_table.find_in_map(self.region, "AZ1"),
                                   cidr_block=public_subnet_cidr,
                                   map_public_ip_on_launch=True
                                   )

        # Create and attach internet gateway for public subnet
        internet_gateway = ec2.CfnInternetGateway(self, "CohortModelerInternetGateway")
        public_gateway_attachment = ec2.CfnVPCGatewayAttachment(self, "CohortModelerInternetGatewayAttachement",
                                                                vpc_id=vpc.attr_vpc_id,
                                                                internet_gateway_id=internet_gateway.attr_internet_gateway_id
                                                                )
        # Create default internet out for public subnet
        public_subnet.add_default_internet_route(internet_gateway.attr_internet_gateway_id, public_gateway_attachment)

        # Create Private Subnet 1 with public Nat Gateway and add default route out to internet
        private_subnet_1 = ec2.Subnet(self, "CohortPrivateSubnet1",
                                      vpc_id=vpc.attr_vpc_id,
                                      availability_zone=region_table.find_in_map(self.region, "AZ1"),
                                      cidr_block=private_subnet_1_cidr
                                      )
        eip_nat_gateway_1 = ec2.CfnEIP(self, "CohortModelerEIP1")
        nat_gateway = ec2.CfnNatGateway(self, "CohortModelerNatGateway1",
                                        subnet_id=private_subnet_1.subnet_id,
                                        allocation_id=eip_nat_gateway_1.attr_allocation_id
                                        )
        private_subnet_1.add_route("CohortPublicRoutePrivateSubnet1",
                                   router_id=nat_gateway.attr_nat_gateway_id,
                                   router_type=ec2.RouterType.NAT_GATEWAY,
                                   destination_cidr_block="0.0.0.0/0"
                                   )
        # Private Subnet 2 with public Nat Gateway and create default route to internet
        private_subnet_2 = ec2.Subnet(self, "CohortPrivateSubnet2",
                                      vpc_id=vpc.attr_vpc_id,
                                      availability_zone=region_table.find_in_map(self.region, "AZ2"),
                                      cidr_block=private_subnet_2_cidr
                                      )
        eip_nat_gateway_2 = ec2.CfnEIP(self, "CohortModelerEIP2")
        nat_gateway = ec2.CfnNatGateway(self, "CohortModelerNatGateway2",
                                        subnet_id=private_subnet_2.subnet_id,
                                        allocation_id=eip_nat_gateway_2.attr_allocation_id
                                        )
        private_subnet_2.add_route("CohortPublicRoutePrivateSubnet2",
                                   router_id=nat_gateway.attr_nat_gateway_id,
                                   router_type=ec2.RouterType.NAT_GATEWAY,
                                   destination_cidr_block="0.0.0.0/0"
                                   )

        # Assigning values to Network stack
        self.public_subnet = public_subnet
        self.private_subnet_1 = private_subnet_1
        self.private_subnet_2 = private_subnet_2
        self.vpc = vpc
        self.region_table=region_table

        # Create S3 Endpoint
        s3_endpoint = ec2.CfnVPCEndpoint(self, "CohortS3VPCEndpoint",
                                         vpc_id=vpc.attr_vpc_id,
                                         service_name="com.amazonaws." + self.region + ".s3",
                                         route_table_ids=[
                                             private_subnet_1.route_table.route_table_id,
                                             private_subnet_2.route_table.route_table_id
                                         ],
                                         policy_document=iam.PolicyDocument(
                                             statements=[iam.PolicyStatement(
                                                 actions=[
                                                     "s3:Get*",
                                                     "s3:List*"
                                                 ],
                                                 resources=[
                                                     "arn:"+self.partition+":s3:::*"
                                                 ],
                                                 effect=iam.Effect.ALLOW,
                                                 principals=[
                                                     iam.AnyPrincipal()
                                                 ]
                                             )]
                                         )
                                         )
