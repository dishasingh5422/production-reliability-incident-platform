pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        booleanParam(
            name: 'DEPLOY_TO_GCP',
            defaultValue: false,
            description: 'Deploy the verified image to Google Cloud Run'
        )
        string(name: 'GCP_PROJECT', defaultValue: '', description: 'Google Cloud project ID')
        string(name: 'GCP_REGION', defaultValue: 'asia-south1', description: 'Cloud Run region')
    }

    environment {
        VENV = '.jenkins-venv'
        COMPOSE_PROJECT_NAME = "reliability-ci-${BUILD_NUMBER}"
        APP_PORT = '18080'
        BASE_URL = 'http://127.0.0.1:18080'
        IMAGE_NAME = 'production-reliability-platform'
        GCP_SERVICE = 'production-reliability-platform'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git rev-parse HEAD > evidence/jenkins-commit-sha.txt'
            }
        }

        stage('Install') {
            steps {
                sh '''
                    python3.11 -m venv "$VENV"
                    "$VENV/bin/python" -m pip install --upgrade pip
                    "$VENV/bin/python" -m pip install -e '.[dev]'
                '''
            }
        }

        stage('Quality Gates') {
            parallel {
                stage('Lint') {
                    steps {
                        sh '"$VENV/bin/ruff" check .'
                    }
                }
                stage('Type Check') {
                    steps {
                        sh '"$VENV/bin/mypy" app'
                    }
                }
                stage('Security') {
                    steps {
                        sh '"$VENV/bin/bandit" -q -r app'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                sh '''
                    "$VENV/bin/pytest" \
                        --junitxml=evidence/junit.xml \
                        --cov=app \
                        --cov-report=term-missing \
                        --cov-report=xml:evidence/coverage.xml \
                        --cov-fail-under=80
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'evidence/junit.xml'
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'evidence/coverage.xml'
                }
            }
        }

        stage('Build Container') {
            steps {
                sh 'docker build --tag "$IMAGE_NAME:$BUILD_NUMBER" .'
            }
        }

        stage('Container Smoke Test') {
            steps {
                sh '''
                    docker compose up --build --detach
                    for attempt in $(seq 1 30); do
                        if curl --silent --fail "$BASE_URL/healthz" >/dev/null; then
                            break
                        fi
                        if [ "$attempt" -eq 30 ]; then
                            docker compose logs --no-color
                            exit 1
                        fi
                        sleep 2
                    done
                    ./scripts/smoke-test.sh
                '''
            }
        }

        stage('Publish and Deploy') {
            when {
                expression { return params.DEPLOY_TO_GCP }
            }
            steps {
                script {
                    if (!params.GCP_PROJECT?.trim()) {
                        error('GCP_PROJECT is required when DEPLOY_TO_GCP is enabled')
                    }
                }
                withCredentials([file(credentialsId: 'gcp-service-account', variable: 'GCP_KEY')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file="$GCP_KEY"
                        ./scripts/deploy-gcp.sh \
                            --project "$GCP_PROJECT" \
                            --region "$GCP_REGION" \
                            --commit "$(git rev-parse HEAD)"
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker compose logs --no-color > evidence/jenkins-compose.log 2>&1 || true'
            sh 'docker compose down --remove-orphans || true'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'evidence/jenkins-*.txt,evidence/jenkins-*.log'
        }
        success {
            echo 'All requested quality, test, build, and smoke-test stages passed.'
        }
        failure {
            echo 'Pipeline failed. Review archived evidence before retrying or deploying.'
        }
    }
}

