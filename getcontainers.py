import os
import subprocess
import json

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

class HostController:
    def __init__(self):
        self.get_envs()
        self.errors = []
        self.containers = []
        self.containers = self.get_containers_info()
        self.last_chat_id = 0
    
    def get_envs(self):
        try:
            self.hostKey = os.environ['hostKey']
            self.hostIP = os.environ['hostIP']
            self.hostUser = os.environ['hostUser']
            print("got it!")
        except:
            print("where is my keys?")
            from dotenv import load_dotenv
            load_dotenv('secrets/jnqafun.env') # .env in secrets folder
            self.hostKey = os.getenv('hostKey')
            self.hostIP = os.getenv('hostIP')
            self.hostUser = os.getenv('hostUser')

    def run_command(self, command):
        return subprocess.check_output(
            f"sshpass -p {self.hostKey} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=sshfile {self.hostUser}@{self.hostIP} {command}",
            shell=True).decode("utf-8")

    def get_containers_info(self):
        containers = []
        # try:
        if True:
            names = list(filter(None, self.run_command("docker ps --format '{{.Names}}'").split("\n")))
            images = list(filter(None, self.run_command("docker ps --format '{{.Image}}'").split("\n")))
            ids = list(filter(None, self.run_command("docker ps --format '{{.ID}}'").split("\n")))
            # Save old containers
            if self.containers:
                containers = self.containers
            # Add new containers
            for n in names:
                if not [True for elem in containers if n in elem.values()]:
                    new_image = images[names.index(n)].split(":")
                    version = new_image[1] if len(new_image) > 1 else "latest"
                    ports = self.get_ports(n)
                    containers.append({
                        'id': len(containers)+1,
                        'commands': '--restart=always',
                        'name': n,
                        'description': '',
                        'image': new_image[0],
                        'version': version,
                        'portIn': ports[0],
                        'portOut': ports[1],
                        'running': True
                    })
            # Detect not running containers
            for c in containers:
                if c['name'] not in names:
                    containers[containers.index(c)]['running'] = False
        # except Exception as error:
        #     print(f"ERROR: {error}")
        #     self.errors.append(error)
        return self.json_it(containers)

    def json_it(self, listik):
        containers = []
        for li in listik:
            containers.append(
                    {
                        'id': li["id"],
                        'commands': li["commands"],
                        'name': li["name"],
                        'description': li["description"],
                        'image': li["image"],
                        'version': li["version"],
                        'portIn': li["portIn"],
                        'portOut': li["portOut"],
                        'running': li["running"]
                    }
            )
        return containers

    def get_ports(self, containerName):
        ports = self.run_command(f"docker port {containerName}")
        portIN = ports.split("\n")[0].split("/")[0]
        if len(ports.split("\n")[0].split(":")) > 1:
            portOUT = ports.split("\n")[0].split(":")[1]
            return [portIN, portOUT]
        else:
            return [None, None]

    def get_current_version(self, containerName):
        image = list(filter(None, self.run_command(f"docker ps -f name={containerName} --format {{.Image}}").split("\n")))[0]
        if len(image.split(":")) > 1:
            return image.split(":")[0]
        else:
            return "latest"

    def upgrade_container(self, containerName, version="latest"):
        current = next(item for item in self.containers if item["name"] == containerName)
        new_image = f"{str(current['image']).split(':')[0]}:{version}"
        print(f"\x1b[1;32;40m - update {containerName} > {new_image}\x1b[0m")
        try:
            status = self.run_command(f"docker pull {new_image}")
            print(status)
        except:
            print(f"\x1b[1;31;40m - bad {new_image}\x1b[0m")
            self.containers["version"] = self.get_current_version(containerName)
            return False
        if self.get_current_version(containerName) == version and version != "latest":
            print(f"\x1b[1;33;40m - {current['version']} == {version}\x1b[0m")
            return False
        else:
            if new_image != "jnqa/docker-updater":
                print(self.run_command(f'docker stop {containerName}'))
                self.run_command(f'docker rm {containerName}')
                if "portOut" in current.keys() and current["portOut"]:
                    self.run_command(f'docker run --name={containerName} {current["commands"]} -d -p {current["portOut"]}:{current["portIn"]} {new_image}')
                    print(f'\x1b[1;32;40m - docker run --name={containerName} {current["commands"]} -d -p {current["portOut"]}:{current["portIn"]} {new_image}\x1b[0m')
                else:
                    self.run_command(f'docker run --name={containerName} {current["commands"]} -d {new_image}')
                return True
            else:
                return False


def GetContainers():
    CONTOLLER = HostController()
    return CONTOLLER.containers

if __name__ == '__main__':
    Containers = HostController()
    print(f'\x1b[1;32;40m{Containers.containers}\x1b[0m')

