# jfrog-pipeline-aws-ecr-sync

### Overview 
- For client consulting needed to provide an more robust option other than manually running docker tag and docker push add-hoc commands.
- Caveats: Did not have requisite access to the Art/jfrog or their AWS environment, but providing this as a possible future soltion to explore.

To automate the process of querying all JFrog repositories for Docker images and their tags, and then pushing those images to a specified AWS ECR repository:

1. **Authenticate** with JFrog and AWS ECR.
2. **List** all repositories in JFrog and find Docker images and their tags.
3. **Pull** each Docker image from JFrog.
4. **Tag** and **push** each Docker image to AWS ECR.

### Step-by-Step Plan

1. **Setup Authentication:**
   - Obtain credentials for JFrog (API key or username/password).
   - Configure AWS CLI with necessary permissions to access the ECR.

2. **Query JFrog Repositories:**
   - Use JFrog's REST API to get a list of repositories and their Docker images.

3. **Pull Docker Images:**
   - Use Docker commands to pull images from JFrog.

4. **Tag and Push to ECR:**
   - Retag the images for the target ECR and push them.

### Script Implementation

This script assumes you have `docker`, `awscli`, and `requests` (Python library) installed and configured properly.

```python
import subprocess
import requests
import json

# JFrog configuration
JFROG_URL = "https://your_jfrog_instance.jfrog.io"
JFROG_USER = "your_username"
JFROG_API_KEY = "your_api_key"
DOCKER_REPO_KEY = "docker-repo"  # The JFrog Docker repository key

# AWS ECR configuration
AWS_ECR_URL = "123456789012.dkr.ecr.region.amazonaws.com"
AWS_REGION = "your_aws_region"

# JFrog Authentication
jfrog_headers = {
    "Authorization": f"Basic {JFROG_API_KEY}",
    "Content-Type": "application/json"
}

def list_jfrog_repositories():
    """List all Docker repositories in JFrog."""
    url = f"{JFROG_URL}/artifactory/api/repositories?type=local"
    response = requests.get(url, headers=jfrog_headers)
    response.raise_for_status()
    return [repo['key'] for repo in response.json() if repo['packageType'] == 'docker']

def list_docker_images(repo):
    """List all Docker images and their tags in a specific JFrog repository."""
    url = f"{JFROG_URL}/artifactory/api/docker/{repo}/v2/_catalog"
    response = requests.get(url, headers=jfrog_headers)
    response.raise_for_status()
    return response.json().get('repositories', [])

def list_image_tags(repo, image):
    """List all tags for a specific Docker image in a JFrog repository."""
    url = f"{JFROG_URL}/artifactory/api/docker/{repo}/v2/{image}/tags/list"
    response = requests.get(url, headers=jfrog_headers)
    response.raise_for_status()
    return response.json().get('tags', [])

def docker_login_jfrog():
    """Docker login to JFrog."""
    login_cmd = f"docker login {JFROG_URL} -u {JFROG_USER} -p {JFROG_API_KEY}"
    subprocess.run(login_cmd, shell=True, check=True)

def docker_login_aws():
    """Docker login to AWS ECR."""
    login_cmd = f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {AWS_ECR_URL}"
    subprocess.run(login_cmd, shell=True, check=True)

def docker_pull_image(image, tag):
    """Pull Docker image from JFrog."""
    full_image_name = f"{JFROG_URL}/{DOCKER_REPO_KEY}/{image}:{tag}"
    pull_cmd = f"docker pull {full_image_name}"
    subprocess.run(pull_cmd, shell=True, check=True)

def docker_tag_image(image, tag):
    """Tag Docker image for AWS ECR."""
    jfrog_image_name = f"{JFROG_URL}/{DOCKER_REPO_KEY}/{image}:{tag}"
    ecr_image_name = f"{AWS_ECR_URL}/{image}:{tag}"
    tag_cmd = f"docker tag {jfrog_image_name} {ecr_image_name}"
    subprocess.run(tag_cmd, shell=True, check=True)
    return ecr_image_name

def docker_push_image(image_name):
    """Push Docker image to AWS ECR."""
    push_cmd = f"docker push {image_name}"
    subprocess.run(push_cmd, shell=True, check=True)

def migrate_images_to_ecr():
    """Main function to migrate all Docker images from JFrog to AWS ECR."""
    docker_login_jfrog()
    docker_login_aws()
    
    # List all repositories in JFrog
    repositories = list_jfrog_repositories()
    
    for repo in repositories:
        # List all Docker images in the repository
        images = list_docker_images(repo)
        
        for image in images:
            # List all tags for each image
            tags = list_image_tags(repo, image)
            
            for tag in tags:
                print(f"Migrating image {image}:{tag} from JFrog to AWS ECR...")
                docker_pull_image(image, tag)
                ecr_image_name = docker_tag_image(image, tag)
                docker_push_image(ecr_image_name)
                print(f"Successfully pushed {ecr_image_name} to AWS ECR.")

if __name__ == "__main__":
    migrate_images_to_ecr()
```

