#!/usr/bin/env

# Remove debug code
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS requires '' after -i
    # Update version first
    sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEXT_VERSION\"/g" pluscoder/__version__.py
    
    sed -i '' 's/not config.dev and //g' pluscoder/main.py
    sed -i '' '/dev: CliImplicitFlag\[bool\] = Field(False, description="Enable development mode (skips token validation)")/d' pluscoder/config/config.py
    sed -i '' '/dev: CliImplicitFlag\[bool\] = Field(False, description="Enable development mode (skips token validation)")/d' pluscoder/config/config.py
    sed -i '' 's|API_BASE_URL = "http://127.0.0.1:8000/api"|API_BASE_URL = "https://api.pluscoder.cl/api"|g' pluscoder/api_integration.py
else
    # Linux version
    # Update version first
    sed -i "s/__version__ = \".*\"/__version__ = \"$NEXT_VERSION\"/g" pluscoder/__version__.py
    
    sed -i 's/not config.dev and //g' pluscoder/main.py
    sed -i '/dev: CliImplicitFlag\[bool\] = Field(False, description="Enable development mode (skips token validation)")/d' pluscoder/config/config.py
    sed -i 's|API_BASE_URL = "http://127.0.0.1:8000/api"|API_BASE_URL = "https://api.pluscoder.cl/api"|g' pluscoder/api_integration.py
fi