apiVersion: v1
kind: Secret
metadata:
  name: secrets
  namespace: {{cookiecutter.project_slug}}-__ENVIRONMENT__
type: Opaque
stringData:
  BASIC_AUTH_PASSWORD: __PASSWORD__
  BASIC_AUTH_USER: {{cookiecutter.project_slug}}
  DJANGO_ADMINS: 20tab,errors@20tab.com;admin,errors@{{cookiecutter.domain_url}}
  DJANGO_ALLOWED_HOSTS: 127.0.0.1,localhost,__SUBDOMAIN__.{{cookiecutter.domain_url}}
  DJANGO_CONFIGURATION: __CONFIGURATION__
  DJANGO_DEBUG: "__DEBUG__"
  DJANGO_DEFAULT_FROM_EMAIL: info@{{cookiecutter.domain_url}}
  DJANGO_SECRET_KEY: __SECRETKEY__
  DJANGO_SERVER_EMAIL: server@{{cookiecutter.domain_url}}
  EMAIL_URL: console:///
  NODE_ENV: production
  POSTGRES_DB: {{cookiecutter.project_slug}}
  POSTGRES_PASSWORD: postgres
  POSTGRES_USER: postgres
  S3_ACCESS_KEY_ID: __ S3_ACCESS_KEY_ID__
  S3_ACCESS_KEY_SECRET: __S3_ACCESS_KEY_SECRET__
  S3_BUCKET_NAME: {{cookiecutter.project_slug}}
  S3_DEFAULT_ACL: public-read
  S3_HOST: __REGION__.digitaloceanspaces.com
  SENTRY_DSN: __SENTRY_DSN__
