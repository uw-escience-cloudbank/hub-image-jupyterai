# jupyter-ai enabled test image

Based on template repository for creating dedicated user images for 2i2c hubs 

Trying out https://github.com/jupyterlab/jupyter-ai for scientific workshops

Goal: Wire up to UW eScience SSEC's [LiteLLM Proxy server](https://github.com/uw-ssec/llmoxie) to broker access to LLMs via AWS Bedrock running on https://www.cloudbank.org

## Usage:

- in brief: modify environment.yml, commits to main build [Docker images linked to this repository](https://github.com/uw-escience-cloudbank/hub-image-jupyterai/pkgs/container/hub-image-jupyterai) tagged with :sha and :latest
- in detail: https://docs.2i2c.org/admin/environment/hub-user-image-template-guide/ 

## Container Usage:

```
docker pull ghcr.io/uw-escience-cloudbank/hub-image-jupyterai:latest
docker run -it --rm ghcr.io/uw-escience-cloudbank/hub-image-jupyterai:latest /bin/bash
```
