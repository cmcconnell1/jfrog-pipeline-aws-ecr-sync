# This script assumes you have docker, awscli, and requests (Python library) installed and configured properly.

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