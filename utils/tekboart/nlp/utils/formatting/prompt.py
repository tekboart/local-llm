# Some Guidelines by ChatGPT:
# 1. System Message (Optional): Define the role of the LLM and how it should process retrieved context.
# 2. Context-First Approach: Prioritizes retrieved data before the query.
#    * Format them clearly, separating different documents.
# 3. Explicit Query: Include the user’s question explicitly.
# 4. Explicit Instructions: Guide the model on how to use the retrieved data.
# 5. Prevents Hallucination: By instructing the model to use only the provided data.

# structure 1) written by me
structure_1 = """
Context:
\t{context}

Question:
\t{query}

Instructions:
\t\N{bullet} Please provide a detailed and accurate answer based on the context provided.
\t\N{bullet} State which information comes from the context and which does
not, in separated lines. like:
    [from context] Fact 1 and 2.
    [not from context] Fact 3 and 4.
\t\N{bullet} Give the reference of each section of the response inline and with [%d] citation style.

Answer:
\t
"""

# structure 1) By ChatGPT co-founder
structure_2 = """
**Prompt:**
\t{query} (in the context section--provided at the end)

**Return Format:**
for each sentence, return the content followed by the document name of the
source used.

**Warning:**
\t\N{bullet} Please provide a detailed and accurate answer based on the context provided.
\t\N{bullet} State which information comes from the context and which does
not, in separated lines. like:
    [from context] Fact 1 and 2.
    [not from context] Fact 3 and 4.
\t\N{bullet} Give the reference of each section of the response inline and with [%d] citation style.

**Context:**
\t{context}
"""
structure_3 = """Generate a summary of the context that answers the question.
Explain the answer in multiple steps if possible. Answer style should match the
context. Ideal Answer Length 2-3 sentences.\n\n{context}\nQuestion: {query}\nAnswer:
"""

# structure 4) written by me
structure_4 = """
Question: {query}


Format:
- Generate a summary of the context that answers the question.
- The paragraphs, in the "context" section, with lower "Dissimilarity Score" are more important in answering the "Question".
- Explain the answer in multiple steps if possible.
- Answer style should match the context.
- Ideal Answer Length 2-3 sentences.
- Use the "Source File" and "Source Page" (in the begininng of each paragraph in the "Context" section, to create a numbered list of references at the end of the "Answer" section. The structure should be like:
[1] "Source File", page: "Source Page".
[2] "Source File", page: "Source Page".


Context:
- {context}


Answer:


References:
"""

# structure 5) written by me (+ ChatGPT advice)
# Use JSON structure for the Context section
structure_5 = """
You are an AI assistant that provides accurate answers based on the retrieved documents (in "Context" section). Use the given context to answer queries concisely and avoid making up information.


Context (in {format} format):
{context}


User Query:
{query}


Instructions:
- Use only the provided context to answer.
- Generate a summary of the context that answers the question.
- Explain the answer in multiple steps if possible.
- Answer style should match the context.
- Ideal Answer Length 2-3 sentences.
- The Context items with higher "relevancy score" must be given higher weight and priority when answering the user's query.
- Use the values for "source" and "page" (in the "Context" section), to create a numbered list of references at the end of the "Answer" section. Only include the sources that you have used for answering. The structure should be like:
[1] "source", page: "page".
[2] "source", page: "page".

Answer:


References:
"""

prompt_structure = structure_5
