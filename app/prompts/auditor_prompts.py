"""
Auditor Prompts: Semantic verification and logic checking.
The Auditor compares user intent vs generated code.
"""

AUDITOR_SYSTEM_PROMPT = """You are The Auditor - a meticulous code reviewer.

Your job is to verify the generated code matches the user's request and functions correctly.

VERIFICATION CHECKLIST:
1. Feature Completeness - Does it have ALL requested features?
2. Logic Correctness - Do the JavaScript functions actually work?
3. Asset Usage - Are CDN libraries used properly (not invented)?
4. User Experience - Is it responsive and user-friendly?
5. Hallucination Check - Did the builder invent fake libraries or APIs?

COMMON ISSUES TO CATCH:
- Missing event listeners
- Broken button connections
- Fake API endpoints
- Invented library methods
- Non-functional forms
- Missing user-requested features

OUTPUT FORMAT (JSON only):
{
  "is_approved": true | false,
  "semantic_issues": [
    "User requested dark mode toggle but no such button exists",
    "Calculator division by zero not handled"
  ],
  "missing_features": ["feature 1", "feature 2"],
  "recommendations": ["Add error handling for X", "Improve Y"]
}

If is_approved = false, the code will be sent back for revision."""

FEW_SHOT_EXAMPLES = [
    {
        "user_query": "Build a todo app with add, delete, and mark complete features",
        "generated_code": """<!DOCTYPE html>
<html>
<body>
    <input id="task" type="text">
    <button onclick="addTask()">Add</button>
    <ul id="list"></ul>
    <script>
        function addTask() {
            const input = document.getElementById('task');
            const li = document.createElement('li');
            li.textContent = input.value;
            document.getElementById('list').appendChild(li);
            input.value = '';
        }
    </script>
</body>
</html>""",
        "response": {
            "is_approved": False,
            "semantic_issues": [
                "Missing delete functionality - no delete button in list items",
                "Missing mark complete feature - no way to toggle task completion",
                "No visual indication of completed tasks"
            ],
            "missing_features": ["Delete task", "Mark as complete/incomplete"],
            "recommendations": [
                "Add delete button to each <li> element",
                "Add click event to toggle 'completed' class on tasks",
                "Add CSS for strikethrough on completed tasks"
            ]
        }
    },
    {
        "user_query": "Create a calculator with basic operations",
        "generated_code": """<!DOCTYPE html>
<html>
<body>
    <div id="display">0</div>
    <button onclick="appendNum('1')">1</button>
    <button onclick="appendNum('2')">2</button>
    <button onclick="appendOp('+')">+</button>
    <button onclick="calculate()">=</button>
    <script>
        let current = '';
        function appendNum(n) { current += n; document.getElementById('display').textContent = current; }
        function appendOp(op) { current += op; }
        function calculate() {
            try {
                current = eval(current).toString();
                document.getElementById('display').textContent = current;
            } catch(e) {
                document.getElementById('display').textContent = 'Error';
            }
        }
    </script>
</body>
</html>""",
        "response": {
            "is_approved": True,
            "semantic_issues": [],
            "missing_features": [],
            "recommendations": [
                "Consider adding a clear button for better UX",
                "Add more number buttons (0, 3-9)",
                "Add more operators (-, *, /)"
            ]
        }
    }
]


def build_auditor_prompt(
    user_query: str,
    generated_code: dict,
    file_structure: list
) -> str:
    """Construct the auditor verification prompt."""
    
    examples_text = "\n\n".join([
        f"Example {i+1}:\nQuery: {ex['user_query']}\n\nGenerated Code:\n{ex['generated_code'][:500]}...\n\nAudit Result: {ex['response']}"
        for i, ex in enumerate(FEW_SHOT_EXAMPLES)
    ])
    
    code_preview = "\n\n".join([
        f"File: {filename}\n{code[:1000]}..." 
        for filename, code in list(generated_code.items())[:3]
    ])
    
    return f"""{AUDITOR_SYSTEM_PROMPT}

EXAMPLES:
{examples_text}

NOW AUDIT THIS PROJECT:

USER REQUEST: {user_query}

PLANNED ARCHITECTURE:
{file_structure}

GENERATED CODE:
{code_preview}

Audit Result (JSON only):"""