pipeline {
    agent any

    options {
        timestamps()
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
            }
        }
    }
}
