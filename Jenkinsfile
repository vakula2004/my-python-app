pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command: ["sleep"]
    args: ["99d"]
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  - name: git-tool
    # Используем образ с git для обновления манифестов
    image: alpine/git:latest
    command: ["cat"]
    tty: true
  volumes:
  - name: docker-config
    emptyDir: {}
'''
        }
    }

    environment {
        DOCKER_HUB_USER = "vakula2004"
        APP_NAME = "my-python-app"
        GIT_REPO = "github.com/vakula2004/my-python-app.git"
    }

    stages {
        stage('Checkout') {
            steps {
                git url: "https://${GIT_REPO}", 
                    credentialsId: 'github-token', 
                    branch: 'main'
            }
        }

        stage('Build & Push Image') {
            steps {
                container('kaniko') {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', 
                                     passwordVariable: 'DOCKER_PASS', 
                                     usernameVariable: 'DOCKER_USER')]) {
                        sh '''
                            printf '{"auths":{"https://index.docker.io/v1/":{"auth":"%s"}}}' \
                            $(echo -n "${DOCKER_USER}:${DOCKER_PASS}" | base64) > /kaniko/.docker/config.json
                            
                            /kaniko/executor --context . \
                                             --dockerfile Dockerfile \
                                             --destination ${DOCKER_HUB_USER}/${APP_NAME}:${BUILD_NUMBER} \
                                             --destination ${DOCKER_HUB_USER}/${APP_NAME}:latest
                        '''
                    }
                }
            }
        }

        stage('Update Git Manifests') {
            steps {
                container('git-tool') {
                    withCredentials([usernamePassword(credentialsId: 'github-token', 
                                     passwordVariable: 'GIT_PASS', 
                                     usernameVariable: 'GIT_USER')]) {
                        sh """
                            git config --global user.email "jenkins@vakula.dev"
                            git config --global user.name "Jenkins CI"
                            
                            # Меняем тег образа в YAML файле (используем sed)
                            sed -i "s|image: ${DOCKER_HUB_USER}/${APP_NAME}:.*|image: ${DOCKER_HUB_USER}/${APP_NAME}:${BUILD_NUMBER}|g" k8s/app.yaml
                            
                            git add k8s/app.yaml
                            git commit -m "image update to version ${BUILD_NUMBER} [skip ci]"
                            
                            # Пушим изменения обратно в репозиторий
                            git push https://${GIT_USER}:${GIT_PASS}@${GIT_REPO} HEAD:main
                        """
                    }
                }
            }
        }
    }
}