### Key Points:
1. **Authentication**: The script logs into both JFrog and AWS ECR using credentials provided.
2. **Image Management**: Pulls images from JFrog, retags them for ECR, and pushes them to AWS ECR.
3. **Error Handling**: It’s minimal here; you may want to add more detailed error handling and logging for robustness.
4. **Efficiency**: The script processes images one by one. For many images, consider optimizing or parallelizing.

### Prerequisites:
- Ensure you have Docker and AWS CLI configured and authenticated.
- Your user has permissions to list and pull images from JFrog and push to AWS ECR.


# To run the above Python script as a scheduled JFrog pipeline
- create a JFrog pipeline configuration that does the following:

1. **Defines the Resources** that the pipeline will use, such as the Git repository containing the script and any necessary environment variables.
2. **Defines the Steps** in the pipeline to install dependencies, execute the script, and handle any logging or notification.
3. **Schedules the Pipeline** to run at specified intervals.

### Pipeline Configuration Overview

JFrog Pipelines uses a YAML-based configuration. Here's how to set up the pipeline configuration file (`pipelines.yml`) and the necessary resources:

#### Step 1: Define Resources

1. **GitRepo Resource**: This is used to specify the Git repository containing your Python script.
2. **Environment Variables**: Use an `EnvVar` resource to define sensitive information like API keys, URLs, and credentials.

```yaml
resources:
  - name: docker-migration-script-repo
    type: GitRepo
    configuration:
      gitProvider: <your-git-provider-integration>
      path: your-username/your-repo-name  # The repository path in your Git provider
      branches:
        - main

  - name: jfrog-env-vars
    type: EnvVar
    configuration:
      variables:
        - name: JFROG_URL
          value: "https://your_jfrog_instance.jfrog.io"
        - name: JFROG_USER
          value: "your_username"
        - name: JFROG_API_KEY
          value: "your_api_key"
        - name: DOCKER_REPO_KEY
          value: "docker-repo"  # The JFrog Docker repository key
        - name: AWS_ECR_URL
          value: "123456789012.dkr.ecr.region.amazonaws.com"
        - name: AWS_REGION
          value: "your_aws_region"
```

#### Step 2: Define the Pipeline

1. **Pipeline Definition**: The pipeline will have one step to run the Python script.
2. **Scheduled Trigger**: The pipeline should have a scheduled trigger to run periodically (e.g., daily).

```yaml
pipelines:
  - name: docker-migration-pipeline
    steps:
      - name: migrate-docker-images
        type: Bash
        configuration:
          inputResources:
            - docker-migration-script-repo
            - jfrog-env-vars
          execution:
            onExecute:
              - echo "Starting Docker image migration..."
              - apt-get update && apt-get install -y python3 python3-pip
              - pip3 install requests boto3
              - python3 ./your-script-directory/migrate_images.py
```

#### Step 3: Define the Schedule Trigger

You can configure a scheduled trigger to run the pipeline at specific intervals.

```yaml
triggers:
  - name: schedule-docker-migration
    type: Scheduled
    configuration:
      cron: "0 0 * * *"  # This cron expression runs the pipeline daily at midnight
      pipeline: docker-migration-pipeline
```

#### Full Pipeline Configuration

Putting everything together, your `pipelines.yml` file should look like this:

```yaml
resources:
  - name: docker-migration-script-repo
    type: GitRepo
    configuration:
      gitProvider: <your-git-provider-integration>
      path: your-username/your-repo-name
      branches:
        - main

  - name: jfrog-env-vars
    type: EnvVar
    configuration:
      variables:
        - name: JFROG_URL
          value: "https://your_jfrog_instance.jfrog.io"
        - name: JFROG_USER
          value: "your_username"
        - name: JFROG_API_KEY
          value: "your_api_key"
        - name: DOCKER_REPO_KEY
          value: "docker-repo"
        - name: AWS_ECR_URL
          value: "123456789012.dkr.ecr.region.amazonaws.com"
        - name: AWS_REGION
          value: "your_aws_region"

pipelines:
  - name: docker-migration-pipeline
    steps:
      - name: migrate-docker-images
        type: Bash
        configuration:
          inputResources:
            - docker-migration-script-repo
            - jfrog-env-vars
          execution:
            onExecute:
              - echo "Starting Docker image migration..."
              - apt-get update && apt-get install -y python3 python3-pip
              - pip3 install requests boto3
              - python3 ./your-script-directory/migrate_images.py

triggers:
  - name: schedule-docker-migration
    type: Scheduled
    configuration:
      cron: "0 0 * * *"  # Daily at midnight
      pipeline: docker-migration-pipeline
```

### Steps to Implement

1. **Create the Git Repository**: Make sure your Python script (`migrate_images.py`) is committed to the specified Git repository.
2. **Create a Pipeline Source in JFrog Pipelines**:
   - Go to JFrog Pipelines and create a new pipeline source pointing to your repository with the `pipelines.yml` configuration.
3. **Configure Environment Variables**:
   - Ensure that sensitive variables like `JFROG_API_KEY` are securely managed, preferably using the JFrog Pipeline's `Secrets` feature.
4. **Run and Test the Pipeline**:
   - Manually trigger the pipeline to ensure everything works as expected before relying on the scheduled trigger.

This configuration should set up your JFrog pipeline to periodically migrate Docker images to your AWS ECR.