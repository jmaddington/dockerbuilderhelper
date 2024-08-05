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
- `tag` (optional): The tag to use for the image
- `container` (optional): The name of the container that is used in the compose file. This will be required if you want to run the interactive mode.
- `dockerfile` (optional): The path to the Dockerfile to build. If not specified, the default is `Dockerfile`
- `composefile` (optional): The path to the docker-compose file to use. If not specified, the default is `docker-compose.yml`
- `envfile` (optional): The path to the .env file to use. If not specified, the default is `.env`
- `buildargs` (optional): A dictionary of build arguments to pass to the docker build command.
- `composeargs` (optional): A dictionary of arguments to pass to the docker-compose command.
- `platform` (optional): A list of platform to build for, used with buildx for multi-platform builds.
- `push` (optional): Whether to push the image to the registry. Defaults to `false`.
- `registry` (optional): The registry to push the image to.
- `buildonly` (optional): Whether to only build the image and not run the compose file. Defaults to `false`.
- `interactive` (optional): Whether to run `docker exec -ti <container> bash` after running the compose file. Defaults to `true`. Requires the `container` field to be set.
- `pre_build` (optional): A list of commands to run before building the image.
- `post_build` (optional): A list of commands to run after building the image.
- `logging` (optional): Specifies a log levels and file to log to. Defaults to `info` and `dockerbuilder.log`.


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
    platform:
      - linux/amd64
      - linux/arm64
    push: true
    registry: myregistry.com
    buildonly: false
    interactive: true
    pre_build: ./scripts/pre_build.sh
    post_build: ./scripts/post_build.sh
    logging:
      level: debug
      file: /var/log/dockerbuilderhelper.log

  development:
    name: development
    tag: development-123
    dockerfile: Dockerfile
    composefile: docker-compose.dev.yml
    envfile: .env.dev
    buildargs:
      - BUILD_ENV=development
    platform: amd64
    buildonly: false
    interactive: true
    logging:
      level: debug
      file: /var/log/dockerbuilderhelper.log
```

### Installation
The suggested installation is to either add it as a sub-module to your project or to clone it to a directory in your path.

### Running
To run the script, first ensure it is executable:

```bash
chmod +x dockerbuilder-helper/dockerbuilder.py
```

Then simply run `./dockerbuilder-helper/dockerbuilder.py <environment>`. 

For example, to build the production environment, run `./dockerbuilder-helper/dockerbuilder.py production`.

### Samples
You can find sample Dockerfiles, docker-compose files, and .env files in the project pre-configured for the environments in the configuration file.

### Flags
You can run the script with additional flags:
- `list` or `ls`: List all the environments in the configuration file
- `remove <environment>` or `rm <environment>`: Remove an environment from the configuration file
- `remove-cache <environment>`: Remove the cache for an environment
- `no-cache`: Build the image with the `--no-cache` flag regardless of the configuration
- `push`: Push the image to the registry regardless of the configuration (requires the `registry` field to be set in the configuration)
- `platform <architecture>`: Specify the platform to build the image for, regardless of the configuration
- `buildonly`: Only build the image and do not run the compose file, regardless of the configuration
- `verbose`: Enable verbose output for Docker and Docker Compose commands
- `clean`: Clean up dangling images and containers
- `hard-clean`: Clean up all images, containers, networks and un-named volumes. Use with caution. This will prompt you to confirm before proceeding.
- `help`: Display the help message

### Interactive Mode
You can run the script interactively by running `python dockerbuilder.py`. By default, the script will prompt you to select an environment.
From there you can choose to build it, edit the configuration, or do a one-off build with custom options that include:
- `no-cache`: Build the image with the `--no-cache` flag
- `push`: Push the image to the registry
- `platform`: Specify the platform to build the image for
- `verbose`: Enable verbose output for Docker and Docker Compose commands

### Health Checks
Before building and running Docker images, the script performs the following health checks:

- Ensures Docker is installed and running
- Ensures Docker Compose is installed

These checks help ensure that the environment is properly set up before attempting to build and run Docker images.


## Notes on macOS
macOS is a little more complex when using docker buildx. You need to install the `docker buildx` plugin and create a new builder with the `docker buildx create` command. You can then use the `--builder` flag to specify the builder to use. The script will automatically detect the builder and use it if it is available.

For example, dockerbuilderhelper will run a command similar to the following:
```bash
  docker buildx create --name ams86builder --use
  docker buildx inspect --bootstrap
  docker buildx build --platform linux/amd64
  --buildarg BUILD_ENV=production --no-cache
```

Where `buildarg` are the build arguments defined in the configuration file. Buildx will be called separately for each platform defined in the configuration file.

The project will check for the existence of `buildx` before running the build command. If `buildx` is not available, the script will error out.

For builds that match the local architecture or where none is defined in the configuration file, the script will use the default docker build command.

# Contributing
Contributions are welcome! Please open a pull request with your changes.

The entire code has extensive comments and docstrings to help you understand the codebase. They should all be
written at a level that a junior developer can understand. We want this project to be a learning tool for everyone.

## Testing
`dockerbuilderhelper` is tested using:

 - `pytest` for unit tests
 - `docker-py` for integration tests
 - `pytest-docker` for integration tests
 - `unittest.mock` for mocking
 - `pytest-mock` for mocking

To run tests: `python -m unittest discover -s tests -p 'test_*.py'`
