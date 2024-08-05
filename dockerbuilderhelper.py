#!/usr/bin/env python3

import argparse
import subprocess
import yaml
import os
import sys
import logging

# Function to load the configuration file
def load_config(file_path='dockerbuilder.yml'):
    """
    Load the YAML configuration file.

    :param file_path: Path to the configuration file
    :return: Parsed configuration as a dictionary
    """
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Function to set up logging
def setup_logging(level, file, verbose):
    """
    Set up logging configuration.

    :param level: Logging level (e.g., 'info', 'debug')
    :param file: File to log to
    :param verbose: Boolean indicating if verbose output is enabled
    """
    # Remove existing handlers to avoid duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()

    # Configure logging with the specified level and file
    logging.basicConfig(level=logging.DEBUG if verbose else getattr(logging, level.upper(), None),
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(file, mode='a'),
                            logging.StreamHandler()
                        ])

# Function to check for the availability of docker-compose or docker compose
def check_docker_compose():
    """
    Check if 'docker-compose' or 'docker compose' is available.

    :return: List of command parts to use for Docker Compose
    """
    try:
        # Check if 'docker-compose' is available
        subprocess.run(['docker-compose', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ['docker-compose']
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Check if 'docker compose' is available
            subprocess.run(['docker', 'compose', 'version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return ['docker', 'compose']
        except (subprocess.CalledProcessError, FileNotFoundError):
            sys.exit("Neither docker-compose nor docker compose is installed or not running.")

# Function to perform health checks
def health_checks():
    """
    Perform health checks to ensure Docker and Docker Compose are installed and running.

    :return: List of command parts to use for Docker Compose
    """
    try:
        # Check if Docker is installed and running
        subprocess.run(['docker', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        sys.exit("Docker is not installed or not running.")
    return check_docker_compose()

# Function to build the Docker image
def build_image(env_config, no_cache):
    """
    Build the Docker image based on the environment configuration.

    :param env_config: Environment configuration dictionary
    :param no_cache: Boolean indicating whether to use the --no-cache flag
    """
    dockerfile = env_config.get('dockerfile', 'Dockerfile')
    if not os.path.exists(dockerfile):
        raise FileNotFoundError(f"Dockerfile {dockerfile} not found")
    
    # Check for required environment variables
    required_env_vars = ['BUILD_ENV']
    buildargs = {arg.split('=')[0]: arg.split('=')[1] for arg in env_config.get('buildargs', [])}
    for var in required_env_vars:
        if var not in buildargs:
            raise KeyError(f"Required environment variable {var} not found in build arguments")
    
    # Construct the Docker build command
    build_command = ['docker', 'build', '-f', dockerfile]
    if no_cache:
        build_command.append('--no-cache')
    if 'buildargs' in env_config:
        for arg in env_config['buildargs']:
            build_command.extend(['--build-arg', arg])
    if 'platform' in env_config:
        build_command.extend(['--platform', ','.join(env_config['platform'])])
    if 'tag' in env_config:
        if env_config.get('push', False) and 'registry' in env_config:
            full_tag = f"{env_config['registry']}/{env_config['tag']}"
            build_command.extend(['-t', full_tag])
        else:
            build_command.extend(['-t', env_config['tag']])
    build_command.append('.')
    
    logging.debug(f"Build command: {' '.join(build_command)}")
    try:
        result = subprocess.run(build_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if result.stderr:
            logging.error(result.stderr.decode())
    except subprocess.CalledProcessError as e:
        logging.error(f"Build failed with error: {e.stderr.decode()}")
        sys.exit(1)

# Function to run Docker Compose
def run_compose(env_config, compose_command):
    """
    Run Docker Compose based on the environment configuration.

    :param env_config: Environment configuration dictionary
    :param compose_command: List of command parts to use for Docker Compose
    """
    compose_file = env_config.get('composefile', 'docker-compose.yml')
    if not os.path.exists(compose_file):
        raise FileNotFoundError(f"Compose file {compose_file} not found")
    
    # Construct the Docker Compose command
    compose_command.extend(['-f', compose_file])
    if 'composeargs' in env_config:
        for arg, value in env_config['composeargs'].items():
            compose_command.extend([arg, value])
    compose_command.extend(['up', '-d'])  # Add the '-d' flag for detached mode
    
    logging.debug(f"Compose command: {' '.join(compose_command)}")
    try:
        result = subprocess.run(compose_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if result.stderr:
            logging.error(result.stderr.decode())
    except subprocess.CalledProcessError as e:
        logging.error(f"Docker Compose failed with error: {e.stderr.decode()}")
        sys.exit(1)

# Function to push the Docker image
def push_image(env_config):
    """
    Push the Docker image to a registry.

    :param env_config: Environment configuration dictionary
    """
    if 'tag' in env_config and 'registry' in env_config:
        full_tag = f"{env_config['registry']}/{env_config['tag']}"
        push_command = ['docker', 'push', full_tag]
        logging.debug(f"Push command: {' '.join(push_command)}")
        try:
            result = subprocess.run(push_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(result.stdout.decode())
            if result.stderr:
                logging.error(result.stderr.decode())
        except subprocess.CalledProcessError as e:
            logging.error(f"Push failed with error: {e.stderr.decode()}")
            sys.exit(1)

# Function to execute pre-build and post-build commands
def execute_commands(commands):
    """
    Execute a list of shell commands.

    :param commands: List of commands to execute
    """
    for command in commands:
        logging.debug(f"Executing command: {command}")
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(result.stdout.decode())
            if result.stderr:
                logging.error(result.stderr.decode())
        except subprocess.CalledProcessError as e:
            logging.error(f"Command '{command}' failed with error: {e.stderr.decode()}")
            sys.exit(1)

# Main function to run the script
def main():
    print("Welcome to the Docker Builder Helper")
    
    parser = argparse.ArgumentParser(description="Docker Builder Helper")
    parser.add_argument('environment', nargs='?', help="The environment to build")
    parser.add_argument('--list', action='store_true', help="List all environments")
    parser.add_argument('--remove', help="Remove an environment")
    parser.add_argument('--remove-cache', help="Remove the cache for an environment")
    parser.add_argument('--no-cache', action='store_true', help="Build the image with the --no-cache flag")
    parser.add_argument('--push', action='store_true', help="Push the image to the registry")
    parser.add_argument('--platform', help="Specify the platform to build the image for")
    parser.add_argument('--buildonly', action='store_true', help="Only build the image and do not run the compose file")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output for Docker and Docker Compose commands")
    parser.add_argument('--clean', action='store_true', help="Clean up dangling images and containers")
    parser.add_argument('--hard-clean', action='store_true', help="Clean up all images, containers, networks and un-named volumes")
    
    args = parser.parse_args()
    
    config = load_config()
    
    if args.list:
        # List all environments
        print("Environments:")
        for env in config['environments']:
            print(f" - {env}")
        return
    
    if args.remove:
        # Remove the specified environment
        if args.remove in config['environments']:
            del config['environments'][args.remove]
            with open('dockerbuilder.yml', 'w') as file:
                yaml.dump(config, file)
            print(f"Environment {args.remove} removed.")
        else:
            print(f"Environment {args.remove} not found.")
        return

    # Test for non-existent environment    
    if not args.environment:
        print("No environment specified.")
        sys.exit(1)
        return

    if args.environment not in config['environments']:
        print(f"Environment {args.environment} not found.")
        sys.exit(1)
        return

    env_config = config['environments'][args.environment]

    # Set up logging
    setup_logging(env_config.get('logging', {}).get('level', 'info'),
                  env_config.get('logging', {}).get('file', 'dockerbuilder.log'),
                  args.verbose)
    
    # Perform health checks to ensure Docker and Docker Compose are installed and running
    compose_command = health_checks()
    
    # Execute pre-build commands if any
    if 'pre_build' in env_config:
        execute_commands(env_config['pre_build'])
    
    # Determine if the --no-cache flag should be used
    no_cache = args.no_cache or env_config.get('no_cache', False)
    
    # Build the Docker image
    build_image(env_config, no_cache)
    
    # Run Docker Compose if not in build-only mode
    if not args.buildonly and not env_config.get('buildonly', False):
        run_compose(env_config, compose_command)
    
    # Push the Docker image if specified
    if args.push or env_config.get('push', False):
        push_image(env_config)
    
    # Execute post-build commands if any
    if 'post_build' in env_config:
        execute_commands(env_config['post_build'])
    
    # Run an interactive shell in the container if specified
    if env_config.get('interactive', False):
        container = env_config.get('container')
        if not container:
            logging.error("Interactive mode requested, but 'container' key is missing in the configuration.")
            sys.exit(1)
        subprocess.run(['docker', 'exec', '-ti', container, 'bash'], check=True)

if __name__ == "__main__":
    main()
