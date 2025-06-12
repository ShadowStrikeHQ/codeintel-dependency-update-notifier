# codeintel-Dependency-Update-Notifier
Scans project dependencies and notifies the user if there are newer versions available, potentially including security updates. Uses `pip` and `packaging`. - Focused on Tools for static code analysis, vulnerability scanning, and code quality assurance

## Install
`git clone https://github.com/ShadowStrikeHQ/codeintel-dependency-update-notifier`

## Usage
`./codeintel-dependency-update-notifier [params]`

## Parameters
- `-h`: Show help message and exit
- `-r`: Path to the requirements.txt file.
- `-p`: Path to the project directory. Defaults to current directory.
- `-v`: Enable verbose logging.
- `--check-security`: Check for known security vulnerabilities using safety.

## License
Copyright (c) ShadowStrikeHQ
