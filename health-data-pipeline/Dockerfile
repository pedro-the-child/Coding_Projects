FROM astrocrpublic.azurecr.io/runtime:3.2-5

# GCP ADC credentials are copied to include/gcloud/ (gitignored) on the host.
# Astro mounts include/ at /usr/local/airflow/include/ inside the container.
ENV GOOGLE_APPLICATION_CREDENTIALS=/usr/local/airflow/include/gcloud/application_default_credentials.json
