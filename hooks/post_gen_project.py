"""Define hooks to be run after project generation."""

import os
import re
import requests
import shutil
import unicodedata
import warnings

from cookiecutter.main import cookiecutter
from gitlab import Gitlab, MAINTAINER_ACCESS


class GitlabSync:
    """A GitLab interface."""

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""
        self.protocol = "https://"
        self.server_url = "gitlab.com"
        self.gl = Gitlab(
           f"{self.protocol}{self.server_url}" , private_token=os.environ["GITLAB_PRIVATE_TOKEN"]
        )
        self.gl.auth()

    def is_group_slug_available(self, group_slug):
        """Tell if group name is available."""
        resp = requests.get(f"{self.protocol}{self.server_url}")
        for p in self.gl.groups.list(search=group_slug):
            if p.path == group_slug:
                return False
        for u in self.gl.users.list(username=group_slug):
            if u.web_url.replace(f"{self.protocol}{self.server_url}/", "").casefold() == group_slug.casefold():
                return False
        return True

    def create_group(self, project_name, group_slug):
        """Create a GitLab group."""
        self.group = self.gl.groups.create({"name": project_name, "path": group_slug})
        pipeline_badge_link = "/%{project_path}/pipelines"
        pipeline_badge_image_url = "/%{project_path}/badges/%{default_branch}/pipeline.svg"
        pipeline_badge = self.group.badges.create({
            "link_url": f"{self.protocol}{self.server_url}{pipeline_badge_link}", 
            'image_url': f"{self.protocol}{self.server_url}{pipeline_badge_image_url}"
        })
        self.orchestrator = self.gl.projects.create(  # noqa
            {"name": "Orchestrator", "namespace_id": self.group.id}
        )
        self.backend = self.gl.projects.create(  # noqa
            {"name": "Backend", "namespace_id": self.group.id}
        )
        coverage_badge_image_url = "/%{project_path}/badges/%{default_branch}/coverage.svg"
        coverage_badge = self.group.badges.create({
            "link_url": f"{self.protocol}{self.group.path}.{self.server_url}/{self.backend.path}", 
            'image_url': f"{self.protocol}{self.server_url}{coverage_badge_image_url}"
        })
        self.frontend = self.gl.projects.create(  # noqa
            {"name": "Frontend", "namespace_id": self.group.id}
        )

    def set_default_branch(self):
        """Set default branch"""
        self.orchestrator.default_branch = "develop"
        self.orchestrator.save()
        self.backend.default_branch = "develop"
        self.backend.save()
        self.frontend.default_branch = "develop"
        self.frontend.save()

    def set_members(self):
        """Add given members to gitlab group"""
        list_members = []
        try:
            local_user = os.popen("git config user.email").read().strip()
            list_members.append(self.gl.users.list(search=local_user)[0].username)
        except IndexError:
            warnings.warn("git local user doesn't exists")
        members = input("Insert the usernames of all users you want to add to the group, separated by comma or empty to skip: ")
        if members:
            list_members.extend(members.split(","))
        for member in list_members:
            try:
                user = self.gl.users.list(username=member.strip())[0]
                self.group.members.create({'user_id': user.id, 'access_level': MAINTAINER_ACCESS})
                print(f"{member} added to group {self.group.name}")
            except IndexError:
                print(f"{member} doesn't exists. Please add him from gitlab.com")


class MainProcess:
    """Main process class"""

    def __init__(self, *args, **kwargs):
        """Create a main process instance with chosen parameters"""
        self.project_name = "{{ cookiecutter.project_name }}"
        self.project_slug = "{{ cookiecutter.project_slug }}"
        self.group_slug = self.project_slug
        self.use_gitlab = "{{ cookiecutter.use_gitlab }}" == "y"
        self.gitlab = None
        
    def slugify(value, allow_unicode=False):
        """
        Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
        Remove characters that aren't alphanumerics, underscores, or hyphens.
        Convert to lowercase. Also strip leading and trailing whitespace.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower()).strip()
        return re.sub(r'[-\s]+', '-', value)

    def remove(self, path):
        """Remove a file or a directory at the given path."""
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def copy_secrets(self):
        """Copy the Kubernetes secrets manifest."""
        with open("k8s/secrets.yaml.tpl", "r") as f:
            text = f.read()
            text_development = text.replace("__ENVIRONMENT__", "development")
            text_integration = text.replace("__ENVIRONMENT__", "integration")
            text_production = text.replace("__ENVIRONMENT__", "production")

            with open("k8s/development/secrets.yaml", "w+") as fd:
                fd.write(text_development)

            with open("k8s/integration/secrets.yaml", "w+") as fd:
                fd.write(text_integration)

            with open("k8s/production/secrets.yaml", "w+") as fd:
                fd.write(text_production)

    def replace_gitlab_path(self):
        """Replace __GITLAB_GROUP__ variable in README.md file"""
        text_group = ""
        with open("TEMP_README.md", "r") as f:
            text = f.read()
            text_group = text.replace("__GITLAB_GROUP__", self.group_slug)
        with open("README.md", "w+") as f:
            f.write(text_group)
        self.remove("TEMP_README.md")

    def create_subprojects(self):
        """Create the the django and react apps."""
        os.system("./scripts/init.sh")
        cookiecutter(
            "https://github.com/20tab/django-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "project_dirname": "backend",
                "gitlab_group_slug": self.group_slug,
                "static_url": "/backendstatic/",
            },
            no_input=True,
        )
        cookiecutter(
            "https://github.com/20tab/react-continuous-delivery",
            extra_context={
                "project_name": self.project_name,
                "project_slug": self.project_slug,
                "gitlab_group_slug": self.group_slug,
                "project_dirname": "frontend",
            },
            no_input=True,
        )

    def git_init(self):
        """Initialize local git repository"""
        os.system(f"./scripts/git_init.sh {self.gitlab.orchestrator.ssh_url_to_repo}")
        os.system(f"cd backend && ../scripts/git_init.sh {self.gitlab.backend.ssh_url_to_repo}")
        os.system(f"cd frontend && ../scripts/git_init.sh {self.gitlab.frontend.ssh_url_to_repo}")
    
    def run(self):
        # """Run the main process operations"""
        if self.use_gitlab:
            self.gitlab = GitlabSync()
            group_slug = input(f"Choose the gitlab group path slug [{self.group_slug}]: ") or self.group_slug
            self.group_slug = self.slugify(group_slug)
            while not self.gitlab.is_group_slug_available(self.group_slug):
                self.group_slug = input(
                    f'A Gitlab group named "{self.group_slug}" already exists. Please choose a '
                    "different name and try again: "
                )
            self.gitlab.create_group(self.project_name, self.group_slug)

        self.copy_secrets()
        self.create_subprojects()
        self.replace_gitlab_path()
        if self.gitlab:
            self.gitlab.set_members()
            self.git_init()
            self.gitlab.set_default_branch()


main_process = MainProcess()
main_process.run()