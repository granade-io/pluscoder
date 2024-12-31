# PlusCoder CLI

PlusCoder provides an enhanced command-line interface for efficient interaction:

!!! warning 
    Some of these features are not available when running inside Docker. Like image pasting using Ctrl + V.

|               | **Action**                                      | **Description**                                                     |
|--------------------------|---------------------------------------------------|------------------------------------------------------------------|
| **Input History**         | Press the **Up Arrow**                            | Recall and reuse previous inputs.                                |
| **Multiline Input**       | Press `Ctrl + Return` or `Option + Return`                          | Create a new line for multiline commands.                        |
| **Input Clearing**        | Press `Ctrl + C`                                | Clear the current text in the input field.                       |
| **File Autocomplete**     | Start typing a filename. Use `Tab` to alternate suggestions.                                | Get suggestions and autocomplete file paths.                     |
| **Paste Support**         | Paste multiline text directly                     | Use standard paste commands in the input field.                  |
| **Quick Confirmation**    | Use `y` or `Y`                            | Quickly confirm prompts or actions.                              |
| **Image as context**       | Write `img::<url>` or `img::<local_path>`         | Pass images to agents.                                     |
| **Pasting Images**         | Press `Ctrl + V`                                | Copy images and paste it directly into the terminal to pass the to agents. |

## Next Steps

- [CLI Commands](cli-commands.md)