import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import subprocess
import yaml
import os
import sys
import logging

# Add the parent directory to the Python path so that the module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import functions from the main script
from dockerbuilderhelper import load_config, setup_logging, health_checks, build_image, run_compose, push_image, execute_commands, main

class TestDockerBuilderHelper(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='environments:\n  test:\n    name: test\n')
    def test_load_config(self, mock_file):
        """
        Test loading the configuration file.
        """
        config = load_config()
        self.assertIn('test', config['environments'])
        mock_file.assert_called_with('dockerbuilder.yml', 'r')

    @patch('logging.basicConfig')
    def test_setup_logging(self, mock_basic_config):
        """
        Test setting up logging configuration.
        """
        setup_logging('debug', 'test.log')
        mock_basic_config.assert_called_once()

    @patch('subprocess.run')
    def test_health_checks(self, mock_subprocess_run):
        """
        Test performing health checks for Docker and Docker Compose.
        """
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        compose_command = health_checks()
        mock_subprocess_run.assert_any_call(['docker', '--version'], check=True)
        self.assertIn(compose_command, [['docker-compose'], ['docker', 'compose']])

    @patch('subprocess.run')
    def test_build_image(self, mock_subprocess_run):
        """
        Test building the Docker image.
        """
        env_config = {
            'dockerfile': 'Dockerfile',
            'buildargs': ['BUILD_ENV=test'],
            'platform': ['linux/amd64'],
            'tag': 'test:latest'
        }
        build_image(env_config)
        mock_subprocess_run.assert_called_once()
        self.assertIn('docker', mock_subprocess_run.call_args[0][0])
        self.assertIn('build', mock_subprocess_run.call_args[0][0])
        self.assertIn('--build-arg', mock_subprocess_run.call_args[0][0])
        self.assertIn('--platform', mock_subprocess_run.call_args[0][0])
        self.assertIn('-t', mock_subprocess_run.call_args[0][0])

    @patch('subprocess.run')
    def test_run_compose(self, mock_subprocess_run):
        """
        Test running Docker Compose.
        """
        env_config = {
            'composefile': 'docker-compose.yml',
            'composeargs': {'-d': ''}
        }
        run_compose(env_config, ['docker-compose'])
        mock_subprocess_run.assert_called_once_with(['docker-compose', '-f', 'docker-compose.yml', '-d', '', 'up'], check=True)

    @patch('subprocess.run')
    def test_push_image(self, mock_subprocess_run):
        """
        Test pushing the Docker image to a registry.
        """
        env_config = {
            'tag': 'test:latest',
            'registry': 'myregistry.com'
        }
        push_image(env_config)
        mock_subprocess_run.assert_called_once()
        self.assertIn('docker', mock_subprocess_run.call_args[0][0])
        self.assertIn('push', mock_subprocess_run.call_args[0][0])
        self.assertIn('myregistry.com/test:latest', mock_subprocess_run.call_args[0][0])

    @patch('subprocess.run')
    def test_execute_commands(self, mock_subprocess_run):
        """
        Test executing pre-build and post-build commands.
        """
        commands = ['echo "Hello, World!"', 'ls -l']
        execute_commands(commands)
        self.assertEqual(mock_subprocess_run.call_count, 2)
        mock_subprocess_run.assert_any_call('echo "Hello, World!"', shell=True, check=True)
        mock_subprocess_run.assert_any_call('ls -l', shell=True, check=True)

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_missing_config_file(self, mock_open):
        """
        Test handling of missing configuration file.
        """
        with self.assertRaises(FileNotFoundError):
            load_config()

    @patch('builtins.open', new_callable=mock_open, read_data=': invalid_yaml')
    def test_invalid_config_file(self, mock_file):
        """
        Test handling of invalid configuration file.
        """
        with self.assertRaises(yaml.YAMLError):
            load_config()

    @patch('builtins.open', new_callable=mock_open, read_data='environments:\n  test:\n    name: test\n')
    def test_missing_environment(self, mock_file):
        """
        Test handling of missing environment in the configuration file.
        """
        with patch('sys.exit') as mock_exit:
            with patch('sys.argv', ['dockerbuilder-helper.py', 'nonexistent-environment']):
                main()
            mock_exit.assert_called_once_with(1)

    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='environments:\n  test:\n    name: test\n    buildargs: ["BUILD_ENV=test"]\n    pre_build: ["echo pre-build"]\n    post_build: ["echo post-build"]\n')
    def test_pre_post_build_commands(self, mock_file, mock_subprocess_run):
        """
        Test execution of pre-build and post-build commands.
        """
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        with patch('sys.argv', ['dockerbuilder-helper.py', 'test']):
            main()
        mock_subprocess_run.assert_any_call('echo pre-build', shell=True, check=True)
        mock_subprocess_run.assert_any_call('echo post-build', shell=True, check=True)

    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='environments:\n  test:\n    name: test\n    interactive: true\n    container: test-container\n')
    def test_interactive_mode(self, mock_file, mock_subprocess_run):
        """
        Test handling of interactive mode.
        """
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        with patch('sys.argv', ['dockerbuilder-helper.py', 'test']):
            main()
        mock_subprocess_run.assert_any_call(['docker', 'exec', '-ti', 'test-container', 'bash'], check=True)

    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='environments:\n  test:\n    name: test\n')
    def test_command_line_arguments(self, mock_file, mock_subprocess_run):
        """
        Test handling of various command-line arguments.
        """
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        with patch('sys.argv', ['dockerbuilder-helper.py', 'test', '--no-cache']):
            main()
            mock_subprocess_run.assert_called()

    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open, read_data='environments:\n  test:\n    name: test\n    tag: test:latest\n')
    def test_build_only_mode(self, mock_file, mock_subprocess_run):
        """
        Test handling of build-only mode.
        """
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        with patch('sys.argv', ['dockerbuilder-helper.py', 'test', '--buildonly']):
            main()
        # Check that subprocess.run was called for both health checks and the build command
        expected_calls = [
            call(['docker', '--version'], check=True),
            call(['docker-compose', '--version'], check=True, stdout=-1, stderr=-1),
            call(['docker', 'build', '-f', 'Dockerfile', '-t', 'test:latest', '.'], check=True)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls)

    @patch('subprocess.run')
    def test_invalid_dockerfile_path(self, mock_subprocess_run):
        """
        Test handling of invalid Dockerfile path.
        """
        env_config = {
            'dockerfile': 'invalid_path/Dockerfile',
            'buildargs': ['BUILD_ENV=test'],
            'platform': ['linux/amd64'],
            'tag': 'test:latest'
        }
        with self.assertRaises(FileNotFoundError):
            build_image(env_config)

    @patch('subprocess.run')
    def test_invalid_composefile_path(self, mock_subprocess_run):
        """
        Test handling of invalid docker-compose file path.
        """
        env_config = {
            'composefile': 'invalid_path/docker-compose.yml',
            'composeargs': {'-d': ''}
        }
        with self.assertRaises(FileNotFoundError):
            run_compose(env_config, ['docker-compose'])

    @patch('subprocess.run')
    def test_missing_environment_variables(self, mock_subprocess_run):
        """
        Test handling of missing environment variables.
        """
        env_config = {
            'dockerfile': 'Dockerfile',
            'buildargs': [],
            'platform': ['linux/amd64'],
            'tag': 'test:latest'
        }
        with self.assertRaises(KeyError):
            build_image(env_config)

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'docker push'))
    def test_push_image_failure(self, mock_subprocess_run):
        """
        Test handling of Docker image push failure.
        """
        env_config = {
            'tag': 'test:latest',
            'registry': 'myregistry.com'
        }
        with self.assertRaises(subprocess.CalledProcessError):
            push_image(env_config)

@patch('logging.FileHandler')
@patch('logging.StreamHandler')
@patch('logging.basicConfig')
def test_logging_configuration(self, mock_basic_config, mock_stream_handler, mock_file_handler):
    """
    Test setting up logging configuration.
    """
    setup_logging('debug', 'test.log')
    
    # Check that basicConfig was called with the correct level and format
    mock_basic_config.assert_called_once_with(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            mock_file_handler.return_value,
            mock_stream_handler.return_value
        ]
    )
    
    # Ensure the handlers are created with the correct parameters
    mock_file_handler.assert_called_once_with('test.log', mode='a')
    mock_stream_handler.assert_called_once()


if __name__ == '__main__':
    unittest.main()
