#!/usr/bin/env python3
import os
import sys
import yaml
import subprocess
from pathlib import Path
import logging

# Configuration file name
CONFIG_FILE = 'dockerbuilder.yml'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to load the configuration file
def load_config():
    if not Path(CONFIG_FILE).is_file():
        logging.error(f"Configuration file {CONFIG_FILE} not found.")
        sys.exit(1)
    with open(CONFIG_FILE, 'r') as file:
        return yaml.safe_load(file)

# Function to check if Docker is installed and running
def check_docker():
    try:
        subprocess.run(['docker', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        logging.error("Docker is not installed. Please install Docker and try again.")
        sys.exit(1)
    
    try:
        subprocess.run(['docker', 'info'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        logging.error("Docker daemon is not running. Please start Docker and try again.")
        sys.exit(1)

# Function to check if Docker Compose is installed
def check_docker_compose():
    try:
        subprocess.run(['docker-compose', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        logging.error("Docker Compose is not installed. Please install Docker Compose and try again.")
        sys.exit(1)

# Function to build the Docker image
def build_image(env_config, no_cache=False, arch=None, verbose=False):
    dockerfile = env_config.get('dockerfile', 'Dockerfile')
    buildargs = env_config.get('buildargs', [])
    archs = env_config.get('arch', [])

    if arch:
        archs = [arch]

    build_command = ['docker', 'build', '-t', env_config['tag'], '-f', dockerfile]
    
    if no_cache or '--no-cache' in buildargs:
        build_command.append('--no-cache')

    for arg in buildargs:
        if arg != '--no-cache':
            build_command.extend(['--build-arg', arg])

    for arch in archs:
        build_command.extend(['--platform', f'linux/{arch}'])

    build_command.append('.')
    
    if verbose:
        logging.info(f"Running build command: {' '.join(build_command)}")
        subprocess.run(build_command)
    else:
        subprocess.run(build_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Function to run docker-compose
def run_compose(env_config, verbose=False):
    composefile = env_config.get('composefile', 'docker-compose.yml')
    envfile = env_config.get('envfile', '.env')
    composeargs = env_config.get('composeargs', {})
    
    compose_command = ['docker-compose', '-f', composefile, '--env-file', envfile, 'up', '-d']
    
    for key, value in composeargs.items():
        compose_command.extend([key, value])
    
    if verbose:
        logging.info(f"Running compose command: {' '.join(compose_command)}")
        subprocess.run(compose_command)
    else:
        subprocess.run(compose_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Function to push the Docker image to a registry
def push_image(env_config, verbose=False):
    registry = env_config.get('registry')
    if not registry:
        logging.error("Registry not specified in configuration.")
        return
    
    tag = env_config['tag']
    image_name = f"{registry}/{tag}"
    
    tag_command = ['docker', 'tag', tag, image_name]
    push_command = ['docker', 'push', image_name]

    if verbose:
        logging.info(f"Running tag command: {' '.join(tag_command)}")
        logging.info(f"Running push command: {' '.join(push_command)}")
        subprocess.run(tag_command)
        subprocess.run(push_command)
    else:
        subprocess.run(tag_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(push_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Function to list all environments in the configuration
def list_environments(config):
    logging.info("Available environments:")
    for env in config['environments']:
        logging.info(f" - {env}")

# Function to remove an environment from the configuration
def remove_environment(config, env_name):
    if env_name in config['environments']:
        del config['environments'][env_name]
        with open(CONFIG_FILE, 'w') as file:
            yaml.dump(config, file)
        logging.info(f"Environment {env_name} removed.")
    else:
        logging.error(f"Environment {env_name} not found.")

# Function to remove the Docker build cache for an environment
def remove_cache(env_name):
    subprocess.run(['docker', 'builder', 'prune', '--filter', f'label={env_name}'])

# Function to clean up dangling images and containers
def clean_up(verbose=False):
    clean_command = ['docker', 'system', 'prune', '-f']
    
    if verbose:
        logging.info(f"Running clean up command: {' '.join(clean_command)}")
        subprocess.run(clean_command)
    else:
        subprocess.run(clean_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Main function to handle command-line arguments and execute the appropriate actions
def main():
    config = load_config()
    
    if len(sys.argv) < 2:
        logging.error("Usage: python dockerbuilder.py <environment> [flags]")
        sys.exit(1)
    
    check_docker()
    check_docker_compose()
    
    command = sys.argv[1]
    
    if command in ['list', 'ls']:
        list_environments(config)
        return
    
    if command in ['remove', 'rm']:
        if len(sys.argv) < 3:
            logging.error("Usage: python dockerbuilder.py remove <environment>")
            sys.exit(1)
        remove_environment(config, sys.argv[2])
        return
    
    if command == 'remove-cache':
        if len(sys.argv) < 3:
            logging.error("Usage: python dockerbuilder.py remove-cache <environment>")
            sys.exit(1)
        remove_cache(sys.argv[2])
        return
    
    if command == 'clean':
        clean_up('--verbose' in sys.argv)
        return
    
    if command not in config['environments']:
        logging.error(f"Environment {command} not found in configuration.")
        sys.exit(1)
    
    env_config = config['environments'][command]
    no_cache = '--no-cache' in sys.argv
    push = '--push' in sys.argv
    buildonly = '--buildonly' in sys.argv
    verbose = '--verbose' in sys.argv
    arch = None
    
    if '--arch' in sys.argv:
        arch_index = sys.argv.index('--arch') + 1
        if arch_index < len(sys.argv):
            arch = sys.argv[arch_index]
    
    build_image(env_config, no_cache, arch, verbose)
    
    if push or env_config.get('push', False):
        push_image(env_config, verbose)
    
    if not buildonly and not env_config.get('buildonly', False):
        run_compose(env_config, verbose)
    
    if env_config.get('interactive', True):
        subprocess.run(['docker', 'exec', '-ti', env_config['tag'], 'bash'])

if __name__ == "__main__":
    main()
