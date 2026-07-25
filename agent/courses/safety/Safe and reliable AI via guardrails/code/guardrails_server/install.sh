# install deps
pip install -r requirements.txt --no-cache-dir

guardrails hub install hub://guardrails/provenance_llm --no-install-local-models;
# TODO install("hub://guardrails/provenance_nli", True)
guardrails hub install hub://guardrails/detect_pii;
guardrails hub install hub://tryolabs/restricttotopic --no-install-local-models;
guardrails hub install hub://guardrails/competitor_check --no-install-local-models;