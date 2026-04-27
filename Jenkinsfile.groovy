pipeline {
    agent any

    options {
        timestamps()
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    environment {
        DOCKER_IMAGE = "playwright-demo:${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Test Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}", ".")
                }
            }
        }

        stage('Run Tests In Container') {
            steps {
                script {
                    docker.image("${DOCKER_IMAGE}").inside("-u root:root -v ${env.WORKSPACE}/reports:/app/reports") {
                        sh '''
                            set +e
                            mkdir -p reports/results
                            python -m pytest -q --alluredir reports/results
                            TEST_EXIT=$?
                            set -e

                            rm -rf reports/html
                            allure generate reports/results -o reports/html

                            exit $TEST_EXIT
                        '''
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true, fingerprint: true
            cleanWs deleteDirs: true, disableDeferredWipeout: true
        }
    }
}
