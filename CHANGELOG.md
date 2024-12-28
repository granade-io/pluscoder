# [2.5.0-rc.5](https://gitlab.com/codematos/pluscoder/compare/v2.5.0-rc.4...v2.5.0-rc.5) (2024-12-28)


### Features

* add --silent flag to hide logs ([8961a9e](https://gitlab.com/codematos/pluscoder/commit/8961a9eca6df12a9d8ad6f120ebf5f8a249aa036))

# [2.5.0-rc.4](https://gitlab.com/codematos/pluscoder/compare/v2.5.0-rc.3...v2.5.0-rc.4) (2024-12-12)


### Features

* now chat history can be preserved between agents conversations ([65c7db3](https://gitlab.com/codematos/pluscoder/commit/65c7db3291ee86937b05260ff820a5ec7d963949))

# [2.5.0-rc.3](https://gitlab.com/codematos/pluscoder/compare/v2.5.0-rc.2...v2.5.0-rc.3) (2024-12-12)


### Features

* agent suggestions ([508eb87](https://gitlab.com/codematos/pluscoder/commit/508eb8724a1e62630f179aa358a2e67eba97274f))
* agents can now query the codebase using vector db with --embedding_model ([ce9ca59](https://gitlab.com/codematos/pluscoder/commit/ce9ca594bb4fe93ba0fdc58ed9453a0423e2af70))
* new --repo_include_only regex to include specific files when running agents ([c2adc53](https://gitlab.com/codematos/pluscoder/commit/c2adc53c5c4c4e96af0dd72326789668a434de09))
* now indexing detects if file were created/updated/removed at start of pluscoder ([7fce8ed](https://gitlab.com/codematos/pluscoder/commit/7fce8ed82c181d0c8d1ecbb2272a41b2a4475ab4))

# [2.5.0-rc.2](https://gitlab.com/codematos/pluscoder/compare/v2.5.0-rc.1...v2.5.0-rc.2) (2024-12-01)


### Performance Improvements

* now stale content is marked as stale for improving agent code suggestions ([c26e226](https://gitlab.com/codematos/pluscoder/commit/c26e226aaa9b599d90781fd12c8b2f79e1bfab7f))

# [2.5.0-rc.1](https://gitlab.com/codematos/pluscoder/compare/v2.4.0...v2.5.0-rc.1) (2024-11-29)


### Bug Fixes

* /undo now removes last commit along messages until last user message is removed ([3fcb091](https://gitlab.com/codematos/pluscoder/commit/3fcb091d37b9c7e6f06e689787fad53bd0da2545))


### Features

* new --task_list arg to pass a json string or file for running task list with orchestrator ([4a3aa58](https://gitlab.com/codematos/pluscoder/commit/4a3aa58bdf8555a067fb0b29149a1382ecb78261))

# [2.4.0](https://gitlab.com/codematos/pluscoder/compare/v2.3.0...v2.4.0) (2024-11-18)


### Bug Fixes

* now cli extra args are being properly ignored ([d791932](https://gitlab.com/codematos/pluscoder/commit/d791932f34461c7480405d5a322b4c1a7b529a2e))
* now environment variables are used for models instead of config values ([78778f9](https://gitlab.com/codematos/pluscoder/commit/78778f97d7d0ce9c57240d35968fb3ba10931b96))
* token validation at start and backend api ([99e5630](https://gitlab.com/codematos/pluscoder/commit/99e5630067144a45bf11ca7b03a2b237483cece9))


### Features

* added ~/.config/pluscoder/vars.env to manage global credentials ([46f5f89](https://gitlab.com/codematos/pluscoder/commit/46f5f89ccd62bca0c067597105221f406fa91226))
* added exponential backoff on errors related to llm endpoint ([299e861](https://gitlab.com/codematos/pluscoder/commit/299e861b1ba9c73299812f16ee6311e5fd6a0145))
* added vertex ai support through gcloud cli ([cb94f0d](https://gitlab.com/codematos/pluscoder/commit/cb94f0df5fd9947dbe8638b593a4075001d9cf64))
* new --repository and --source_branch configs to clone a repo before running pluscoder, --repository also accepts a git path ([80c5202](https://gitlab.com/codematos/pluscoder/commit/80c5202a0f41aa6476173fe3b9f9054d97430307))
* new global configuration yaml for reusable configs cross project. Check --show_config to see where its located ([7b1447a](https://gitlab.com/codematos/pluscoder/commit/7b1447a45f4440b9ab4d9938c4c390cc02c750b6))
* version display at start ([ad43b8f](https://gitlab.com/codematos/pluscoder/commit/ad43b8fd76c75734aca1ed60a44f864df07f113a))

# [2.4.0-rc.1](https://gitlab.com/codematos/pluscoder/compare/v2.3.0...v2.4.0-rc.1) (2024-11-18)


### Bug Fixes

* now cli extra args are being properly ignored ([d791932](https://gitlab.com/codematos/pluscoder/commit/d791932f34461c7480405d5a322b4c1a7b529a2e))
* now environment variables are used for models instead of config values ([78778f9](https://gitlab.com/codematos/pluscoder/commit/78778f97d7d0ce9c57240d35968fb3ba10931b96))
* token validation at start and backend api ([99e5630](https://gitlab.com/codematos/pluscoder/commit/99e5630067144a45bf11ca7b03a2b237483cece9))


### Features

* added ~/.config/pluscoder/vars.env to manage global credentials ([46f5f89](https://gitlab.com/codematos/pluscoder/commit/46f5f89ccd62bca0c067597105221f406fa91226))
* added exponential backoff on errors related to llm endpoint ([299e861](https://gitlab.com/codematos/pluscoder/commit/299e861b1ba9c73299812f16ee6311e5fd6a0145))
* added vertex ai support through gcloud cli ([cb94f0d](https://gitlab.com/codematos/pluscoder/commit/cb94f0df5fd9947dbe8638b593a4075001d9cf64))
* new --repository and --source_branch configs to clone a repo before running pluscoder, --repository also accepts a git path ([80c5202](https://gitlab.com/codematos/pluscoder/commit/80c5202a0f41aa6476173fe3b9f9054d97430307))
* new global configuration yaml for reusable configs cross project. Check --show_config to see where its located ([7b1447a](https://gitlab.com/codematos/pluscoder/commit/7b1447a45f4440b9ab4d9938c4c390cc02c750b6))
* version display at start ([ad43b8f](https://gitlab.com/codematos/pluscoder/commit/ad43b8fd76c75734aca1ed60a44f864df07f113a))

# [2.2.0-rc.4](https://gitlab.com/codematos/pluscoder/compare/v2.2.0-rc.3...v2.2.0-rc.4) (2024-11-18)


### Bug Fixes

* now environment variables are used for models instead of config values ([78778f9](https://gitlab.com/codematos/pluscoder/commit/78778f97d7d0ce9c57240d35968fb3ba10931b96))

# [2.2.0-rc.3](https://gitlab.com/codematos/pluscoder/compare/v2.2.0-rc.2...v2.2.0-rc.3) (2024-11-17)


### Bug Fixes

* token validation at start and backend api ([99e5630](https://gitlab.com/codematos/pluscoder/commit/99e5630067144a45bf11ca7b03a2b237483cece9))

# [2.2.0-rc.2](https://gitlab.com/codematos/pluscoder/compare/v2.2.0-rc.1...v2.2.0-rc.2) (2024-11-13)


### Features

* version display at start ([ad43b8f](https://gitlab.com/codematos/pluscoder/commit/ad43b8fd76c75734aca1ed60a44f864df07f113a))

# [2.3.0](https://gitlab.com/codematos/pluscoder/compare/v2.2.0...v2.3.0) (2024-11-06)

### Bug Fixes

* broken --no-init flags now is working again ([070b943](https://gitlab.com/codematos/pluscoder/commit/070b94349d5fd64ef0bfce566fb0bb04c5d9abdc))
* error handling when starting in a non-git folder ([418235c](https://gitlab.com/codematos/pluscoder/commit/418235c3b8436f38b2ff1014d971a45dfd1ddf2d))
* fixed loop when invoking non-orchestrator agent using --user_input ([61cd427](https://gitlab.com/codematos/pluscoder/commit/61cd4274cde9d17b2147482d59110cf0fe7c1876))
* fixed messages with dict and str content items when merged when using multimodal inputs ([1acce49](https://gitlab.com/codematos/pluscoder/commit/1acce49521e8b43f4a50dff9e1449d7ad5bcfacd))
* improve streaming block parsing with 1 more usecase ([7ae9096](https://gitlab.com/codematos/pluscoder/commit/7ae9096ae2d15c773279d736c56dae60cf21adbf))
* initialization process now works seamlessly when running pluscoder by the first time ([be0270f](https://gitlab.com/codematos/pluscoder/commit/be0270f5db6832d5050ee8385ccfd56920ec9aa0))
* initialization target agents now points all to standard developer ([25b21b8](https://gitlab.com/codematos/pluscoder/commit/25b21b86ee58256a780ad6869e5bd633e81f2bbd))
* now cli extra args are being properly ignored ([d791932](https://gitlab.com/codematos/pluscoder/commit/d791932f34461c7480405d5a322b4c1a7b529a2e))
* fixed messages with dict and str content items when merged when using multimodal inputs ([1acce49](https://gitlab.com/codematos/pluscoder/commit/1acce49521e8b43f4a50dff9e1449d7ad5bcfacd))
* now openAI endpoints stream token usage ([6db44df](https://gitlab.com/codematos/pluscoder/commit/6db44df2d53bc5367a222f15898ce2ddfe46ce7a))
* required PROJECT_OVERVIEW.md and CODING_GUIDELINES.md can now be created using --auto_confirm flag ([5b96a71](https://gitlab.com/codematos/pluscoder/commit/5b96a714e3a03c4deab6e6bd46235eb39a07a083))
* run event emitter on current running loop if exists ([84e0100](https://gitlab.com/codematos/pluscoder/commit/84e01008152166c84bba3a571bad0ff982e8c9b9))


### Features

* add system reminders for agent to improve its output consistency ([9952347](https://gitlab.com/codematos/pluscoder/commit/995234784e7260b9db6cd5e59e12593131c1e84e))
* added /agent_create to create a persistent specialized agent and start a chat with it ([1ccad26](https://gitlab.com/codematos/pluscoder/commit/1ccad2616863e75a00627a75a12f78754c11e128))
* added exponential backoff on errors related to llm endpoint ([299e861](https://gitlab.com/codematos/pluscoder/commit/299e861b1ba9c73299812f16ee6311e5fd6a0145))
* added vertex ai support through gcloud cli ([cb94f0d](https://gitlab.com/codematos/pluscoder/commit/cb94f0df5fd9947dbe8638b593a4075001d9cf64))
* auto-commits now commits only updated files ([f914dc3](https://gitlab.com/codematos/pluscoder/commit/f914dc3e0a76a1d72ac6c64e6a136b7ba25cecd0))
* default models ([5eb9adc](https://gitlab.com/codematos/pluscoder/commit/5eb9adcea08383bf29a26962a6414b5769507457))
* new --debug flag to display some relevant debug information ([d757a80](https://gitlab.com/codematos/pluscoder/commit/d757a80ba630dbb92efa0b902703d2f3e37647a1))
* new --default_agent allow selection of a default agent to chat with ([883af57](https://gitlab.com/codematos/pluscoder/commit/883af576c468666921fe258a0c6d9cdc03298b8a))
* new --repository and --source_branch configs to clone a repo before running pluscoder, --repository also accepts a git path ([80c5202](https://gitlab.com/codematos/pluscoder/commit/80c5202a0f41aa6476173fe3b9f9054d97430307))
* new global configuration yaml for reusable configs cross project. Check --show_config to see where its located ([7b1447a](https://gitlab.com/codematos/pluscoder/commit/7b1447a45f4440b9ab4d9938c4c390cc02c750b6))
* added /agent_create to create a persistent specialized agent and start a chat with it ([1ccad26](https://gitlab.com/codematos/pluscoder/commit/1ccad2616863e75a00627a75a12f78754c11e128))
* default models ([5eb9adc](https://gitlab.com/codematos/pluscoder/commit/5eb9adcea08383bf29a26962a6414b5769507457))
* new --debug flag to display some relevant debug information ([d757a80](https://gitlab.com/codematos/pluscoder/commit/d757a80ba630dbb92efa0b902703d2f3e37647a1))

# [2.2.0](https://gitlab.com/codematos/pluscoder/compare/v2.1.0...v2.2.0) (2024-10-18)


### Bug Fixes

* error handling when starting in a non-git folder ([418235c](https://gitlab.com/codematos/pluscoder/commit/418235c3b8436f38b2ff1014d971a45dfd1ddf2d))
* fixed loop when invoking non-orchestrator agent using --user_input ([61cd427](https://gitlab.com/codematos/pluscoder/commit/61cd4274cde9d17b2147482d59110cf0fe7c1876))
* improve streaming block parsing with 1 more usecase ([7ae9096](https://gitlab.com/codematos/pluscoder/commit/7ae9096ae2d15c773279d736c56dae60cf21adbf))
* initialization process now works seamlessly when running pluscoder by the first time ([be0270f](https://gitlab.com/codematos/pluscoder/commit/be0270f5db6832d5050ee8385ccfd56920ec9aa0))
* initialization target agents now points all to standard developer ([25b21b8](https://gitlab.com/codematos/pluscoder/commit/25b21b86ee58256a780ad6869e5bd633e81f2bbd))


### Features

* add system reminders for agent to improve its output consistency ([9952347](https://gitlab.com/codematos/pluscoder/commit/995234784e7260b9db6cd5e59e12593131c1e84e))
* auto-commits now commits only updated files ([f914dc3](https://gitlab.com/codematos/pluscoder/commit/f914dc3e0a76a1d72ac6c64e6a136b7ba25cecd0))
* new --default_agent allow selection of a default agent to chat with ([883af57](https://gitlab.com/codematos/pluscoder/commit/883af576c468666921fe258a0c6d9cdc03298b8a))
* now agents can read files directly from public repositories without requiring raw file urls. Available for Gitlab & Github only ([9149d47](https://gitlab.com/codematos/pluscoder/commit/9149d47671a4b3e216a9d153a2a2de9bbc036e01))
* orchestrator now operates in read only mode to focus on task design ([3de34f8](https://gitlab.com/codematos/pluscoder/commit/3de34f8bbacda871c2ff99dccaf4fb81b4e01fe3))

# [2.1.0](https://gitlab.com/codematos/pluscoder/compare/v2.0.0...v2.1.0) (2024-10-11)


### Bug Fixes

* chunk streaming parsing blocks ([2b465e1](https://gitlab.com/codematos/pluscoder/commit/2b465e15e0bba7602af5e74ac188a8e848d98097))
* config template now works without a template file in repo ([896b27c](https://gitlab.com/codematos/pluscoder/commit/896b27c2861d4b2fdd0708b39f160832a5656aef))
* git validation order ([dbb9a51](https://gitlab.com/codematos/pluscoder/commit/dbb9a51256a05438c343a36cefc9804ac49ad620))
* setup entrypoint ([79524a9](https://gitlab.com/codematos/pluscoder/commit/79524a9e5ab0f922946108ef64cff22c6e60200c))
* streaming block parsing ([fb812b6](https://gitlab.com/codematos/pluscoder/commit/fb812b6f4acac7b6b5ebeb742527b8e9b52cfc31))


### Features

* new --show_token_usage flag to display llm cost of the session. Default to true ([da0f442](https://gitlab.com/codematos/pluscoder/commit/da0f442ae9db870803238cf3e12efd0c609f7d44))
* new custom_agents config at .pluscoder-config.yml to define agents with customized instructions ([f893f9f](https://gitlab.com/codematos/pluscoder/commit/f893f9f1c16fa81cc10b4ad497f758d8c4fa32b6))

# [2.0.0](https://gitlab.com/codematos/pluscoder/compare/v1.13.0...v2.0.0) (2024-10-08)


### Bug Fixes

* /config command fixed after refactor to pydantic settings ([2eab6d3](https://gitlab.com/codematos/pluscoder/commit/2eab6d33dfa12457be4643aa15edaae377952430))
* config singleton references and inferred model display message ([fb269db](https://gitlab.com/codematos/pluscoder/commit/fb269dbab9012315736442dc66a6a6218337ae24))
* exception when passing empty promopt command to /custom ([ace6310](https://gitlab.com/codematos/pluscoder/commit/ace631007de4e5cdecfcf69344fba18345387fcb))


### Features

* add --read_only config to disable file editions keepping assistance ([0116412](https://gitlab.com/codematos/pluscoder/commit/0116412b755292a493463192766d51927d63387a))
* added documentation link at startup ([0cb6618](https://gitlab.com/codematos/pluscoder/commit/0cb6618a86fee83e203f84b10b4f30b76e61d33f))
* added new --orchestrator-model and --weak-model model and provider configs ([39b849d](https://gitlab.com/codematos/pluscoder/commit/39b849d1241a3ebb548d0501dfe6d45fbebe3f01))
* added new .pluscoder-config.yml settings file to work along cmd args and env vars ([b67a583](https://gitlab.com/codematos/pluscoder/commit/b67a583772af76efb0a8fbdb988f84bc9e8edd65))
* added new custom prompt command (/custom) to pre-define custom repetitive instructions to pass to agents ([b1b60bb](https://gitlab.com/codematos/pluscoder/commit/b1b60bbe4fea6af16a2219509ddfaf1a45892271))
* added system reminder after each user message to improve llm output consistency ([2551455](https://gitlab.com/codematos/pluscoder/commit/2551455e41029fd7b1192e1ac51ac6cb8b71fe8a))
* agents can now download files and add context use entire context. Recommended for .md and raw text files only ([3e8282e](https://gitlab.com/codematos/pluscoder/commit/3e8282e6c1116868494733284a7f2e1a17f134d4))
* display code blocks as unified diffs, updated prompts for output consistency ([d222d7e](https://gitlab.com/codematos/pluscoder/commit/d222d7e34d5dc266309ed752d514e7ef4d67e896))
* enable block detection and config to hide each block in the output ([a54d62b](https://gitlab.com/codematos/pluscoder/commit/a54d62bcc367d97b9b376ff62c8d06e818dc2f97))
* new --hide-thinking-blocks, --hide-output-blocks and --hide-source-blocks to hide llm output ([1698c78](https://gitlab.com/codematos/pluscoder/commit/1698c781306dc9a926d6ce9174f087c292d4b5dc))
* new configuration setup when running Pluscoder by the first time to customize behaviour ([8302e18](https://gitlab.com/codematos/pluscoder/commit/8302e1827146197448e2ef28f64492599f819233))
* new warning message at start up when test/lint is configured but failing to pass to warn about potential errors on file editions ([8bdec88](https://gitlab.com/codematos/pluscoder/commit/8bdec8876c1ae744b2fe0c98f0389ce9b878bf85))
* now orchestrator can delegate multi-modal inputs and resources using paths and links references ([c90699f](https://gitlab.com/codematos/pluscoder/commit/c90699fd367999fa36e5cd434372b250dac44072))

# [1.12.0](https://gitlab.com/codematos/pluscoder/compare/v1.11.0...v1.12.0) (2024-10-01)


### Features

* allow user to paste images to the console input passing them as part of the prompt to multi-modal llms ([cc8c441](https://gitlab.com/codematos/pluscoder/commit/cc8c4411501d089b8ee32888d65bfc1c86d811b0))
* input now accept img::<url_or_path> url images to send them to multi-modal llms when chatting with agents ([2714070](https://gitlab.com/codematos/pluscoder/commit/2714070b8419c9e2a015cdb453b878da979f599b))
* start up message to display current number of tracked and ignored git files ([c094e07](https://gitlab.com/codematos/pluscoder/commit/c094e074a00af85cd1705feb4fbc990171d769a4))

# [1.11.0](https://gitlab.com/codematos/pluscoder/compare/v1.10.0...v1.11.0) (2024-09-28)


### Bug Fixes

* add missing max tokens config to open ai provider, default to 4096 ([0da3393](https://gitlab.com/codematos/pluscoder/commit/0da3393322ec58d9a44c7fb137081059fb8522dd))


### Features

* new move files tool to allow agents move files throught the repository ([2e4c2ca](https://gitlab.com/codematos/pluscoder/commit/2e4c2ca0973676c5c9e2b17bf198cd3fe1e168ee))
* new show repo, repomap and config commands and command line arguments to display relevant pluscoder info that is being used by the agents ([bd10176](https://gitlab.com/codematos/pluscoder/commit/bd10176ae2357e1ded257d573b7b0827eaec2df6))

# [1.10.0](https://gitlab.com/codematos/pluscoder/compare/v1.9.1...v1.10.0) (2024-09-18)


### Features

* new REPO_EXCLUDE_FILES config to exclude files from repo thats passed to agents prompts ([362ce7b](https://gitlab.com/codematos/pluscoder/commit/362ce7b6ecace449007e0408baf669676935f098))

## [1.9.1](https://gitlab.com/codematos/pluscoder/compare/v1.9.0...v1.9.1) (2024-09-12)


### Bug Fixes

* add missing init command to commands autocompletion and fixed circular import ([41c8f5d](https://gitlab.com/codematos/pluscoder/commit/41c8f5dbecceee7fa772e566b6a5d32534dca1df))
* initialization now do not performs auto commits ([c24a170](https://gitlab.com/codematos/pluscoder/commit/c24a1706fbc791c657fa65013e96aa7dc2866333))

# [1.9.0](https://gitlab.com/codematos/pluscoder/compare/v1.8.0...v1.9.0) (2024-09-12)


### Bug Fixes

* delegating task crash fix when using multiple agents, improved context for delegated tasks ([249a109](https://gitlab.com/codematos/pluscoder/commit/249a10981f491a4a83ef3e3a902c9e2cfeee3b77))
* orchestration workflow is not counting tokens twice in some use cases ([33b1178](https://gitlab.com/codematos/pluscoder/commit/33b1178a11f2859010375406db0c0ffe9a2e6d27))
* parse block now do better parse when files have backticks ([345bd3c](https://gitlab.com/codematos/pluscoder/commit/345bd3c046963c3375822f49532ad007009a9f0f))
* read files tool restores its original behaviour to load the entire file body ([e45ea6e](https://gitlab.com/codematos/pluscoder/commit/e45ea6e1dbd7f689f58ac3e0bb0179c943a8c1a7))
* updated default color for brighter agent putputs ([94e7da1](https://gitlab.com/codematos/pluscoder/commit/94e7da1b8b9986536f1d2b9b26eca89d877b6d35))
* updated edit file block format improving performance when generating code markdown ([bd73bf8](https://gitlab.com/codematos/pluscoder/commit/bd73bf8322dd591525c2ac8381b459c34e223be7))


### Features

* add setup task list to automatically generate PROJECT_OVERVIEW.md and CODING_GUIDELINES.md files. Now workflow can run once with pre-defined task list ([9977dff](https://gitlab.com/codematos/pluscoder/commit/9977dff83e74d3ef863e60cfbf064ce59f39c62a))
* added auto_confirm for automatic approvals on the workflow ([e1bf8fe](https://gitlab.com/codematos/pluscoder/commit/e1bf8fe5c1d861707abfce510d62851cdc07121a))
* added thinking process to agents prompt ([c739003](https://gitlab.com/codematos/pluscoder/commit/c73900323385bf1d34c25f4601fbf7a2515cfc9b))
* added user_input config to automate the user input via cmd or env var. Added restrictions and outcome to task items ([0498a0b](https://gitlab.com/codematos/pluscoder/commit/0498a0b97d7112ffc357935fbaa44543bc1b628b))
* error message is displayed when provider is forced and credentials are not defined ([b76d968](https://gitlab.com/codematos/pluscoder/commit/b76d968f072dcf43cdf90d8a1d030a0616ac516a))

# [1.8.0](https://gitlab.com/codematos/pluscoder/compare/v1.7.0...v1.8.0) (2024-09-08)


### Bug Fixes

* block regex for file edition fixed for some use cases ([0f27874](https://gitlab.com/codematos/pluscoder/commit/0f27874d8fd30c3da83199e15d2337dfaebd83fb))


### Features

* added repomap tree tp agent prompts and related config variables ([9d0709c](https://gitlab.com/codematos/pluscoder/commit/9d0709c539c07c1a43e4f2a77b8c0fbc91e4b90b))
* debug to file feature added to io utils ([5026482](https://gitlab.com/codematos/pluscoder/commit/502648218f9a923ec350587e4f64675bde551625))
* repomap feature is built for python, js and jsx, and passed to the prompt of all agents. Added related config parameters ([3947213](https://gitlab.com/codematos/pluscoder/commit/3947213efffbd5b76a695b0115eaacff9e2c4b25))

# [1.7.0](https://gitlab.com/codematos/pluscoder/compare/v1.6.3...v1.7.0) (2024-08-29)


### Features

* input history support to auto-complete input with history on pressing up key ([445e24d](https://gitlab.com/codematos/pluscoder/commit/445e24d39ada3e837d4a00c5e2309d719eb92068))

## [1.6.3](https://gitlab.com/codematos/pluscoder/compare/v1.6.2...v1.6.3) (2024-08-29)


### Bug Fixes

* context files are now excluded from non-loaded files prompt, max deflections now executes the correct amount of retries ([f7c0c14](https://gitlab.com/codematos/pluscoder/commit/f7c0c148d64199dbd0fd97befca63b7a750458b7))
* file management now load entire files body just one time and replaces its every time is loaded, reducing tokens and code duplication in prompt ([9ce5d90](https://gitlab.com/codematos/pluscoder/commit/9ce5d9036374bfb6787df778e5a31b6761602127))

## [1.6.2](https://gitlab.com/codematos/pluscoder/compare/v1.6.1...v1.6.2) (2024-08-28)


### Bug Fixes

* now user empty messages doesnt break the console interaction ([4ed3436](https://gitlab.com/codematos/pluscoder/commit/4ed34366e11906e1d22eaa16ded1f7bc3c27c9c8))

## [1.6.1](https://gitlab.com/codematos/pluscoder/compare/v1.6.0...v1.6.1) (2024-08-21)


### Bug Fixes

* stream chunks properly displayed when progress is shown ([b7409e9](https://gitlab.com/codematos/pluscoder/commit/b7409e9b842c5887c0c5d81d2a739dc5c0de3a6a))

# [1.6.0](https://gitlab.com/codematos/pluscoder/compare/v1.5.0...v1.6.0) (2024-08-21)


### Bug Fixes

* test to match agent instructions ([fd93070](https://gitlab.com/codematos/pluscoder/commit/fd9307050b7b189756a40e438ab29d86e0780ac2))


### Features

* agents now have full context of task list to solve the current task ([8e97751](https://gitlab.com/codematos/pluscoder/commit/8e977513a8169cc9178f267394917f37b9808384))

# [1.5.0](https://gitlab.com/codematos/pluscoder/compare/v1.4.2...v1.5.0) (2024-08-20)


### Features

* auto lint fix & lint command configs ([5e42a83](https://gitlab.com/codematos/pluscoder/commit/5e42a83e27901b28dbd605c5c8fb9d78e4bb47f6))
* lint & test support ([afbd184](https://gitlab.com/codematos/pluscoder/commit/afbd184b8459819b887dedf6e2beca57dea8c0a7))

## [1.4.2](https://gitlab.com/codematos/pluscoder/compare/v1.4.1...v1.4.2) (2024-08-19)


### Bug Fixes

* removed unused/debug prints ([c7dc0c6](https://gitlab.com/codematos/pluscoder/commit/c7dc0c61d917d63ae1f37bf24f3d89deaea8a680))

## [1.4.1](https://gitlab.com/codematos/pluscoder/compare/v1.4.0...v1.4.1) (2024-08-19)


### Bug Fixes

* agent deflections now finishes when max reached. Tests added ([23692b8](https://gitlab.com/codematos/pluscoder/commit/23692b87ff497252960b47e7113cb7a4c331fe38))

# [1.4.0](https://gitlab.com/codematos/pluscoder/compare/v1.3.0...v1.4.0) (2024-08-13)


### Features

* anthropic support ([3b14155](https://gitlab.com/codematos/pluscoder/commit/3b14155d73b7405f3d6e14877d5af232d84ffc24))

# [1.3.0](https://gitlab.com/codematos/pluscoder/compare/v1.2.0...v1.3.0) (2024-08-13)


### Features

* now untracked files in repo are included in chat/prompts ([00e871d](https://gitlab.com/codematos/pluscoder/commit/00e871ddfcb225b566cf0b4c05b794bf8cc9886d))

# [1.2.0](https://gitlab.com/codematos/pluscoder/compare/v1.1.0...v1.2.0) (2024-08-12)


### Features

* new run command to execute bash command in chat ([d0e1ba7](https://gitlab.com/codematos/pluscoder/commit/d0e1ba736dfbec454846ad592141948878ba01e4))

# [1.1.0](https://gitlab.com/codematos/pluscoder/compare/v1.0.0...v1.1.0) (2024-08-12)


### Features

* added provider config & updated overview with new features ([e49df23](https://gitlab.com/codematos/pluscoder/commit/e49df23e2807829151d173eea7bcce4959355154))

# 1.0.0 (2024-08-12)


### Bug Fixes

* pluscoder referente for testing ([3490daf](https://gitlab.com/codematos/pluscoder/commit/3490daf639e4ab807809a3dc7f115b7b94ae8737))


### Features

* add token llm token tracking ([390cded](https://gitlab.com/codematos/pluscoder/commit/390cded6b0d05286d5cdcff06ccff5b4068a15b6))
* new setup for start up validation, cost tracking for any model ([a86daa2](https://gitlab.com/codematos/pluscoder/commit/a86daa2f10b579d18b976a1a0d54840c49a2383a))
* restores cicd test ([6deac7b](https://gitlab.com/codematos/pluscoder/commit/6deac7b637bff8275abffa078575077337a63a32))

## [1.3.1](https://gitlab.com/codematos/plus-coder/compare/v1.3.0...v1.3.1) (2024-08-11)


### Bug Fixes

* now feedback for are block errors are given in reflections ([eab90b5](https://gitlab.com/codematos/plus-coder/commit/eab90b5ad3e679ef74eb868080100402534a58c3))

# [1.3.0](https://gitlab.com/codematos/plus-coder/compare/v1.2.1...v1.3.0) (2024-08-11)


### Bug Fixes

* pytest argsv and main test emit event  patch ([d27e99c](https://gitlab.com/codematos/plus-coder/commit/d27e99c46c1085c252a52c369519d7597691cdc8))


### Features

* base commands, improved orch prompt, max agent deflections and manual user task validation ([b8708e3](https://gitlab.com/codematos/plus-coder/commit/b8708e3c3f5e017038041dda6e7708847d320b48))
* command input autocompleter ([13aa429](https://gitlab.com/codematos/plus-coder/commit/13aa429fdcfb23a647ba90dab9d6ee7292c5d7c5))
* commit and undo only plus coder commits ([ef21739](https://gitlab.com/codematos/plus-coder/commit/ef21739619dbb57d9a980f80e5a23232228e0afe))
* new commands, clear chat, config update, undo commit/message, change agent & help command ([cd1eebe](https://gitlab.com/codematos/plus-coder/commit/cd1eebe356080c6ea1a44b9b4d077d9d40f447c0))

## [1.2.1](https://gitlab.com/codematos/plus-coder/compare/v1.2.0...v1.2.1) (2024-08-10)


### Bug Fixes

* llm out chunks now are displayed properly on progress ([cce5974](https://gitlab.com/codematos/plus-coder/commit/cce5974882c8318c90789c826440811e0b726345))
* loadenv path for module use ([b4055b2](https://gitlab.com/codematos/plus-coder/commit/b4055b2bac6500617527f02311dd10832df96444))

# [1.2.0](https://gitlab.com/codematos/plus-coder/compare/v1.1.0...v1.2.0) (2024-08-09)


### Features

* auto-commits config ([ea84528](https://gitlab.com/codematos/plus-coder/commit/ea845285fba435e6b5fb027a17df85a885625374))
* commit, undo and diff git logic and event handler ([99f5079](https://gitlab.com/codematos/plus-coder/commit/99f50792585da87c9407b18da2ff4f5d01a8046f))

# [1.1.0](https://gitlab.com/codematos/plus-coder/compare/v1.0.1...v1.1.0) (2024-08-08)


### Bug Fixes

* apply_block_update on empty FIND blocks ([0659043](https://gitlab.com/codematos/plus-coder/commit/06590438c5c3c31b0818e8c1fdeb798d77300128))
* restore dotenv logic ([13e6cf7](https://gitlab.com/codematos/plus-coder/commit/13e6cf7de2635311a6ca45b7eb34fda75552032b))


### Features

* non-streamed llm responses & fix missing block parse use case ([c05981b](https://gitlab.com/codematos/plus-coder/commit/c05981b66f55363c2f27851b2e48dbb84eb71060))
* pluscoder command line & env vars config ([688497e](https://gitlab.com/codematos/plus-coder/commit/688497e31a3135601a092b48d2d2726c0137c8dd))

## [1.0.1](https://gitlab.com/codematos/plus-coder/compare/v1.0.0...v1.0.1) (2024-08-07)


### Bug Fixes

* pip setup ([b21ee0d](https://gitlab.com/codematos/plus-coder/commit/b21ee0dcfc629109e4458849dc50a96aa658901a))

# 1.0.0 (2024-08-06)


### Bug Fixes

* deflection + update prompts ([e77d9f1](https://gitlab.com/codematos/plus-coder/commit/e77d9f14a4542031627f67994c12162a5753f9c2))
* init file ([451e7f9](https://gitlab.com/codematos/plus-coder/commit/451e7f9edfba7b6a23821785f632580aefebc4ef))
* model call ([40d83ac](https://gitlab.com/codematos/plus-coder/commit/40d83ac5ac1546890ae02ca4d2dec58a175682c4))
* orchestrator ([f6f26d1](https://gitlab.com/codematos/plus-coder/commit/f6f26d15429110716deb0490849643e1b872446d))
* parse mentioned files ([62f40bc](https://gitlab.com/codematos/plus-coder/commit/62f40bc25d56ecfa7f9c6ca9a296bf3b4269482c))
* requirements ([501b706](https://gitlab.com/codematos/plus-coder/commit/501b706a455a715f1ef0ee32b03944c76647bb86))
* test references to pluscoder ([57eee8b](https://gitlab.com/codematos/plus-coder/commit/57eee8b91c4d0bc77887212d64e16963ce11c98f))


### Features

* add semantic release cicd & changelog ([818e6eb](https://gitlab.com/codematos/plus-coder/commit/818e6eb518157764c06bb28cb5ab8ebdd41a4cd5))
* semantic release for develop ([8438fbd](https://gitlab.com/codematos/plus-coder/commit/8438fbdd36d365d5803d9f316df50d8df537a2e0))

# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2023-05-14

### Added
- Initial project structure and core functionality
- Implemented base Agent class and specific agent types:
  - Domain Stakeholder Agent
  - Domain Expert Agent
  - Planning Agent
  - Developer Agent
  - Orchestrator Agent
- Basic workflow engine using LangGraph
- User interaction flow with agent selection and task approval
- File auto-completion in input using prompt_toolkit
- Event system for agent progress tracking
- Command-line interface using rich library for enhanced console output
- Integration with AWS Bedrock using Claude 3 Sonnet model
- File system operations and utility functions
- Asynchronous operations throughout the system
- Basic testing setup with pytest
- CI/CD configuration with GitLab

### Changed
- N/A (First release)

### Deprecated
- N/A (First release)

### Removed
- N/A (First release)

### Fixed
- N/A (First release)

### Security
- N/A (First release)
