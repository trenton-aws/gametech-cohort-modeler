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
    aws_neptune as neptune,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam
)
from constructs import Construct


class Database(Stack):

    def __init__(self,
                 scope: Construct,
                 id_: str,
                 network_stack,
                 db_instance_size: str,
                 **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        neptune_security_group = ec2.CfnSecurityGroup(self, "CohortModelerSecurityGroup",
                                                      group_description="SG of Neptune DB",
                                                      security_group_egress=[
                                                          ec2.CfnSecurityGroup.EgressProperty(
                                                              ip_protocol="tcp",
                                                              cidr_ip=network_stack.vpc.cidr_block,
                                                              from_port=8182,
                                                              to_port=8182
                                                          )
                                                      ],
                                                      security_group_ingress=[
                                                          ec2.CfnSecurityGroup.IngressProperty(
                                                              ip_protocol="tcp",
                                                              cidr_ip=network_stack.vpc.cidr_block,
                                                              from_port=8182,
                                                              to_port=8182
                                                          )# ,
                                                          # ec2.CfnSecurityGroup.IngressProperty(
                                                          #     ip_protocol="tcp",
                                                          #     cidr_ip="0.0.0.0/0",
                                                          #     from_port=0,
                                                          #     to_port=65535
                                                          # )
                                                      ],
                                                      vpc_id=network_stack.vpc.attr_vpc_id
                                                      )

        neptune_managed_s3_role = iam.ManagedPolicy(self, "CohortManagedRoleS3",
                                                    description="Neptune default policy for S3 access for data load",
                                                    managed_policy_name="Cohort-neptune-s3-policy",
                                                    statements=[
                                                        iam.PolicyStatement(
                                                            effect=iam.Effect.ALLOW,
                                                            actions=[
                                                                "s3:Get*",
                                                                "s3:List*"
                                                            ],
                                                            resources=[
                                                                "arn:"+self.partition+":s3:::*"]
                                                        )
                                                    ]

                                                    )
        neptune_managed_logs_role = iam.ManagedPolicy(self, "CohortManagedRoleLogs",
                                                      description="Default policy for CloudWatch logs",
                                                      managed_policy_name="Cohort-neptune-cw-policy",
                                                      statements=[
                                                          iam.PolicyStatement(
                                                              effect=iam.Effect.ALLOW,
                                                              actions=[
                                                                  "logs:CreateLogGroup",
                                                                  "logs:PutRetentionPolicy"
                                                              ],
                                                              resources=[
                                                                  "arn:"+self.partition+":logs:" + self.region + ":" + self.account + \
                                                                  ":log-group:/aws/neptune/*"
                                                              ]
                                                          ),
                                                          iam.PolicyStatement(
                                                              effect=iam.Effect.ALLOW,
                                                              actions=[
                                                                  "logs:CreateLogStream",
                                                                  "logs:PutLogEvents",
                                                                  "logs:DescribeLogStreams",
                                                                  "logs:GetLogEvents",
                                                              ],
                                                              resources=[
                                                                  "arn:"+self.partition+":logs:" + self.region + ":" + self.account + \
                                                                  ":log-group:/aws/neptune/*:log-stream:*"
                                                              ]
                                                          )
                                                      ]
                                                      )

        neptune_role = iam.Role(self, "CohortNeptuneDBRole",
                                role_name="Cohort-neptune-iam-role",
                                assumed_by=iam.CompositePrincipal(
                                    iam.ServicePrincipal("rds.amazonaws.com"),
                                    iam.ServicePrincipal("monitoring.rds.amazonaws.com"),
                                ),
                                managed_policies=[
                                    neptune_managed_s3_role,
                                    neptune_managed_logs_role
                                ]
                                )

        neptune_subnet_group = neptune.CfnDBSubnetGroup(self, "CohortSubnetGroup",
                                                        db_subnet_group_name="cohort-db-subnet-group", #Cant use capitals in name
                                                        db_subnet_group_description="Subnets for Cohort Neptune Database",
                                                        subnet_ids=[
                                                            network_stack.private_subnet_1.subnet_id,
                                                            network_stack.private_subnet_2.subnet_id
                                                        ]
                                                        )

        neptune_cluster = neptune.CfnDBCluster(self, "CohortGraphDB",
                                               availability_zones=[
                                                   network_stack.region_table.find_in_map(self.region, "AZ1"),
                                                   network_stack.region_table.find_in_map(self.region, "AZ2")
                                               ],
                                               db_cluster_identifier="cohort-modeler-graph-db",
                                               vpc_security_group_ids=[neptune_security_group.attr_group_id],
                                               db_subnet_group_name=neptune_subnet_group.db_subnet_group_name,
                                               associated_roles=[neptune.CfnDBCluster.DBClusterRoleProperty(
                                                   role_arn=neptune_role.role_arn
                                               )]
                                               )
        neptune_instance = neptune.CfnDBInstance(self, "CohortGraphInstance",
                                                 db_instance_class=db_instance_size,
                                                 auto_minor_version_upgrade=True,
                                                 db_cluster_identifier=neptune_cluster.db_cluster_identifier
                                                 )


        # Create ordering dependency DBCluster
        neptune_cluster.node.add_dependency(neptune_security_group)
        neptune_cluster.node.add_dependency(neptune_role)
        neptune_cluster.node.add_dependency(neptune_subnet_group)

        # Create ordering dependency neptune instance
        neptune_instance.node.add_dependency(neptune_cluster)

        # Add neptune cluster to dbstack object
        self.neptune_cluster = neptune_cluster
        self.neptune_role = neptune_role
