pipeline {
    agent any
    
    environment {
        DOCKER_HUB_USER = "vakula2004"
        IMAGE_NAME = "python-app"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/vakula2004/my-python-app.git'
            }
        }

        stage('Docker Build & Push') {
            steps {
                script {
                    // Тобі треба буде додати Docker Hub Credentials у Jenkins
                    sh "docker build -t ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
                    sh "docker login -u ${DOCKER_HUB_USER} -p ${DOCKER_PASSWORD}"
                    sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Deploy to K8s') {
            steps {
                script {
                    // Оновлюємо образ у маніфесті та застосовуємо його
                    sh "sed -i 's|image:.*|image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|' python-app-ha.yaml"
                    sh "kubectl apply -f python-app-ha.yaml"
                }
            }
        }
    }
}
