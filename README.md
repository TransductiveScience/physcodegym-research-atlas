# PhysCodeGym Research Atlas | Transductive Science

Published public research: https://physics.transductive.science/

An evidence-forward, machine-indexed inquiry into the observed numerical defects of AI-generated Blender simulations, plus a full catalogue of the 156 source tasks and 43 counterfactual rubrics in the 2026 PhysCodeGym benchmark.

## What is and is not claimed

The PhysCodeGym numerical witnesses measure defects in coding-agent reconstructions. They are not laboratory evidence for violations of physical law. The site distinguishes authors' claims, case metadata, independent inferences and unexecuted experimental proposals.

* Authors' work: https://arxiv.org/abs/2610.17288
* Source benchmark: https://github.com/ShaoShuai0605/PhysCodeGym
* TransductiveScience fork: https://github.com/TransductiveScience/PhysCodeGym
* Research conversation: https://chatgpt.com/c/6af0b330-ad88-83eb-ab31-3501375a3db5
* Static public content: root of this repository
* Case source lock: `data/source-lock.json`, based on revision `de1c8b75cddff0054f77b6322a979759e7a01f81`

## Publishing

The site is served through a separate Caddy origin and named Cloudflare tunnel; this repository is a versioned public backup, not the server's operational secret/configuration store. No Cloudflare credentials or server-private deployment files are included.

The public status endpoint `/health.json` is generated on the hosting machine every fifteen minutes and is intentionally excluded from version control.
