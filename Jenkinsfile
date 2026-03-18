pipeline {
    agent any
    
    environment {
        DOCKER_HUB_USER = "vakula2004" // Твій логін (або змініть на свій)
        IMAGE_NAME = "python-app"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        APP_NAMESPACE = "jenkins"
    }

    stages {
        stage('Checkout') {
            steps {
                // Jenkins сам бере код з SCM, якщо пайплайн налаштований через GitHub
                checkout scm 
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    echo "Building image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker build -t ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
                    sh "docker tag ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest"
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                // Використовуй Credentials ID 'docker-hub-creds', який треба створити в Jenkins
                withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', 
                                 usernameVariable: 'DOCKER_USER', 
                                 passwordVariable: 'DOCKER_PASS')]) {
                    sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                    sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest"
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    // Оновлюємо тег образу в нашому HA маніфесті
                    sh "sed -i 's|image:.*|image: ${DOCKER_HUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}|' python-app-ha.yaml"
                    
                    // Деплоїмо в кластер
                    sh "kubectl apply -f python-app-ha.yaml -n ${APP_NAMESPACE}"
                    
                    // Чекаємо успішного розгортання
                    sh "kubectl rollout status deployment/python-app -n ${APP_NAMESPACE}"
                }
            }
        }
    }
    
    post {
        always {
            sh "docker logout"
            cleanWs()
        }
    }
}pipeline {
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
