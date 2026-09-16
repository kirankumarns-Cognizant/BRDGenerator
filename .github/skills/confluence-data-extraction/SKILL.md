# Confluence Data Extraction Skill

## Skill Definition
**Name**: Confluence Data Extraction  
**Type**: Data Extraction  
**Language**: Python  

## Description
Extracts documentation, requirements, and specifications from Confluence spaces.

## Prerequisites
- Confluence API access token
- Confluence space key
- Network access to Confluence instance

## Configuration
Add to `.env`:
```
CONFLUENCE_TOKEN=your_token_here
```

Add to `config.yaml`:
```yaml
resources:
  confluence:
    base_url: "https://yourcompany.atlassian.net"
    space_key: "YOUR_SPACE"
    token_env: CONFLUENCE_TOKEN
    enabled: true
```

## Invocation
```python
from tools.adapters.unstructured_adapter import UnstructuredAdapter

adapter = UnstructuredAdapter(config)
docs = adapter.load_confluence_space(space_key="YOUR_SPACE")
```

## Outputs
- Extracted markdown documents
- Page hierarchy
- Attachments
- Links and references

## Integration
Used by Agent 1 for artifact discovery when Confluence is enabled.
