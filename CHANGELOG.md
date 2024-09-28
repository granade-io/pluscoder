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
