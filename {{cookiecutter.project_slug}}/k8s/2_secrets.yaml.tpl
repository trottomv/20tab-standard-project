apiVersion: v1
kind: Secret
metadata:
  name: secrets
  namespace: {{cookiecutter.project_slug}}-__ENVIRONMENT__
type: Opaque
stringData:
  DJANGO_ADMINS: 20tab,errors@20tab.com;admin,errors@{{cookiecutter.domain_url}}
  DJANGO_ALLOWED_HOSTS: 127.0.0.1,localhost,__SUBDOMAIN__.{{cookiecutter.domain_url}}
  DJANGO_CONFIGURATION: __CONFIGURATION__
  DJANGO_DEBUG: "__DEBUG__"
  DJANGO_DEFAULT_FROM_EMAIL: info@{{cookiecutter.domain_url}}
  DJANGO_SECRET_KEY: secretkey
  DJANGO_SERVER_EMAIL: server@{{cookiecutter.domain_url}}
  EMAIL_URL: console:///
  NODE_ENV: production
  POSTGRES_DB: {{cookiecutter.project_slug}}
  POSTGRES_PASSWORD: postgres
  POSTGRES_USER: postgres
