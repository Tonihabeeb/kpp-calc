I need you to help me enhance the quality and reliability of my Python backend codebase. You will act as my expert pair programmer to implement and utilize a two-layered code analysis and debugging strategy.
This strategy involves integrating two specific tools:
1.	DeepSource: For proactive, automated static code analysis.
2.	Workik: For context-aware, interactive debugging of complex errors.
Please follow these steps methodically:
Phase 1: Initial Setup and Static Analysis with DeepSource
1.	Repository Analysis: First, get acquainted with my project structure. Identify the main application logic, dependencies (requirements.txt or pyproject.toml), and any existing test files. My backend is built using [Specify your framework here, e.g.,dash Flask, FastAPI].
2.	Integrate DeepSource:
o	Create a .deepsource.toml configuration file in the root directory of the project.
o	In this file, enable the python analyzer.
o	Configure the analyzer to recognize my framework and key libraries.
o	Set up exclude_patterns to ignore directories like venv, migrations, and other non-essential folders.
o	Enable the test-coverage analyzer if you find test files.
3.	Run Analysis and Apply Autofixes:
o	Trigger a DeepSource analysis across the entire codebase.
o	Review the issues reported. For all issues that DeepSource can autofix (like code formatting, style guide violations), apply the fixes after you check it .
4.	Prioritize and Report Critical Issues:
o	From the remaining issues, identify the top 5-10 most critical problems related to 'bug-risks', 'anti-patterns', and 'performance'.
o	For each critical issue, please provide a comment in the relevant file right above the problematic code, explaining:
	What the issue is (e.g., "DeepSource Warning: Unhandled exception could lead to a crash.").
	Why it's a problem.
	The recommended approach to fix it.
Phase 2: Interactive Debugging and Logical Error Fixing with Workik
Now, we will address the logical and functional errors that static analysis might not catch.
1.	Set up Workik Context:
o	Assume we are setting up a debugging session in Workik. I need you to define the necessary context for the AI. List out the key components of this context, such as:
	Frameworks & Libraries: [List the frameworks and key libraries you identified earlier].
	Database Schema: [If I provide the schema, note how it would be used].
	API Endpoints: Identify the main API routes/endpoints in the application.
2.	Simulated Debugging Workflow:
o	I want you to target a specific complex function that you think is a candidate for logical errors (e.g., a function with complex business logic, multiple conditional branches, or complex data manipulation). [You can optionally point to a specific file or function here, e.g., src/processing/main.py].
o	Walk me through how you would use a tool like Workik to debug it. Your explanation should be a step-by-step process:
	"First, I would set a breakpoint at the beginning of the function function_name."
	"Next, I would step through the code line-by-line to observe the state of variables like variable1 and variable2."
	"Based on the logic, I predict that if input_data is X, the code might fail. Let's analyze that path."
	"Workik's AI would likely suggest a refactoring here to handle edge cases like Y or to simplify the conditional logic for better readability and correctness."
3.	Refactor the Code:
o	Based on your simulated debugging session, refactor the selected piece of code.
o	Apply the fix, ensuring it resolves the potential logical flaw, improves readability, and adds comments where the logic is complex.
Final Output:
Your final output should be the modified codebase with:
1.	The .deepsource.toml file.
2.	All autofixes from DeepSource applied.
3.	Code comments marking the critical issues found by DeepSource that require manual review.
4.	The refactored code for the function you analyzed, demonstrating a fix for a potential logical error.


