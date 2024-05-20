#!/bin/bash
set -e
PROFILE_NAME=tutorial
CLUSTER_NAME=tradechat-v1-Cluster-gCKiEfF6ACNl
REGION=us-west-2
LAUNCH_TYPE=EC2
ecs-cli configure profile --profile-name "$PROFILE_NAME" --access-key "$AWS_ACCESS_KEY_ID" --secret-key "$AWS_SECRET_ACCESS_KEY"
ecs-cli configure --cluster "$CLUSTER_NAME" --default-launch-type "$LAUNCH_TYPE" --region "$REGION" --config-name "$PROFILE_NAME"