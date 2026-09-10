# GitLab mirror and Jenkins connection

GitHub is the canonical public portfolio repository. GitLab is an optional secondary mirror used to demonstrate a second source-control and CI environment without splitting ownership of the project.

## Add a GitLab mirror

1. Create an empty GitLab project named `production-reliability-incident-platform`.
2. Add the remote without embedding credentials:

   ```bash
   git remote add gitlab https://gitlab.com/USERNAME/production-reliability-incident-platform.git
   git push -u gitlab main
   ```

3. Protect `main` and require the quality, test, and build jobs in `.gitlab-ci.yml`.
4. Do not describe the GitLab pipeline as verified until the remote pipeline has passed.

## Connect Jenkins

Create a Jenkins Multibranch Pipeline using the canonical GitHub repository URL. Store all repository and GCP credentials in Jenkins Credentials. Never place access tokens in the Jenkinsfile, repository URL, environment example, logs, or screenshots.

The Jenkinsfile keeps deployment disabled by default. A cloud deployment requires the explicit `DEPLOY_TO_GCP` parameter and a configured `gcp-service-account` file credential.

