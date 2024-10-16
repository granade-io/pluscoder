#!/bin/bash

# This script installs PlusCoder in the local machine
# It also adds the PlusCoder configuration to the shell configuration file
# The script is intended to be run in a Unix-like system, such as Linux or MacOS

# Default PlusCoder image
PLUSCODER_IMAGE="registry.gitlab.com/codematos/pluscoder-repository:latest"
PLUSCODER_FOLDER="$HOME/.pluscoder"
PLUSCODER_ENVFILE=.pluscoder-env
OPEN_ENV_FILE=true

# Function to display usage
usage() {
    echo "Usage: install.sh [-i <image>] [-f <folder>] [-h]"
    echo "  -i <image>    Specify the image to use."
    echo "  -f <folder>   Specify the folder to use."
    echo "  -s            Skip the opening of the env file."
    echo "  -h            Display this help message."
    exit 1
}

# Parse command line options
while getopts ":i:f:sh" opt; do
    case ${opt} in
        i )
            PLUSCODER_IMAGE=$OPTARG
            ;;
        f )
            PLUSCODER_FOLDER=$OPTARG
            ;;
        s )
            OPEN_ENV_FILE=false
            ;;
        h )
            usage
            ;;
        \? )
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        : )
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done


# Print the PlusCoder logo
echo """
-------------------------------------------------------------------------------

                      @@@@@@@   @@@@@@   @@@@@@@   @@@@@@@@  @@@@@@@
                     @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@@
             @@!     !@@       @@!  @@@  @@!  @@@  @@!       @@!  @@@
             !@!     !@!       !@!  @!@  !@!  @!@  !@!       !@!  @!@
          @!@!@!@!@  !@!       @!@  !@!  @!@  !@!  @!!!:!    @!@!!@!
          !!!@!@!!!  !!!       !@!  !!!  !@!  !!!  !!!!!:    !!@!@!
             !!:     :!!       !!:  !!!  !!:  !!!  !!:       !!: :!!
             :!:     :!:       :!:  !:!  :!:  !:!  :!:       :!:  !:!
                      ::: :::  ::::: ::   :::: ::   :: ::::  ::   :::
                      :: :: :   : :  :   :: :  :   : :: ::    :   : :

-------------------------------------------------------------------------------
"""

# Terms and conditions
echo "By installing PlusCoder, you agree to the terms and conditions of the PlusCoder."
echo -n "Do you agree to the terms and conditions? (yes/no): "

read terms_conditions

if [ $terms_conditions != "yes" ]; then
    echo "You must agree to the terms and conditions to install PlusCoder."
    exit 1
fi

# Check if Docker is installed
echo ""
echo -n "Checking if Docker is installed... "
if ! [ -x "$(command -v docker)" ]; then
    echo "Docker is not installed."
    echo "Please install Docker before running this script."
    exit 1
else
    echo "Docker is installed"
fi

# Create local PlusCoder folder
echo ""
echo -n "Checking PlusCoder folder... "
if [ -d $PLUSCODER_FOLDER ]; then
    echo "folder already exists"
else
    echo "creating PlusCoder folder "
    mkdir $PLUSCODER_FOLDER
fi
echo ""
echo -n "Checking PlusCoder env file... "
if [ -f $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE ]; then
    echo "already exists"
else
    echo "creating"
    touch $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE
    echo "# ANTHROPIC_API_KEY=sk-...." >> $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE
    echo "# OPENAI_API_KEY=sk-...." >> $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE
    echo "# OPENAI_API_BASE=..." >> $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE
fi

# Pull PlusCoder image if is not locally available
echo ""
echo -n "Checking if PlusCoder image is available... "
if [ "$(docker images -q $PLUSCODER_IMAGE 2> /dev/null)" == "" ]; then
    echo "image is not available"
    echo "Pulling PlusCoder image..."
    docker pull $PLUSCODER_IMAGE
else
    echo "image is already available"
fi

# Identify the shell
shell=$(echo $SHELL | awk -F '/' '{print $3}')
if [ $shell == "zsh" ]; then
    config_file="$HOME/.zshrc"
elif [ $shell == "bash" ]; then
    config_file="$HOME/.bashrc"
else
    echo "Shell not supported"
    exit 1
fi

# Add the PlusCoder configuration to the configuration file
# First, check if the configuration is already added
if grep -q "# PlusCoder" $config_file; then
    echo "PlusCoder configuration is already added to $config_file"
    echo "PlusCoder has been successfully installed."
    echo "alias pluscoder='docker run --env-file $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE -it --rm -v   \$(pwd):/app $PLUSCODER_IMAGE'" >> $config_file
else
    # Add the PlusCoder configuration to the configuration file
    echo ""
    echo "Adding PlusCoder configuration to $config_file"
    echo "" >> $config_file
    echo "# PlusCoder" >> $config_file
    echo "function pluscoder() {" >> $config_file
    echo "  docker_image=$PLUSCODER_IMAGE" >> $config_file
    echo "  user_env=$PLUSCODER_FOLDER/$PLUSCODER_ENVFILE" >> $config_file
    echo "  workspace=\$(pwd)" >> $config_file
    echo "  workspace_env=\$(pwd)/.env" >> $config_file
    echo "  if [ -f \$workspace_env ]; then" >> $config_file
    echo "    docker run \\" >> $config_file
    echo "      --env-file <(env) --env-file \$user_env --env-file \$workspace_env \\" >> $config_file
    echo "      -v \$(pwd):/app -it --rm \$docker_image" >> $config_file
    echo "  else" >> $config_file
    echo "    docker run \\" >> $config_file
    echo "      --env-file <(env) --env-file \$user_env \\" >> $config_file
    echo "      -v \$(pwd):/app -it --rm \$docker_image" >> $config_file
    echo "  fi" >> $config_file
    echo "}" >> $config_file
    echo "" >> $config_file

    echo ""
    echo "PlusCoder has been successfully installed."

    echo ""
    echo "Please restart your shell or run 'source $config_file' to start using PlusCoder."
fi

echo "You can also add your API keys to the $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE file."

# Open the env file with the default editor, but first check code is installed
if [ $OPEN_ENV_FILE == false ]; then
    exit 0
fi

if [ -x "$(command -v code)" ]; then
    code $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE
else
    open $PLUSCODER_FOLDER/$PLUSCODER_ENVFILE
fi
