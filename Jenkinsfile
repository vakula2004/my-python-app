pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  dnsConfig:
    nameservers:
      - 1.1.1.1
      - 8.8.8.8
    options:
      - name: ndots
        value: "1"
  containers:
  - name: docker
    image: docker:24.0.6-dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
  # ДОБАВИЛИ ЭТОТ КОНТЕЙНЕР ДЛЯ HELM
  - name: helm-tool
    image: alpine/k8s:1.27.1
    command: ["cat"]
    tty: true
  - name: jnlp
    image: jenkins/inbound-agent:alpine
"""
        }
    }

    environment {
        DOCKER_HUB_USER = "vakula2004"
        IMAGE_NAME = "python-app"
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/vakula2004/my-python-app.git', branch: 'main'
            }
        }

        stage('Build, Test & Push') {
            steps {
                container('docker') {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', passwordVariable: 'PASS', usernameVariable: 'USER')]) {
                        sh '''
                            export DOCKER_HOST=tcp://localhost:2375
                            sleep 10
                            
                            docker build -t ${DOCKER_HUB_USER}/${IMAGE_NAME}:${BUILD_NUMBER} .
                            docker tag ${DOCKER_HUB_USER}/${IMAGE_NAME}:${BUILD_NUMBER} ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest
                            
                            docker run -d --name test-app -p 5000:5000 ${DOCKER_HUB_USER}/${IMAGE_NAME}:${BUILD_NUMBER}
                            sleep 10
                            docker exec test-app python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/health').read().decode())" | grep "UP"
                            
                            TEST_RESULT=$?
                            docker stop test-app && docker rm test-app
                            
                            if [ $TEST_RESULT -ne 0 ]; then
                                exit 1
                            fi
                            
                            echo $PASS | docker login -u $USER --password-stdin
                            docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:${BUILD_NUMBER}
                            docker push ${DOCKER_HUB_USER}/${IMAGE_NAME}:latest
                        '''
                    }
                }
            }
        }

        stage('Deploy with Helm') {
            steps {
                // ТЕПЕРЬ ИСПОЛЬЗУЕМ КОНТЕЙНЕР С HELM
                container('helm-tool') {
                    sh """
                        helm upgrade --install my-python-release ./python-app \
                            --set image.tag=${env.BUILD_NUMBER} \
                            --namespace jenkins
                    """
                }
            }
        }
    }
}
