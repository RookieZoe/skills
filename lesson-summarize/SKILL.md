---
name: lesson-summarize
description: Summarize a lesson from courseware (PDF/MD), ASR transcripts, and/or QA notes into a structured study note.
---

# Lesson Summarize Skill

Process lesson materials (Courseware, Transcripts, QA Notes) to generate a high-quality, structured study note.

## Usage
Run this skill when you have a lesson directory containing course materials.

## Procedure

1.  **Analyze Input Directory**
    *   Scan the current or specified directory for available materials.
        *   **Courseware**: `*.pdf`, `*.pptx`, `*.docx` (Original Courseware) or `*.md` (OCR result). Note: Original courseware and OCR-recognized files are equally important.
        *   **Transcript**: `*-文字稿.txt` or `*-transcription.txt`.
        *   **QA Notes**: `*-课堂笔记.txt` or `*-note.txt` or `*-qa.txt` (Teacher's QA/Notes).

2.  **Content Extraction Strategy**
    *   **Source Roles**:
        *   **Courseware (PDF/PPTX/DOCX/MD)**: The **Skeleton**. Defines the logical flow and key concepts. Original courseware and OCR Markdown provide the core structural outline with equal importance.
        *   **Transcript**: The **Flesh**. Provides detailed explanations, examples, and nuance.
        *   **QA Notes**: The **Appendix/Supplement**. Contains specific answers to student questions, often supplementary to the main lecture.

    *   **Scenario Handling**:

        *   **Scenario A: Full Suite (Courseware + Transcript + QA)**
            *   **Structure**: Follows the Courseware's flow.
            *   **Content**: Synthesize Courseware and Transcript for the main body.
            *   **QA Handling**: Add a distinct "Teacher Q&A" section at the end (or relevant location) for these specific questions. *Do not mix them into the main concept flow unless critical.*

        *   **Scenario B: Courseware + Transcript (Standard)**
            *   **Structure**: Follows the Courseware's flow.
            *   **Content**: Use Transcript to explain the concepts in the Courseware.
            *   *Goal*: Combine the visual structure of slides with the verbal detail of the lecture.

        *   **Scenario C: Only Courseware**
            *   **Structure**: Follows the Courseware's flow.
            *   **Content**: Summarize visual text and bullet points. Infer context where possible.

        *   **Scenario D: Only Transcript**
            *   **Structure**: Infer logical breaks (Topic 1, Topic 2) from speech transitions.
            *   **Content**: Summary of the spoken content.

3.  **Drafting the Note (Structured Textbook Style)**
    *   **Tone**: Objective, educational, professional (Textbook style).
    *   **Structure**:
        *   **Title**: Lesson Name + "Study Note".
        *   **Core Summary**: 1-2 paragraphs summarizing the lesson's main thesis.
        *   **Key Concepts**: Break down into clear sections (I, III, III...).
            *   Use **Textbook Definitions** + **Lecturer's Examples**.
            *   Use **Comparison Tables** for contrasting concepts.
            *   Highlight **"Why it matters"** (Significance).
        *   **Supplementary Q&A** (If QA notes present): Short section for "Common Questions" at the end.
    *   **Formatting**: Use Markdown (Bold, Lists, Tables).

4.  **Verification & Output**
    *   Review the note for clarity and completeness.
    *   Save the result to `Summaries/{LessonName}-学习笔记.md`.
    *   If `Summaries/` does not exist, create it.
