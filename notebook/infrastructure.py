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
    aws_sagemaker as sagemaker,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    Fn
)
from constructs import Construct
import textwrap


class Notebook(Stack):

    def __init__(self,
                 scope: Construct,
                 id_: str,
                 network_stack,
                 db_stack,
                 **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        cohort_notebook_security_group = ec2.CfnSecurityGroup(self, "CohortNotebookSecurityGroup",
                                                              group_description="SG of Cohort Notebook Instance",
                                                              security_group_egress=[
                                                                  ec2.CfnSecurityGroup.EgressProperty(
                                                                      ip_protocol="-1",
                                                                      cidr_ip=network_stack.vpc.cidr_block,
                                                                      from_port=0,
                                                                      to_port=65535
                                                                  )
                                                              ],
                                                              vpc_id=network_stack.vpc.attr_vpc_id
                                                              )

        cohort_notebook_role = iam.Role(self, "CohortNotebookRole",
                                        assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
                                        path="/",
                                        inline_policies={
                                            "NotebookPolicy": iam.PolicyDocument(
                                                statements=[
                                                    iam.PolicyStatement(
                                                        effect=iam.Effect.ALLOW,
                                                        actions=[
                                                            "cloudwatch:PutMetricData"
                                                        ],
                                                        resources=[
                                                            "arn:" + self.partition + ":cloudwatch:" + self.region + ":" + self.account + ":*"
                                                        ]
                                                    ),
                                                    iam.PolicyStatement(
                                                        effect=iam.Effect.ALLOW,
                                                        actions=[
                                                            "logs:CreateLogGroup",
                                                            "logs:CreateLogStream",
                                                            "logs:DescribeLogStreams",
                                                            "logs:PutLogEvents",
                                                            "logs:GetLogEvents",
                                                        ],
                                                        resources=[
                                                            "arn:" + self.partition + ":cloudwatch:" + self.region + ":" \
                                                            + self.account + ":*"
                                                        ]
                                                    ),
                                                    iam.PolicyStatement(
                                                        effect=iam.Effect.ALLOW,
                                                        actions=[
                                                            "s3:Get*",
                                                            "s3:List*"
                                                        ],
                                                        resources=[
                                                            "arn:" + self.partition + ":s3:::*"
                                                        ]
                                                    ),
                                                    iam.PolicyStatement(
                                                        effect=iam.Effect.ALLOW,
                                                        actions=[
                                                            "s3:PutObject",
                                                            "neptune-db:connect",
                                                            "s3:List"
                                                        ],
                                                        resources=[
                                                            "arn:" + self.partition + ":s3:::*",
                                                            "arn:" + self.partition + ":rds:" + self.region + ":" \
                                                            + self.account + ":cluster:*"
                                                        ]
                                                    )
                                                ]
                                            )
                                        }
                                        )
        notebook_boot_script = \
            '''\
            #!/bin/bash 
            sudo -u ec2-user -i << 'EOF'
            echo 'export GRAPH_NOTEBOOK_AUTH_MODE=DEFAULT' >> ~/.bashrc
            echo 'export GRAPH_NOTEBOOK_HOST={neptuneEndpoint}' >> ~/.bashrc
            echo 'export GRAPH_NOTEBOOK_PORT={neptunePort}' >> ~/.bashrc
            echo 'export NEPTUNE_LOAD_FROM_S3_ROLE_ARN={neptuneRoleArn}' >> ~/.bashrc
            echo 'export AWS_REGION={region}' >> ~/.bashrc
            aws s3 cp s3://aws-neptune-notebook/graph_notebook.tar.gz /tmp/graph_notebook.tar.gz
            rm -rf /tmp/graph_notebook
            tar -zxvf /tmp/graph_notebook.tar.gz -C /tmp
            /tmp/graph_notebook/install.sh
            aws s3 cp s3://aws-neptune-customer-samples/aws-gametech-blog/cohort-modeler/data/seed/ /home/ec2-user/anaconda3/envs/JupyterSystemEnv/lib/python3.7/site-packages/graph_notebook/seed/queries/propertygraph/cohort_modeler/ --recursive
            aws s3 cp s3://aws-neptune-customer-samples/aws-gametech-blog/cohort-modeler/CohortModelerSampleNotebook.ipynb /home/ec2-user/SageMaker/
            EOF
            '''.format(neptuneEndpoint=db_stack.neptune_cluster.attr_endpoint,
                       neptunePort=db_stack.neptune_cluster.attr_port,
                       neptuneRoleArn=db_stack.neptune_role.role_arn,
                       region=self.region
                       )

        cohort_notebook_lifecycle = sagemaker.CfnNotebookInstanceLifecycleConfig(self, "CohortNotebookLifecycleConfig",
                                                                                 on_start=[
                                                                                     sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
                                                                                         content=Fn.base64(
                                                                                             textwrap.dedent(
                                                                                                 notebook_boot_script)
                                                                                         )
                                                                                     )
                                                                                 ])

        cohort_notebook_instance = sagemaker.CfnNotebookInstance(self, "CohortNotebookInstance",
                                                                 instance_type="ml.t3.medium",
                                                                 subnet_id=network_stack.public_subnet.subnet_id,
                                                                 security_group_ids=[
                                                                     cohort_notebook_security_group.attr_group_id
                                                                 ],
                                                                 role_arn=cohort_notebook_role.role_arn,
                                                                 lifecycle_config_name=cohort_notebook_lifecycle.attr_notebook_instance_lifecycle_config_name
                                                                 )
        cohort_notebook_instance.node.add_dependency(cohort_notebook_lifecycle)
