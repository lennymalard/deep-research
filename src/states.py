from typing import TypedDict, List, Annotated, NotRequired, Optional, Tuple, Any
from pydantic import BaseModel, Field
import operator

class SystemState(TypedDict):
    user_query: str
    search_queries: List[dict[str, str]]
    search_results : Annotated[List[dict[str, str]], operator.add]
    summaries : Annotated[List[dict[str, str]], operator.add]
    review: dict[str, str]
    reports: Annotated[List[dict[str, Any]], operator.add]
    final_report: str
    search_iteration: int

class QueryGeneratorState(TypedDict):
    user_query : str
    search_iteration: int

class ResearcherState(TypedDict):
    user_query: str
    search_query: str
    search_results: Annotated[List[dict[str, str]], operator.add]

class ReviewerState(TypedDict):
    summaries: List[dict[str, str]]
    user_query: str
    search_iteration: int

class WriterState(TypedDict):
    summaries : List[dict[str, str]]
    user_query: str

class EvaluatorState(TypedDict):
    reports: List[dict[str, Any]]
    summaries: List[dict[str, str]]
    user_query: str

class QueryItem(BaseModel):
    query: str = Field(description="The keyword-optimized search string.")
    reason: str = Field(description="Justification for why this query was chosen.")

class GenerateQueries(BaseModel):
    search_queries: List[QueryItem] = Field(
        description="A list of 3 to 5 distinct search queries with justifications."
    )

class Summarize(BaseModel):
    summary: str = Field(
        description="A concise extraction of facts, dates, and numbers from the text that directly answer the user query. If the text contains NO relevant information, this must be an empty string."
    )

class Review(BaseModel):
    is_search_complete: bool = Field(
        description="True ONLY if the gathered information allows for a comprehensive, detailed answer to the user query. False if any specific detail is missing."
    )
    justification: str = Field(
        description="If False, specify exactly what information is missing to guide the next search. If True, briefly summarize why the data is sufficient."
    )

class Write(BaseModel):
    report: str = Field(
        description="A professional, structured report in Markdown format. It must answer the user query in depth using ONLY the provided page summaries, including inline citations [Source: URL] for every fact."
    )
    confidence: int = Field(
        ge=1, le=10,
        description="A 1-10 score of your fidelity to the sources. 10 = you successfully transcribed explicit facts with zero interpretation; 1 = the sources were messy or incomplete, forcing you to interpret, infer, or bridge gaps to make the report coherent."
    )

class EvaluationItem(BaseModel):
    report_index: int = Field(
        description="The index number of the report being evaluated (e.g., 0, 1, 2, 3, 4)."
    )
    faithfulness: int = Field(
        ge=1, le=10,
        description="1-10 scale of factual grounding. 10 = all claims are explicitly backed by the provided sources with no hallucinations. 1 = the report fabricates information or directly contradicts the source material."
    )
    answer_relevance: int = Field(
        ge=1, le=10,
        description="1-10 scale of intent matching. 10 = directly, concisely, and completely answers the user's specific prompt without tangential fluff. 1 = completely misses the point of the user's query."
    )
    context_completeness: int = Field(
        ge=1, le=10,
        description="1-10 scale of source utilization. 10 = successfully extracts and includes all critical information and caveats from the provided sources. 1 = poorly cherry-picks data, leaving out major context or counter-arguments."
    )
    formatting_quality: int = Field(
        ge=1, le=10,
        description="1-10 scale of structure and readability. 10 = professional, clean Markdown with logical headers, bullet points, and high readability. 1 = a broken, disorganized wall of text."
    )
    synthesis_quality: int = Field(
        ge=1, le=10,
        description="1-10 scale of narrative cohesion. 10 = seamlessly weaves multiple sources together into a logical, flowing narrative. 1 = reads like a disjointed, copy-pasted list of separate summaries."
    )

class Evaluate(BaseModel):
    marks: List[EvaluationItem] = Field(
        description="A list containing the detailed scoring for each candidate report."
    )
