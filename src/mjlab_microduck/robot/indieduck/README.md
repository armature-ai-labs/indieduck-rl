# Canonical IndieDuck R20 model

Generated from the complete published R20 CAD assembly. Contract v2, 15 physical joints, 14 policy actions and a separate direct-drive mouth. SI body-local visual meshes, estimated aggregate bounding-box inertias, conservative ground/prop collision proxies, explicit source identities and revision hashes. CAD self-clearance must be checked separately; collision proxies intentionally do not certify self-collision freedom.

`contract.json` and `part-bodies.json` define joint and component ownership. `poses.json` holds illustrative configurations; only current reports under repository `validation/r20-*` describe this revision. R07 reports are historical. `tools/` regenerates browser/runtime assets from this directory. See root third-party notices for the mixed-source mesh terms.
