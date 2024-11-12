#!/bin/bash

# Files to obfuscate
files=(
    "pluscoder/main.py"
    "pluscoder/workflow.py"  
    "pluscoder/setup.py"  
    "pluscoder/tools.py"  
    "pluscoder/api_integration.py"  
    "pluscoder/type.py"  
    "pluscoder/agents/base.py"
    "pluscoder/agents/core.py"
    "pluscoder/agents/orchestrator.py"
    "pluscoder/agents/prompts.py"
    "pluscoder/agents/stream_parser.py"
    "pluscoder/agents/utils.py"
)

# Remove debug code
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS requires '' after -i
    sed -i '' 's/not config.dev and //g' pluscoder/main.py
    sed -i '' '/dev: CliImplicitFlag\[bool\] = Field(False, description="Enable development mode (skips token validation)")/d' pluscoder/config/config.py
else
    # Linux version
    sed -i 's/not config.dev and //g' pluscoder/main.py
    sed -i '/dev: CliImplicitFlag\[bool\] = Field(False, description="Enable development mode (skips token validation)")/d' pluscoder/config/config.py
fi

# Create temp directory for pyarmor output
rm -rf dist/
mkdir -p dist/

# Run pyarmor on files
pyarmor g "${files[@]}"

# First move runtime to avoid import errors
rm -rf pluscoder/pyarmor_runtime_000000
mv dist/pyarmor_runtime_000000 pluscoder/

# For each file in array
for file in "${files[@]}"; do
    filename=$(basename "$file")
    
    # Backup original file
    # mv "$file" "${file}.b"
    rm "$file"
    
    # Update import path in generated file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS requires '' after -i
        sed -i '' 's/from pyarmor_runtime_000000/from pluscoder.pyarmor_runtime_000000/g' "dist/$filename"
    else
        # Linux version
        sed -i 's/from pyarmor_runtime_000000/from pluscoder.pyarmor_runtime_000000/g' "dist/$filename"
    fi
    
    # Move generated file to original location
    mv "dist/$filename" "$file"
    
    # Ensure correct permissions
    chmod 644 "$file"
done

# Cleanup
rm -rf dist/