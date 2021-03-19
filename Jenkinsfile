node {

    // checkout latest
    checkout scm

    stage('build') {

        withCredentials([usernamePassword(credentialsId: 'pat',
                    usernameVariable: 'user',
                    passwordVariable: 'token')]){

            pypi_base=env.PYPI_BASE

            install_url = 'pip_index_url=' +
                          "https://user:token@" +
                           pypi_base + '/simple'

            pip_find_index = '--index-url=https://pypi.org/simple --extra-index-url=' + install_url

            pip_upload_url = 'pip_upload_url=https://' +
                         pypi_base + '/upload'

            // pass in environment vars
            environs = [ pip_find_index, pip_upload_url ]
            withEnv(environs){
                try {
                    sh '''
                        set +x -e

                        # clean if necessary
                        make clean

                        make commitno

                        # build wheel
                        make

                        # install locally
                        make update

                        # publish to artifact repo
                        make publish
                    '''


                   eggDir='aras_oslc_api.egg-info'
                   moduleName=eggValue(eggDir,'Name')
                   moduleVer=eggValue(eggDir,'Version')

                   buildPackage packageOpts: 'publish',
                       moduleName: "${moduleName}",
                       moduleVer: "${moduleVer}",
                       packageName: 'aras-oslc-api',
                       artifactRepoSource: 'pypy',
                       executeWebhook: 'true',
                       hookName: 'https://xxxx/deploy-oslc'

                }
                catch (Exception e) {
                   throw e
                }
                finally {
                    deleteDir()
                }
            }
        }
    }
}

