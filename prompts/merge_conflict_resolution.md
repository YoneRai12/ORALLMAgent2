# AI-Assisted Merge Conflict Resolution Prompt

Use the following template when invoking an LLM to help resolve git merge
conflicts. Replace the placeholders with the conflicting code blocks.

```
You are assisting with a git merge conflict. Combine the changes from both
sides, keeping all fixes and features. Explain any decisions.

<<<<<<< HEAD
{ours}
=======
{theirs}
>>>>>>> BRANCH
```

Provide the final merged code and a short explanation.
