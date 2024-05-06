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
    Stack,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    RemovalPolicy,
    aws_sam as sam,
    aws_s3 as s3,
    aws_s3_assets as s3_assets
)
from constructs import Construct
import os
import path


class Api(Stack):

    def __init__(self,
                 scope: Construct,
                 id_: str,
                 network_stack,
                 db_stack,
                 **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        # Create Lambda Security Group
        cohort_lambda_security_group = ec2.CfnSecurityGroup(self, "CohortLambdaSecurityGroup",
                                                            group_description="SG of Cohort API DB",
                                                            security_group_egress=[
                                                                ec2.CfnSecurityGroup.EgressProperty(
                                                                    ip_protocol="-1",
                                                                    cidr_ip=network_stack.vpc.cidr_block,
                                                                    from_port=0,
                                                                    to_port=65535
                                                                )
                                                            ],
                                                            security_group_ingress=[
                                                                ec2.CfnSecurityGroup.IngressProperty(
                                                                    ip_protocol="tcp",
                                                                    cidr_ip=network_stack.vpc.cidr_block,
                                                                    from_port=8182,
                                                                    to_port=8182
                                                                ),
                                                                ec2.CfnSecurityGroup.IngressProperty(
                                                                    ip_protocol="tcp",
                                                                    cidr_ip=network_stack.vpc.cidr_block,
                                                                    from_port=443,
                                                                    to_port=443
                                                                ),
                                                                ec2.CfnSecurityGroup.IngressProperty(
                                                                    ip_protocol="tcp",
                                                                    cidr_ip=network_stack.vpc.cidr_block,
                                                                    from_port=80,
                                                                    to_port=80
                                                                )
                                                            ],
                                                            vpc_id=network_stack.vpc.attr_vpc_id
                                                            )
        # Create Lambda Layer
        cohort_validation_layer = lambda_.LayerVersion(self, "CohortValidationLayer",
                                                       removal_policy=RemovalPolicy.DESTROY,
                                                       code=lambda_.Code.from_asset(
                                                           "./api/layers/validator.zip"),
                                                       compatible_runtimes=[lambda_.Runtime.PYTHON_3_8]
                                                       )

        # Upload lambda asset and create Player Put API
        cohort_s3_lambda_player_put_asset = s3_assets.Asset(self, "CohortPlayerPutLambdaCode",
                                                            path=os.path.join(os.getcwd(), \
                                                                              "./api/player/methods/put/player-put.zip")
                                                            )
        cohort_api_player_put = sam.CfnFunction(self, "CohortApiPlayerPut",
                                                code_uri=sam.CfnFunction.S3LocationProperty(
                                                    bucket=cohort_s3_lambda_player_put_asset.s3_bucket_name,
                                                    key=cohort_s3_lambda_player_put_asset.s3_object_key,
                                                ),
                                                timeout=3,
                                                handler="app.handler",
                                                runtime="python3.8",
                                                vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                    security_group_ids=[cohort_lambda_security_group.attr_group_id],
                                                    subnet_ids=[
                                                        network_stack.private_subnet_1.subnet_id,
                                                        network_stack.private_subnet_2.subnet_id
                                                    ]
                                                ),
                                                environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                    variables={
                                                        "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                    }
                                                ),
                                                events={
                                                    "API": sam.CfnFunction.EventSourceProperty(
                                                        properties=sam.CfnFunction.ApiEventProperty(
                                                            path="/data/player/{player}",
                                                            method="put"
                                                        ),
                                                        type="Api"
                                                    )
                                                },
                                                layers=[
                                                    cohort_validation_layer.layer_version_arn
                                                ]
                                                )
        cohort_api_player_put.node.add_dependency(cohort_s3_lambda_player_put_asset)

        # Upload lambda asset and create Player Post API
        cohort_s3_lambda_player_post_asset = s3_assets.Asset(self, "CohortPlayerPostLambdaCode",
                                                             path=os.path.join(os.getcwd(), \
                                                                               "./api/player/methods/post/player-post.zip")
                                                             )

        cohort_api_player_post = sam.CfnFunction(self, "CohortApiPlayerPost",
                                                 code_uri=sam.CfnFunction.S3LocationProperty(
                                                     bucket=cohort_s3_lambda_player_post_asset.s3_bucket_name,
                                                     key=cohort_s3_lambda_player_post_asset.s3_object_key,
                                                 ),
                                                 timeout=3,
                                                 handler="app.handler",
                                                 runtime="python3.8",
                                                 vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                     security_group_ids=[cohort_lambda_security_group.attr_group_id],
                                                     subnet_ids=[
                                                         network_stack.private_subnet_1.subnet_id,
                                                         network_stack.private_subnet_2.subnet_id
                                                     ]
                                                 ),
                                                 environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                     variables={
                                                         "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                     }
                                                 ),
                                                 events={
                                                     "API": sam.CfnFunction.EventSourceProperty(
                                                         properties=sam.CfnFunction.ApiEventProperty(
                                                             path="/data/player/{player}",
                                                             method="post"
                                                         ),
                                                         type="Api"
                                                     )
                                                 },
                                                 layers=[
                                                     cohort_validation_layer.layer_version_arn
                                                 ]
                                                 )
        cohort_api_player_post.node.add_dependency(cohort_s3_lambda_player_post_asset)

        # Upload lambda asset and create Player Get API
        cohort_s3_lambda_player_get_asset = s3_assets.Asset(self, "CohortPlayerGetLambdaCode",
                                                            path=os.path.join(os.getcwd(), \
                                                                              "./api/player/methods/get/player-get.zip")
                                                            )

        cohort_api_player_get = sam.CfnFunction(self, "CohortApiPlayerGet",
                                                code_uri=sam.CfnFunction.S3LocationProperty(
                                                    bucket=cohort_s3_lambda_player_get_asset.s3_bucket_name,
                                                    key=cohort_s3_lambda_player_get_asset.s3_object_key,
                                                ),
                                                timeout=3,
                                                handler="app.handler",
                                                runtime="python3.8",
                                                vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                    security_group_ids=[cohort_lambda_security_group.attr_group_id],
                                                    subnet_ids=[
                                                        network_stack.private_subnet_1.subnet_id,
                                                        network_stack.private_subnet_2.subnet_id
                                                    ]
                                                ),
                                                environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                    variables={
                                                        "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                    }
                                                ),
                                                events={
                                                    "API": sam.CfnFunction.EventSourceProperty(
                                                        properties=sam.CfnFunction.ApiEventProperty(
                                                            path="/data/player/{player}",
                                                            method="get"
                                                        ),
                                                        type="Api"
                                                    )
                                                },
                                                layers=[
                                                    cohort_validation_layer.layer_version_arn
                                                ]
                                                )

        cohort_api_player_get.node.add_dependency(cohort_s3_lambda_player_get_asset)

        # Upload lambda asset and create Player Delete Api

        cohort_s3_lambda_player_delete_asset = s3_assets.Asset(self, "CohortPlayerDeleteLambdaCode",
                                                               path=os.path.join(os.getcwd(), \
                                                                                 "./api/player/methods/delete/player-delete.zip")
                                                               )

        cohort_api_player_delete = sam.CfnFunction(self, "CohortApiPlayerDelete",
                                                   code_uri=sam.CfnFunction.S3LocationProperty(
                                                       bucket=cohort_s3_lambda_player_delete_asset.s3_bucket_name,
                                                       key=cohort_s3_lambda_player_delete_asset.s3_object_key,
                                                   ),
                                                   timeout=3,
                                                   handler="app.handler",
                                                   runtime="python3.8",
                                                   vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                       security_group_ids=[cohort_lambda_security_group.attr_group_id],
                                                       subnet_ids=[
                                                           network_stack.private_subnet_1.subnet_id,
                                                           network_stack.private_subnet_2.subnet_id
                                                       ]
                                                   ),
                                                   environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                       variables={
                                                           "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                       }
                                                   ),
                                                   events={
                                                       "API": sam.CfnFunction.EventSourceProperty(
                                                           properties=sam.CfnFunction.ApiEventProperty(
                                                               path="/data/player/{player}",
                                                               method="delete"
                                                           ),
                                                           type="Api"
                                                       )
                                                   },
                                                   layers=[
                                                       cohort_validation_layer.layer_version_arn
                                                   ]
                                                   )
        cohort_api_player_delete.node.add_dependency(cohort_s3_lambda_player_delete_asset)

        # Upload lambda asset and create Campaign Put Api
        cohort_s3_lambda_campaign_put_asset = s3_assets.Asset(self, "CohortCampaignPutLambdaCode",
                                                              path=os.path.join(os.getcwd(), \
                                                                                "./api/campaign/methods/put/campaign-put.zip")
                                                              )

        cohort_api_campaign_put = sam.CfnFunction(self, "CohortApiCampaignPut",
                                                  code_uri=sam.CfnFunction.S3LocationProperty(
                                                      bucket=cohort_s3_lambda_campaign_put_asset.s3_bucket_name,
                                                      key=cohort_s3_lambda_campaign_put_asset.s3_object_key,
                                                  ),
                                                  timeout=3,
                                                  handler="app.handler",
                                                  runtime="python3.8",
                                                  vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                      security_group_ids=[cohort_lambda_security_group.attr_group_id],
                                                      subnet_ids=[
                                                          network_stack.private_subnet_1.subnet_id,
                                                          network_stack.private_subnet_2.subnet_id
                                                      ]
                                                  ),
                                                  environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                      variables={
                                                          "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                      }
                                                  ),
                                                  events={
                                                      "API": sam.CfnFunction.EventSourceProperty(
                                                          properties=sam.CfnFunction.ApiEventProperty(
                                                              path="/data/campaign/{campaign}",
                                                              method="put"
                                                          ),
                                                          type="Api"
                                                      )
                                                  },
                                                  layers=[
                                                      cohort_validation_layer.layer_version_arn
                                                  ]
                                                  )
        cohort_api_campaign_put.node.add_dependency(cohort_s3_lambda_campaign_put_asset)

        # Upload lambda asset and create Campaign Post Api
        cohort_s3_lambda_campaign_post_asset = s3_assets.Asset(self, "CohortCampaignPostLambdaCode",
                                                               path=os.path.join(os.getcwd(), \
                                                                                 "./api/campaign/methods/post/campaign-post.zip")
                                                               )

        cohort_api_campaign_post = sam.CfnFunction(self, "CohortApiCampaignPost",
                                                   code_uri=sam.CfnFunction.S3LocationProperty(
                                                       bucket=cohort_s3_lambda_campaign_post_asset.s3_bucket_name,
                                                       key=cohort_s3_lambda_campaign_post_asset.s3_object_key,
                                                   ),
                                                   timeout=3,
                                                   handler="app.handler",
                                                   runtime="python3.8",
                                                   vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                       security_group_ids=[cohort_lambda_security_group.attr_group_id],
                                                       subnet_ids=[
                                                           network_stack.private_subnet_1.subnet_id,
                                                           network_stack.private_subnet_2.subnet_id
                                                       ]
                                                   ),
                                                   environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                       variables={
                                                           "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                       }
                                                   ),
                                                   events={
                                                       "API": sam.CfnFunction.EventSourceProperty(
                                                           properties=sam.CfnFunction.ApiEventProperty(
                                                               path="/data/campaign/{campaign}",
                                                               method="post"
                                                           ),
                                                           type="Api"
                                                       )
                                                   },
                                                   layers=[
                                                       cohort_validation_layer.layer_version_arn
                                                   ]
                                                   )
        cohort_api_campaign_post.node.add_dependency(cohort_s3_lambda_campaign_post_asset)

        # Upload lambda asset and create Campaign Delete Api
        cohort_s3_lambda_campaign_delete_asset = s3_assets.Asset(self, "CohortCampaignDeleteLambdaCode",
                                                                 path=os.path.join(os.getcwd(), \
                                                                                   "./api/campaign/methods/delete/campaign-delete.zip")
                                                                 )

        cohort_api_campaign_delete = sam.CfnFunction(self, "CohortApiCampaignDelete",
                                                     code_uri=sam.CfnFunction.S3LocationProperty(
                                                         bucket=cohort_s3_lambda_campaign_delete_asset.s3_bucket_name,
                                                         key=cohort_s3_lambda_campaign_delete_asset.s3_object_key,
                                                     ),
                                                     timeout=3,
                                                     handler="app.handler",
                                                     runtime="python3.8",
                                                     vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                         security_group_ids=[
                                                             cohort_lambda_security_group.attr_group_id],
                                                         subnet_ids=[
                                                             network_stack.private_subnet_1.subnet_id,
                                                             network_stack.private_subnet_2.subnet_id
                                                         ]
                                                     ),
                                                     environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                         variables={
                                                             "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                         }
                                                     ),
                                                     events={
                                                         "API": sam.CfnFunction.EventSourceProperty(
                                                             properties=sam.CfnFunction.ApiEventProperty(
                                                                 path="/data/campaign/{campaign}",
                                                                 method="delete"
                                                             ),
                                                             type="Api"
                                                         )
                                                     },
                                                     layers=[
                                                         cohort_validation_layer.layer_version_arn
                                                     ]
                                                     )
        cohort_api_campaign_delete.node.add_dependency(cohort_s3_lambda_campaign_delete_asset)

        # Upload lambda asset and create Player Interaction Api

        cohort_s3_lambda_player_interaction_put_asset = s3_assets.Asset(self, "CohortPlayerInteractionPutLambdaCode",
                                                                        path=os.path.join(os.getcwd(), \
                                                                                          "./api/player/interaction/methods/put/interaction-put.zip")
                                                                        )

        cohort_api_player_interaction_put = sam.CfnFunction(self, "CohortApiPlayerInteractionPut",
                                                            code_uri=sam.CfnFunction.S3LocationProperty(
                                                                bucket=cohort_s3_lambda_player_interaction_put_asset.s3_bucket_name,
                                                                key=cohort_s3_lambda_player_interaction_put_asset.s3_object_key,
                                                            ),
                                                            timeout=3,
                                                            handler="app.handler",
                                                            runtime="python3.8",
                                                            vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                                security_group_ids=[
                                                                    cohort_lambda_security_group.attr_group_id],
                                                                subnet_ids=[
                                                                    network_stack.private_subnet_1.subnet_id,
                                                                    network_stack.private_subnet_2.subnet_id
                                                                ]
                                                            ),
                                                            environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                                variables={
                                                                    "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                                }
                                                            ),
                                                            events={
                                                                "API": sam.CfnFunction.EventSourceProperty(
                                                                    properties=sam.CfnFunction.ApiEventProperty(
                                                                        path="/data/player/{player}/interaction",
                                                                        method="put"
                                                                    ),
                                                                    type="Api"
                                                                )
                                                            },
                                                            layers=[
                                                                cohort_validation_layer.layer_version_arn
                                                            ]
                                                            )
        cohort_api_player_interaction_put.node.add_dependency(cohort_s3_lambda_player_interaction_put_asset)

        # Upload lambda asset and create Player Interaction Get Api

        cohort_s3_lambda_player_interaction_get_asset = s3_assets.Asset(self, "CohortPlayerInteractionGetLambdaCode",
                                                                        path=os.path.join(os.getcwd(), \
                                                                                          "./api/player/interaction/methods/get/interaction-get.zip")
                                                                        )

        cohort_api_player_interaction_get = sam.CfnFunction(self, "CohortApiPlayerInteractionGet",
                                                            code_uri=sam.CfnFunction.S3LocationProperty(
                                                                bucket=cohort_s3_lambda_player_interaction_get_asset.s3_bucket_name,
                                                                key=cohort_s3_lambda_player_interaction_get_asset.s3_object_key,
                                                            ),
                                                            timeout=3,
                                                            handler="app.handler",
                                                            runtime="python3.8",
                                                            vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                                security_group_ids=[
                                                                    cohort_lambda_security_group.attr_group_id],
                                                                subnet_ids=[
                                                                    network_stack.private_subnet_1.subnet_id,
                                                                    network_stack.private_subnet_2.subnet_id
                                                                ]
                                                            ),
                                                            environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                                variables={
                                                                    "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                                }
                                                            ),
                                                            events={
                                                                "API": sam.CfnFunction.EventSourceProperty(
                                                                    properties=sam.CfnFunction.ApiEventProperty(
                                                                        path="/data/player/{player}/interaction",
                                                                        method="get"
                                                                    ),
                                                                    type="Api"
                                                                )
                                                            },
                                                            layers=[
                                                                cohort_validation_layer.layer_version_arn
                                                            ]
                                                            )
        cohort_api_player_interaction_get.node.add_dependency(cohort_s3_lambda_player_interaction_get_asset)

        # Upload lambda asset and create Player Relationship Get Api

        cohort_s3_lambda_player_relationship_get_asset = s3_assets.Asset(self, "CohortPlayerRelationshipGetLambdaCode",
                                                                         path=os.path.join(os.getcwd(), \
                                                                                           "./api/player/relationship/methods/get/relationship-get.zip")
                                                                         )

        cohort_api_player_relationship_get = sam.CfnFunction(self, "CohortApiPlayerRelationshipGet",
                                                             code_uri=sam.CfnFunction.S3LocationProperty(
                                                                 bucket=cohort_s3_lambda_player_relationship_get_asset.s3_bucket_name,
                                                                 key=cohort_s3_lambda_player_relationship_get_asset.s3_object_key,
                                                             ),
                                                             timeout=3,
                                                             handler="app.handler",
                                                             runtime="python3.8",
                                                             vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                                 security_group_ids=[
                                                                     cohort_lambda_security_group.attr_group_id],
                                                                 subnet_ids=[
                                                                     network_stack.private_subnet_1.subnet_id,
                                                                     network_stack.private_subnet_2.subnet_id
                                                                 ]
                                                             ),
                                                             environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                                 variables={
                                                                     "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                                 }
                                                             ),
                                                             events={
                                                                 "API": sam.CfnFunction.EventSourceProperty(
                                                                     properties=sam.CfnFunction.ApiEventProperty(
                                                                         path="/data/player/{player}/relationship",
                                                                         method="get"
                                                                     ),
                                                                     type="Api"
                                                                 )
                                                             },
                                                             layers=[
                                                                 cohort_validation_layer.layer_version_arn
                                                             ]
                                                             )
        cohort_api_player_relationship_get.node.add_dependency(cohort_s3_lambda_player_relationship_get_asset)

        # Upload lambda asset and create Prediction Collaborative Filter Api

        cohort_s3_lambda_prediction_collaborative_filter_get_asset = s3_assets.Asset(self,
                                                                                     "CohortPredictionCollaborativeFilterGetLambdaCode",
                                                                                     path=os.path.join(os.getcwd(), \
                                                                                                       "./api/prediction/collaborativeFilter/methods/get/collaborativefilter-get.zip")
                                                                                     )

        cohort_api_prediction_collaborative_filter = sam.CfnFunction(self, "CohortApiPredictionCollabFilter",
                                                                     code_uri=sam.CfnFunction.S3LocationProperty(
                                                                         bucket=cohort_s3_lambda_prediction_collaborative_filter_get_asset.s3_bucket_name,
                                                                         key=cohort_s3_lambda_prediction_collaborative_filter_get_asset.s3_object_key,
                                                                     ),
                                                                     timeout=3,
                                                                     handler="app.handler",
                                                                     runtime="python3.8",
                                                                     vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                                         security_group_ids=[
                                                                             cohort_lambda_security_group.attr_group_id],
                                                                         subnet_ids=[
                                                                             network_stack.private_subnet_1.subnet_id,
                                                                             network_stack.private_subnet_2.subnet_id
                                                                         ]
                                                                     ),
                                                                     environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                                         variables={
                                                                             "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                                         }
                                                                     ),
                                                                     events={
                                                                         "API": sam.CfnFunction.EventSourceProperty(
                                                                             properties=sam.CfnFunction.ApiEventProperty(
                                                                                 path="/prediction/collaborativeFilter",
                                                                                 method="get"
                                                                             ),
                                                                             type="Api"
                                                                         )
                                                                     },
                                                                     layers=[
                                                                         cohort_validation_layer.layer_version_arn
                                                                     ]
                                                                     )
        cohort_api_prediction_collaborative_filter.node.add_dependency(
            cohort_s3_lambda_prediction_collaborative_filter_get_asset)

        # Upload lambda asset and create Triadic Closure Get Api

        cohort_s3_lambda_prediction_triadic_closure_get_asset = s3_assets.Asset(self,
                                                                                "CohortPredictionTriadicClosureGetLambdaCode",
                                                                                path=os.path.join(os.getcwd(), \
                                                                                    "./api/prediction/triadicClosure/methods/get/triadicclosure-get.zip")
                                                                                )

        cohort_api_prediction_triadic_closure = sam.CfnFunction(self, "CohortApiPredictionTriadicClosureGet",
                                                                code_uri=sam.CfnFunction.S3LocationProperty(
                                                                    bucket=cohort_s3_lambda_prediction_triadic_closure_get_asset.s3_bucket_name,
                                                                    key=cohort_s3_lambda_prediction_triadic_closure_get_asset.s3_object_key,
                                                                ),
                                                                timeout=3,
                                                                handler="app.handler",
                                                                runtime="python3.8",
                                                                vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                                    security_group_ids=[
                                                                        cohort_lambda_security_group.attr_group_id],
                                                                    subnet_ids=[
                                                                        network_stack.private_subnet_1.subnet_id,
                                                                        network_stack.private_subnet_2.subnet_id
                                                                    ]
                                                                ),
                                                                environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                                    variables={
                                                                        "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                                    }
                                                                ),
                                                                events={
                                                                    "API": sam.CfnFunction.EventSourceProperty(
                                                                        properties=sam.CfnFunction.ApiEventProperty(
                                                                            path="/prediction/triadicClosure",
                                                                            method="get"
                                                                        ),
                                                                        type="Api"
                                                                    )
                                                                },
                                                                layers=[
                                                                    cohort_validation_layer.layer_version_arn
                                                                ]
                                                                )
        cohort_api_prediction_triadic_closure.node.add_dependency(cohort_s3_lambda_prediction_triadic_closure_get_asset)

        # Upload lambda asset and create Bad Actors Get Api

        cohort_s3_lambda_prediction_bad_actors_get_asset = s3_assets.Asset(self,
                                                                           "CohortPredictionBadActorsGetLambdaCode",
                                                                           path=os.path.join(os.getcwd(), \
                                                                                             "./api/prediction/badActors/methods/get/badactors-get.zip")
                                                                           )

        cohort_api_prediction_bad_actors = sam.CfnFunction(self, "CohortApiPredictionBadActorsGet",
                                                           code_uri=sam.CfnFunction.S3LocationProperty(
                                                               bucket=cohort_s3_lambda_prediction_bad_actors_get_asset.s3_bucket_name,
                                                               key=cohort_s3_lambda_prediction_bad_actors_get_asset.s3_object_key,
                                                           ),
                                                           timeout=3,
                                                           handler="app.handler",
                                                           runtime="python3.8",
                                                           vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                               security_group_ids=[
                                                                   cohort_lambda_security_group.attr_group_id],
                                                               subnet_ids=[
                                                                   network_stack.private_subnet_1.subnet_id,
                                                                   network_stack.private_subnet_2.subnet_id
                                                               ]
                                                           ),
                                                           environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                               variables={
                                                                   "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                               }
                                                           ),
                                                           events={
                                                               "API": sam.CfnFunction.EventSourceProperty(
                                                                   properties=sam.CfnFunction.ApiEventProperty(
                                                                       path="/prediction/badActors",
                                                                       method="get"
                                                                   ),
                                                                   type="Api"
                                                               )
                                                           },
                                                           layers=[
                                                               cohort_validation_layer.layer_version_arn
                                                           ]
                                                           )
        cohort_api_prediction_bad_actors.node.add_dependency(cohort_s3_lambda_prediction_bad_actors_get_asset)

        # Upload lambda asset and create Related Users Get Api
        cohort_s3_lambda_prediction_related_users_get_asset = s3_assets.Asset(self,
                                                                              "CohortPredictionRelatedUsersGetLambdaCode",
                                                                              path=os.path.join(os.getcwd(), \
                                                                                                "./api/prediction/relatedUsers/methods/get/relatedusers-get.zip")
                                                                              )

        cohort_api_prediction_related_users = sam.CfnFunction(self, "CohortApiPredictionRelatedUsersGet",
                                                              code_uri=sam.CfnFunction.S3LocationProperty(
                                                                  bucket=cohort_s3_lambda_prediction_related_users_get_asset.s3_bucket_name,
                                                                  key=cohort_s3_lambda_prediction_related_users_get_asset.s3_object_key,
                                                              ),
                                                              timeout=3,
                                                              handler="app.handler",
                                                              runtime="python3.8",
                                                              vpc_config=sam.CfnFunction.VpcConfigProperty(
                                                                  security_group_ids=[
                                                                      cohort_lambda_security_group.attr_group_id],
                                                                  subnet_ids=[
                                                                      network_stack.private_subnet_1.subnet_id,
                                                                      network_stack.private_subnet_2.subnet_id
                                                                  ]
                                                              ),
                                                              environment=sam.CfnFunction.FunctionEnvironmentProperty(
                                                                  variables={
                                                                      "NeptuneEndpoint": db_stack.neptune_cluster.attr_endpoint
                                                                  }
                                                              ),
                                                              events={
                                                                  "API": sam.CfnFunction.EventSourceProperty(
                                                                      properties=sam.CfnFunction.ApiEventProperty(
                                                                          path="/prediction/relatedUsers",
                                                                          method="get"
                                                                      ),
                                                                      type="Api"
                                                                  )
                                                              },
                                                              layers=[
                                                                  cohort_validation_layer.layer_version_arn
                                                              ]
                                                              )
        cohort_api_prediction_related_users.node.add_dependency(cohort_s3_lambda_prediction_related_users_get_asset)
