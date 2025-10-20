#!/bin/bash
# demo_neura_complete.sh

echo "🧠 NEURA OS - Complete System Demonstration"
echo "==========================================="
echo ""

# 1. CORTEX - Thinking
echo "1️⃣ CORTEX (Thinking) - LLM Local"
echo "Question: 'What is Neura?'"
curl -s -X POST http://localhost:8000/api/cortex/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Neura in one sentence?", "stream": false}' \
  | jq -r '.text' | head -n 2
echo ""

# 2. MEMORY - Remembering
echo "2️⃣ MEMORY (Remembering) - Semantic Search"
echo "Storing: 'Motor + Policy completed on Oct 18'"
curl -s -X POST http://localhost:8000/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"content": "Motor and Policy modules completed on October 18, 2025. Full automation + governance working.", "metadata": {"type": "milestone"}}' \
  | jq -c '{id, timestamp}'

echo ""
echo "Recalling: 'automation'"
curl -s -X POST http://localhost:8000/api/memory/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "automation governance", "k": 1}' \
  | jq -c '.[0] | {content: .entry.content[:50], score}'
echo ""

# 3. POLICY - Judging
echo "3️⃣ POLICY (Judging) - Ethical Validation"
echo "✅ Safe action:"
curl -s -X POST http://localhost:8000/api/policy/validate \
  -H "Content-Type: application/json" \
  -d '{"app": "Notes", "action": "type_text", "text": "Hello", "os": "mac"}' \
  | jq -c '{allowed, reason}'

echo ""
echo "❌ Dangerous action:"
curl -s -X POST http://localhost:8000/api/policy/validate \
  -H "Content-Type: application/json" \
  -d '{"app": "BadApp", "action": "open_app", "os": "mac"}' \
  | jq -c '{allowed, reason, violations}'
echo ""

# 4. MOTOR - Acting
echo "4️⃣ MOTOR (Acting) - Safe Automation"
echo "Executing: Type text in Notes"
curl -s -X POST http://localhost:8000/api/motor/execute \
  -H "Content-Type: application/json" \
  -d '{"app": "Notes", "action": "type_text", "text": "Neura demo completed!", "os": "mac"}' \
  | jq -c '{status, reason, duration_ms, trace_id}'
echo ""

# 5. SYSTEM HEALTH
echo "5️⃣ SYSTEM HEALTH - All Modules"
curl -s http://localhost:8000/health \
  | jq '{status, version, modules}'
echo ""

echo "✅ Demonstration Complete!"
echo ""
echo "📊 Neura Capabilities:"
echo "  🧠 Thinks  (Cortex)"
echo "  🧬 Remembers  (Memory)"
echo "  🧮 Judges  (Policy)"
echo "  ⚙️ Acts  (Motor)"
echo "  📝 Explains  (WHY Journal)"
