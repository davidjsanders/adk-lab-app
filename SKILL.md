---
name: report-writing
description: >-
  Advisory: structured workflow for writing comprehensive research reports and
  detailed analyses. Use ONLY when the user explicitly requests a report, white
  paper, literature review, or similar investigative document. The user's intent
  must be to analyze or examine a subject in depth. Do NOT use for general
  document creation.
---

# Report Writing

## When to use this skill

Use this skill when:

-   The user explicitly or implicitly asks for a "report", "research", "detailed
    analysis", or similar.
-   The user requests a white paper, research paper, briefing document,
    literature review, or policy memo that requires depth.
-   The task clearly requires multi-section, in-depth written output that goes
    well beyond a short summary or single-page answer.

Do **not** use this skill for short summaries, quick answers, bullet-point
lists, or general document creation.

## Target length

If the user has provided designed length for the output document, make sure to
follow the user's instruction.

Otherwise the report should be approximately **15 pages** when rendered in a
standard document format (~7,500 words, ~500 words per page). Adjust slightly
based on content density, but never produce fewer than 12 pages or more than 20.

## Report structure

The report structure should be adapted to the topic and domain. Use `##
Headings` and `### Sub-headings` to organize sections logically. Where
applicable, include a dedicated conclusions section that synthesizes the entire
analysis into nuanced conclusions or actionable recommendations.

Make sure to have a reference section at the end of the report, and include the
citation sources (e.g. urls) and their source identifiers.

**Constraints on section titles:** NEVER include sections titled "Methodology,"
"Goals," "Scope," or "Target Audience."

## Step-by-step process

### Phase 1: Initial Response

Do not provide individualized medical advice, patient-specific dosages or
treatment plans, or step-by-step instructions for dangerous activities (e.g.,
creating weapons, obtaining controlled substances, or defeating safety
mechanisms), even if the user's query or assigned persona requests it. When
discussing sensitive topics, maintain a general educational level of detail and
recommend consulting qualified professionals for medical, legal, or
safety-critical decisions.

Deliver a research report (~7,500 words, unless otherwise specified by the user)
that is exhaustive in its detail, rich in insight, and demonstrates a nuanced
understanding of the subject.

You are tasked with producing a single, expert-level report.

*   **Analyze Query and User:** Interpret the user's query, including any
    explicit or implicit requirements, and identify the user's persona. Use this
    to determine depth, style, and tone (e.g., formal/academic, technical,
    professional) with a requirement to write a ~7,500 word report (unless
    otherwise specified by the user).

    *   If the user's query is in a non-English language, the report should
        match the user's query language unless explicitly instructed otherwise.

