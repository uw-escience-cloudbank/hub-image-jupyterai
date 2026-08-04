# jupyter-ai enabled test image

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/uw-escience-cloudbank/hub-image-jupyterai?devcontainer_path=.devcontainer%2Fdevcontainer.json)
[![Open in JupyterHub](https://img.shields.io/badge/launch-JupyterHub-blue?logo=jupyter)](https://uw-escience.2i2c.cloud/hub/login?next=/hub/spawn%23fancy-forms-config=%7B%22profile%22%3A%22cpu-only%22%2C%22resource_allocation%22%3A%22mem_4_gb%22%2C%22resource_allocation%3Aunlisted_choice%22%3A%22%22%2C%22image%22%3A%22unlisted_choice%22%2C%22image%3Aunlisted_choice%22%3A%22ghcr.io%2Fuw-escience-cloudbank%2Fhub-image-jupyterai%3Alatest%22%7D)

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

To have jupyter-ai automatically connect to an LLM proxy (e.g. the [LiteLLM Proxy server](https://github.com/uw-ssec/llmoxie)), set `OPENAI_API_BASE` and `OPENAI_API_KEY` in the container environment.

Create a `.env` file (not committed to git):

```
OPENAI_API_BASE=https://<your-proxy-server-url>
OPENAI_API_KEY=sk-aaaaabbbbbcccccddddd
```

Then pass it with `--env-file`:

```
docker run -it --rm -p 8888:8888 --env-file .env ghcr.io/uw-escience-cloudbank/hub-image-jupyterai:latest jupyter lab --ip 0.0.0.0
```

Or pass the variables directly with `-e`:

```
docker run -it --rm -p 8888:8888 \
  -e OPENAI_API_BASE=https://<your-proxy-server-url> \
  -e OPENAI_API_KEY=sk-aaaaabbbbbcccccddddd \
  ghcr.io/uw-escience-cloudbank/hub-image-jupyterai:latest jupyter lab --ip 0.0.0.0
```
