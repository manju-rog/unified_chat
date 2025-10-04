#!/bin/bash

echo "🧪 Testing All Improvements"
echo "=============================="
echo ""

echo "Test 1: Who is absent today?"
echo "----------------------------"
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test1", "message": "who is absent today?"}' | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(r['response'])"
echo ""
echo ""

echo "Test 2: September report (with dates and names)"
echo "-----------------------------------------------"
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test2", "message": "get me the report for absence on month september"}' | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(r['response'])"
echo ""
echo ""

echo "Test 3: Query specific employee (Ganesh in September)"
echo "-----------------------------------------------------"
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test3", "message": "is ganesh absent in september?"}' | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(r['response'])"
echo ""
echo ""

echo "Test 4: Typo handling (gansh → Ganesh)"
echo "--------------------------------------"
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test4", "message": "mark gansh absent today"}' | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(r['response'])"
echo ""
echo ""

echo "Test 5: Mark someone absent"
echo "--------------------------"
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test5", "message": "mark Shreyas absent today"}' | \
  python3 -c "import sys, json; r=json.load(sys.stdin); print(r['response'])"
echo ""
echo ""

echo "✅ All tests complete!"