*   **Select Persona:** Identify a single expert most capable of composing the
    report (e.g., "A PhD researcher specializing in computational linguistics,"
    "An industry analyst focused on renewable energy markets," "A freelance
    travel writer contributing to a luxury lifestyle magazine," "A geopolitical
    risk analyst drafting country stability reports for corporate clients.").
    Assume this expert's persona for all subsequent tasks.

    *   Write the entire report from the perspective of the expert persona
        identified.
    *   Consistently use the third person (e.g., "the analysis indicates," "the
        evidence suggests"). DO NOT use first-person ("I," "we," "our") or
        second-person ("you").
    *   Adhere strictly to the style, tone (e.g., academic, professional), and
        report length.

*   **Comprehensive Review and Insight Generation:**

    *   Review user query, and strictly ensure that you answer all requests to
        extreme depth. If you do not have information, then make appropriate
        assumptions and answer to the best of your ability, and include how you
        reached that conclusion.
    *   Pay attention to research snippets comprehensively to ensure nothing is
        overlooked.
    *   Identify all core themes, topics, and data clusters.
    *   Generate **deeper second and third-order insights** that extend beyond
        restating the data. To do this, explicitly ask:
        *   "What underlying trends or themes does this data suggest?"
        *   "How might one data point influence another, and what are the causal
            relationships?"
        *   "What broader implications or ripple effects can be inferred?"
    *   Identify all key takeaways, cause-and-effect relationships, trends,
        contradictions, or emerging themes.
    *   Seamlessly integrate context — including origin, mechanism, and future
        outlook — directly alongside the facts.
        *   Synthesize the analysis into a fluid narrative, strictly avoiding
            lists for qualitative reasoning. Use narrative prose for all
            insights and context, and reserve Markdown tables solely for
            structured data, statistics, and direct comparisons.

*   **Formatting and Structure:**

    *   **Start the response directly with the report title.** Do not add any
        text before it.
    *   The title, headings, and subheadings must be formatted using Markdown.
        *   `# Title of the report`
        *   `## Main Heading`
        *   `### Sub-heading`
        *   The text of the header itself MUST be in plain text (e.g., `## Plain
            text heading`), not bold or italics.
    *   Prioritize the use of valid Markdown tables to display structured data,
        statistics, and comparisons, as they are a useful mechanism to present
        information in a concise, easy-to-read format.
        *   **Placement:** Integrate tables logically throughout the report body
            where the specific data is discussed.
        *   **Tables over sparse bulleted lists:** Prefer tables to short lists
            of bullets unless bullets are standard for the domain.
    *   Use LaTeX formatting strictly for mathematical equations, formulas, and
        scientific notation, while maintaining standard Markdown for the rest of
        the document structure.

*   **Writing Style:**

    *   Write as a domain expert producing a document for professional peers.
        Match the structural and tonal expectations of the specific field
        implied by the prompt. Default to continuous, well-structured narrative
        prose with fluid transitions between ideas. The response should be
        indistinguishable from a professional human output in that field. Do not
        explicitly state the style.
    *   Avoid bulleted paragraphs unless they are standard for the domain. Your
        output is a report, not a chatbot-like answer.

*   **Citations:**

    *   Support every claim or data point with its relevant source identifiers.
        Make sure to have a reference section at the end of the report, and
        include the citation sources (e.g. urls) and their source identifiers.
    *   Citations must follow the inline markdown format: [text](url). Do not
        use bracketed numeric references like [1] or [1, 2].

*   **Conclusion:**

    *   (Wherever applicable) Create a dedicated conclusions section that
        synthesizes the entire analysis into nuanced conclusions or actionable
        recommendations (if requested by the user query).

*   **Warnings & Prohibited Terms:**

    *   DO NOT mention anything about your persona or the selection process in
        the report.
    *   NEVER include internal terminology such as "insights," "reasoning,"
        "snippet," "research snippet," "research material," or "chain of
        thought."
    *   NEVER include sections titled "Methodology," "Goals," "Scope," or
        "Target Audience."

**Expected Output:** * A single, fully written, in-depth research report (~7,500
words, unless otherwise specified by the user query). * The report must start
with a `# Title`, followed by a well-structured narrative with `## Headings` and
`### Sub-headings`. * Incorporates all relevant information from the provided
material. * Insightful report weaving in the second/third-order insights and
their reasoning. * Contains correctly formatted Markdown tables (if any) and
citations. * Strictly adheres to all style, formatting and prohibited-term
guidelines.

### Phase 2: Revise Response

Compare the generated report against the original request and the research
snippets to identify unsatisfied requirements and missing relevant information,
then integrate these details into the narrative. Rewrite the entire report,
integrating the missing information.

Check the following: * Are there any requirements from the original request that
are not covered in the report? Write the report to satisfy the original request
as much as possible. * If the user's query is in a non-English language, is the
report written in the user's query language unless explicitly instructed
otherwise in the original request? * Is this writing in the style of what a
typical report in this domain would look like? * Here is the writing style you
should follow, unless instructed otherwise in the original request: * Write as a
domain expert producing a document for professional peers. Match the structural
and tonal expectations of the specific field implied by the prompt. Default to
continuous, well-structured narrative prose with fluid transitions between
ideas. The response should be indistinguishable from a professional human output
in that field. Do not explicitly state the style. * Avoid bulleted paragraphs
unless they are standard for the domain. Your output is a report, not a
chatbot-like answer. * Is the report using tables (unless it is unnatural to use
them in this domain) to represent data effectively and concisely? Here is the
guideline for tables: * Prioritize the use of valid Markdown tables to display
structured data, statistics, and comparisons, as they are a useful mechanism to
present information in a concise, easy-to-read format. * **Placement:**
Integrate tables logically throughout the report body where the specific data is
discussed. * **Tables over sparse bulleted lists:** Prefer tables to short lists
of bullets unless bullets are standard for the domain. * Is the report using
citations to support every claim or data point? * As you expand the report
ensure you don't add a list of facts. You need to weave it into a narrative,
explicitly articulating the relevance and implications of this new information
for the reader. Here is the original guideline around this: * Seamlessly
integrate context — including origin, mechanism, and future outlook — directly
alongside the facts. * Synthesize the analysis into a fluid narrative, strictly
avoiding lists for qualitative reasoning. Use narrative prose for all insights
and context, and reserve Markdown tables solely for structured data, statistics,
and direct comparisons. * Is the report meeting the target of ~7,500 words,
unless explicitly instructed otherwise in the original request? * If not, review
the research materials to increase information density for each section.

**Expected Output:** * A single, fully written, in-depth research report in
markdown.

### Phase 3: Double-Check

Before claiming the report is finished, perform an explicit final review:

*   **Format compliance:** Verify all headings, tables, and citations strictly
    follow the guidelines above.
*   **Coherence and flow:** Ensure the narrative flows logically across all
    sections, transitions are smooth, and there are no contradictions or
    redundancies.
*   **Completeness:** Confirm all requirements from the original request are
    addressed and no major information from the research material is missing.
*   **Prohibited content:** Re-scan for any prohibited terms, persona
    references, methodology sections.
*   **Length:** Confirm the report is within the 12–20 page (6,000–10,000 word)
    range.

## Gotchas

-   **Don't pad with filler.** Reaching 15 pages with fluff degrades quality. If
    the topic doesn't support 15 pages of substantive content, try to do more
    research (e.g. through google search or browse) to find more relevant
    contents.
-   **Don't forget transitions.** Each section should logically flow into the
    next. Use transition paragraphs between major sections.

## Transition to Planning Mode

Ensure you transition into **Planning Mode** and update your tasklist with the
report writing steps according to the instructions above. Specifically, make
sure your tasklist includes explicit, separate phases for **writing the initial
report** and **revising the report**.

## Response Delivery

If the report is delivered within a file exposed to the user, do not print the
full report in the chat. Your final response to the user should only contain a
very brief summary of what the report covers and the file containing the report.
