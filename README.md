# Docker Builder Helper

Docker Builder Helper is a Python script that makes it faster and easier for you to build Docker images
with different environments. You can specify the docker image file, the compose file, the .env file, and more.

Typical examples include:
- Building your production docker image with a development env file for final testing
- Building your development docker image with a development env file and development compose file for development
- Building your production docker image with a production env file and production compose file for production
or for a local copy of your production environment with access to those production secrets

## Usage
### Configuration
The configuration is done in the `dockerbuilder.yml` file. The configuration file uses sections for each environment,
and each section can have the following:
- `name` (required): The name of the environment
- `tag` (required): The tag to use for the image, this must match the tag in the docker-compose file and is used to
  identify the container for later docker commands, such as `docker exec -ti <container> bash`
- `dockerfile` (optional): The path to the Dockerfile to build. If not specified, the default is `Dockerfile`
- `composefile` (optional): The path to the docker-compose file to use. If not specified, the default is `docker-compose.yml`
- `envfile` (optional): The path to the .env file to use. If not specified, the default is `.env`
- `buildargs` (optional): A dictionary of build arguments to pass to the docker build command.
- `composeargs` (optional): A dictionary of arguments to pass to the docker-compose command.
- `arch` (optional): A dictionary of arguments to pass to the docker-compose command.
- `push` (optional): Whether to push the image to the registry. Defaults to `false`.
- `registry` (optional): The registry to push the image to.
- `buildonly` (optional): Whether to only build the image and not run the compose file. Defaults to `false`.
- `interactive` (optional): Whether to run `docker exec -ti <container> bash` after running the compose file. Defaults to `true`.

Here is an example configuration file:
```yaml
environments:
  production:
    name: production
    tag: production
    dockerfile: Dockerfile
    composefile: docker-compose.yml
    envfile: .env
    buildargs:
      - BUILD_ENV=production
      - --no-cache
    arch:
      - amd64
      - arm64
    push: true
    registry: myregistry.com
    buildonly: false
    interactive: true
  development:
    name: development
    tag: development-123
    dockerfile: Dockerfile
    composefile: docker-compose.dev.yml
    envfile: .env.dev
    buildargs:
      - BUILD_ENV=development
    arch: amd64
    push: false
    registry: myregistry.com
    buildonly: false
    interactive: true

### Running
To run the script, simply run `python dockerbuilder.py <environment>`. For example, to build the production environment, run `python dockerbuilder.py production`.

### Flags
You can run the script with additional flags:
- `list` or `ls`: List all the environments in the configuration file
- `remove <environment>` or `rm <environment>`: Remove an environment from the configuration file
- `remove-cache <environment>`: Remove the cache for an environment
- `no-cache`: Build the image with the `--no-cache` flag regardless of the configuration
- `push`: Push the image to the registry regardless of the configuration (requires the `registry` field to be set in the configuration)
- `arch <architecture>`: Specify the architecture to build the image for, regardless of the configuration
- `buildonly`: Only build the image and do not run the compose file, regardless of the configuration
- `verbose`: Enable verbose output for Docker and Docker Compose commands
- `clean`: Clean up dangling images and containers

### Interactive Mode
You can run the script interactively by running `python dockerbuilder.py`. By default, the script will prompt you to select an environment.
From there you can choose to build it, edit the configuration, or do a one-off build with custom options that include:
- `no-cache`: Build the image with the `--no-cache` flag
- `push`: Push the image to the registry
- `arch`: Specify the architecture to build the image for
- `verbose`: Enable verbose output for Docker and Docker Compose commands

### Health Checks
Before building and running Docker images, the script performs the following health checks:
- Ensures Docker is installed and running
- Ensures Docker Compose is installed

These checks help ensure that the environment is properly set up before attempting to build and run Docker images.
