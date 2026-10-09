pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    triggers {
        // For GitHub webhook delivery, configure the GitHub hook trigger in Jenkins.
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and syntax check') {
            steps {
                sh 'python3 -m compileall -q app.py tests'
                sh 'docker build -t aceest-fitness:jenkins-${BUILD_NUMBER} .'
            }
        }

        stage('Unit tests in container') {
            steps {
                sh 'docker run --rm --entrypoint pytest aceest-fitness:jenkins-${BUILD_NUMBER} -q'
            }
        }
    }

    post {
        always {
            echo 'ACEest build finished. Review the stage results above.'
        }
        cleanup {
            sh 'docker image rm aceest-fitness:jenkins-${BUILD_NUMBER} || true'
        }
    }
}
