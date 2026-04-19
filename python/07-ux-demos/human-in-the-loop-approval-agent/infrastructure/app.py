# Copyright 2026 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

#!/usr/bin/env python3
import aws_cdk as cdk
from stack import OrderApprovalStack
import cdk_nag

app = cdk.App()
OrderApprovalStack(app, "OrderApprovalAgent")

cdk.Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(verbose=True))

app.synth()