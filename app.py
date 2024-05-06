#!/usr/bin/env python3
import os
import aws_cdk as cdk
import constants
from network.infrastructure import Network
from db.infrastructure import Database
from api.infrastructure import Api
from notebook.infrastructure import Notebook


app = cdk.App()

# Network stack has no dependencies
cohort_network_stack = Network(
    app,
    constants.APP_NAME + "-Networking",
    vpc_cidr="10.0.0.0/16",
    public_subnet_cidr="10.0.1.0/24",
    private_subnet_1_cidr="10.0.2.0/24",
    private_subnet_2_cidr="10.0.3.0/24",
)

# Database stack has dependencies on Network stack: VPC ID, VPC Cidr, Public Subnet ID,
# both Private Subnets IDs, and the AZ Region Table
cohort_db_stack = Database(
    app,
    constants.APP_NAME + "Database",
    db_instance_size="db.r5.large",
    network_stack=cohort_network_stack
)
# Api stack has dependencies on Network stack: VPC ID, VPC Cidr, and both Private Subnet IDs
# Api stack has dependencies on Database stack: Neptune Cluster Endpoint
cohort_api_stack = Api(
    app,
    constants.APP_NAME + "Api",
    network_stack=cohort_network_stack,
    db_stack=cohort_db_stack
)
# Notebook stack has dependencies on Network stack: VPC ID, VPC Cidr, Public Subnet ID
# Notebook stack has dependencies on Database stack: Neptune Cluster Endpoint,Neptune Cluster Role, Neptune Cluster Port
cohort_notebook_stack = Notebook(
    app,
    constants.APP_NAME+"Notebook",
    network_stack=cohort_network_stack,
    db_stack=cohort_db_stack
)

app.synth()
