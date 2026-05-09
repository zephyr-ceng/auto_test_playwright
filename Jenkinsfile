pipeline {
    agent any

    options {
        timestamps()
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    parameters {
        string(name: 'HOST_PROJECT_PATH', defaultValue: '/workspace/Playwright_demo', description: 'Path of mounted project inside Jenkins container')
        string(name: 'PYTEST_ARGS', defaultValue: '-q', description: 'Extra pytest args, e.g. -q -k login')
    }

    environment {
        DOCKER_IMAGE = "playwright-demo-runner:${env.BUILD_NUMBER}"
        ALLURE_RESULTS = "reports/results"
    }

    stages {
        stage('Validate Mounted Project') {
            steps {
                sh '''
                    test -d "${HOST_PROJECT_PATH}"
                    test -f "${HOST_PROJECT_PATH}/Dockerfile"
                    test -d "${HOST_PROJECT_PATH}/tests"
                '''
            }
        }

        stage('Build Test Image') {
            steps {
                script {
                    sh """
                        docker build -t ${DOCKER_IMAGE} ${HOST_PROJECT_PATH}
                    """
                }
            }
        }

        stage('Run Pytest In Container') {
            steps {
                sh '''
                    docker run --rm \
                      --shm-size=1g \
                      -u root:root \
                      -v "${HOST_PROJECT_PATH}:/app" \
                      -w /app \
                      ${DOCKER_IMAGE} \
                      sh -c "rm -rf ${ALLURE_RESULTS} && mkdir -p ${ALLURE_RESULTS} && python -m pytest ${PYTEST_ARGS} --alluredir ${ALLURE_RESULTS}"
                '''
            }
        }

        stage('Collect Reports To Jenkins Workspace') {
            steps {
                sh '''
                    rm -rf reports
                    mkdir -p reports
                    if [ -d "${HOST_PROJECT_PATH}/reports/results" ]; then
                      cp -r "${HOST_PROJECT_PATH}/reports/results" reports/results
                    fi
                    if [ -d "${HOST_PROJECT_PATH}/reports/html" ]; then
                      cp -r "${HOST_PROJECT_PATH}/reports/html" reports/html
                    fi
                '''
            }
        }
    }

    post {
        always {
            allure([
                reportBuildPolicy: 'ALWAYS',
                results: [[path: "${ALLURE_RESULTS}"]]
            ])

            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true, fingerprint: true
        }
    }
}
