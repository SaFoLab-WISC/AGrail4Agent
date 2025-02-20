cd ..
python AGrail4Agent/DAS/exp_OS.py --dataset benign --memory memory_os_benign_claude.json --agent_model gpt-4o --guardrail_model gpt-4o --use_guardrail
python AGrail4Agent/DAS/exp_OS.py --dataset system_sabotage --memory memory_os_benign_claude.json --agent_model gpt-4o --guardrail_model gpt-4o --use_guardrail
python AGrail4Agent/DAS/exp_OS.py --dataset prompt_injection --memory memory_os_benign_claude.json --agent_model gpt-4o --guardrail_model gpt-4o --use_guardrail
python AGrail4Agent/DAS/exp_OS.py --dataset environment --memory memory_os_benign_claude.json --agent_model gpt-4o --guardrail_model gpt-4o --use_guardrail