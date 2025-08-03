from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
import docker

class DockerExecOperator(BaseOperator):
    @apply_defaults
    def __init__(self, container_name, command, **kwargs):
        super().__init__(**kwargs)
        self.container_name = container_name
        self.command = command

    def execute(self, context):
        client = docker.from_env()
        container = client.containers.get(self.container_name)
        self.log.info(f"Running command in container '{self.container_name}': {self.command}")
        
        # Execute command directly in existing container
        exit_code, output = container.exec_run(self.command)

        self.log.debug(f"Raw output: {output}")
        
        if exit_code != 0:
            raise RuntimeError(f"Command failed with exit code {exit_code}: {output.decode()}")
        
        self.log.info(f"Command executed successfully: {output.decode()}")
    
        
        return output.decode()