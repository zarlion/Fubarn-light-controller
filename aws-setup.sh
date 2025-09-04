#!/bin/bash
# AWS CLI script to set up CodeBuild project for URBARN APK building
# Run this script if you want to use AWS CodeBuild instead of GitHub Actions

echo "🔶 Setting up AWS CodeBuild for URBARN APK building..."

# Variables - CUSTOMIZE THESE
GITHUB_REPO="https://github.com/YOUR_USERNAME/urbarn-light-controller.git"
S3_BUCKET="urbarn-apk-builds-$(date +%s)"  # Unique bucket name
PROJECT_NAME="urbarn-apk-builder"

echo "Creating S3 bucket for APK artifacts..."
aws s3 mb s3://$S3_BUCKET --region us-east-1

echo "Creating CodeBuild service role..."
cat > codebuild-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "codebuild.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name CodeBuildServiceRole-URBARN \
  --assume-role-policy-document file://codebuild-trust-policy.json

echo "Attaching policies to service role..."
aws iam attach-role-policy \
  --role-name CodeBuildServiceRole-URBARN \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

aws iam attach-role-policy \
  --role-name CodeBuildServiceRole-URBARN \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

echo "Creating CodeBuild project..."
cat > codebuild-project.json << EOF
{
  "name": "$PROJECT_NAME",
  "source": {
    "type": "GITHUB",
    "location": "$GITHUB_REPO",
    "buildspec": "buildspec.yml"
  },
  "artifacts": {
    "type": "S3",
    "location": "$S3_BUCKET",
    "path": "apks/",
    "packaging": "ZIP"
  },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/standard:5.0",
    "computeType": "BUILD_GENERAL1_MEDIUM"
  },
  "serviceRole": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/CodeBuildServiceRole-URBARN"
}
EOF

aws codebuild create-project --cli-input-json file://codebuild-project.json

echo "✅ AWS CodeBuild setup complete!"
echo ""
echo "🚀 To build your APK:"
echo "1. Go to AWS CodeBuild Console"
echo "2. Find project: $PROJECT_NAME"
echo "3. Click 'Start build'"
echo "4. Wait 15-20 minutes"
echo "5. Download APK from S3 bucket: $S3_BUCKET"
echo ""
echo "💰 Estimated cost per build: \$0.10-0.20"
echo "🆓 Free tier: 100 build minutes/month"

# Cleanup temp files
rm -f codebuild-trust-policy.json codebuild-project.json
