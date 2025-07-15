#!/bin/bash
# 🏛️ CAVA Test Runner
# Runs all CAVA tests in sequence

echo "🏛️ CAVA Test Runner"
echo "=================="
echo ""

# Set dry-run mode for safety
export CAVA_DRY_RUN_MODE=true

# Phase 1: Test connections
echo "📊 Phase 1: Testing Database Connections..."
python3 implementation/cava/database_connections.py
echo ""

# Phase 2: Test LLM Query Generator
echo "🧠 Phase 2: Testing LLM Query Generator..."
python3 implementation/cava/llm_query_generator.py
echo ""

# Phase 3: Test Universal Engine
echo "🔄 Phase 3: Testing Universal Conversation Engine..."
python3 implementation/cava/universal_conversation_engine.py
echo ""

# Phase 4: Run Complete Test Suite
echo "🧪 Phase 4: Running Complete Test Suite..."
python3 tests/test_cava_complete_system.py
echo ""

echo "✅ All CAVA tests completed!"
echo ""
echo "To start CAVA API server:"
echo "python3 implementation/cava/cava_api.py"