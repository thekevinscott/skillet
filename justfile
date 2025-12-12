# Default recipe - show available commands
default:
    @just --list

# Run the CLI
run *args:
    uv run skillet {{args}}

# Clean build artifacts
clean:
    rm -rf build/ dist/ *.egg-info

# Build package
build: clean
    uv build
