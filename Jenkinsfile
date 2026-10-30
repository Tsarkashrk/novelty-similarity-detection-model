pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Unit tests') {
            steps {
                sh 'docker build --target test -t thesis-novelty:test-${BUILD_NUMBER} .'
                sh 'docker run --rm thesis-novelty:test-${BUILD_NUMBER} python -m unittest discover -s tests -v'
            }
        }
        stage('Build image') {
            steps {
                sh 'docker build --target runtime -t thesis-novelty:${BUILD_NUMBER} .'
                sh 'docker image inspect thesis-novelty:${BUILD_NUMBER} --format "{{.Id}}"'
                sh 'docker build --target api -t thesis-novelty-api:${BUILD_NUMBER} .'
            }
        }
        stage('Deploy test API') {
            steps {
                sh 'sh devops/deploy-local.sh thesis-novelty-api:${BUILD_NUMBER}'
            }
        }
    }
}
