#!/usr/bin/env python3
"""Test multi-provider LLM system."""

from kb_gen.utils.multi_provider_llm import get_multi_provider_llm, get_active_provider

print('\n' + '='*70)
print('🔍 Multi-Provider LLM System Test')
print('='*70 + '\n')

try:
    llm = get_multi_provider_llm()
    print('✅ Multi-provider LLM system initialized\n')
    
    print(f'🚀 Active Provider: {get_active_provider()}\n')
    
    print('📊 Available Providers:')
    print('-' * 70)
    providers = llm.list_available_providers()
    
    for provider, info in providers.items():
        status = '✅' if info.get('available') else '⚪'
        mode = info.get('mode', 'unknown')
        requires_key = '(requires API key)' if info.get('requires_key') else '(no API key needed)'
        print(f'{status} {info["name"]:40} [{mode}] {requires_key}')
    
    print('\n' + '='*70)
    print('✅ System Ready!')
    print('='*70 + '\n')
    
    # Show how to set providers
    print('📝 Setup Instructions:')
    print('-' * 70)
    print('For Claude API:       export ANTHROPIC_API_KEY="your-key"')
    print('For OpenAI:           export OPENAI_API_KEY="your-key"')
    print('For Google Gemini:    export GOOGLE_API_KEY="your-key"')
    print('For GitHub Copilot:   gh auth login')
    print('For Claude Code:      Install "anthropic.claude-code" in VS Code')
    print('\n' + '='*70 + '\n')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
